#!/usr/bin/env python3
"""
Minimal Venmo helper for Ryan's workflow.

Currently supports:
- get transactions
- get balance
- inspect transfer-to-bank setup
- experimental transfer-to-bank execution

Auth:
  export VENMO_ACCESS_TOKEN='...'

Usage:
  ./venv/bin/python scripts/venmo_transactions.py transactions --limit 20
  ./venv/bin/python scripts/venmo_transactions.py balance
  ./venv/bin/python scripts/venmo_transactions.py transfer-setup
  ./venv/bin/python scripts/venmo_transactions.py transfer-bank --amount 25 --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from dataclasses import dataclass
from typing import Any

import aiohttp


class VenmoAuthError(Exception):
    pass


class VenmoAPIError(Exception):
    pass


@dataclass
class VenmoClient:
    access_token: str
    user_agent: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36"

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "User-Agent": self.user_agent,
        }

    async def _request(self, method: str, url: str, **kwargs: Any) -> dict[str, Any]:
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, **kwargs) as resp:
                data = await resp.json(content_type=None)
                if resp.status in (200, 201):
                    return data
                msg = data.get("error", {}).get("message", str(data)) if isinstance(data, dict) else str(data)
                if resp.status == 401:
                    raise VenmoAuthError(f"Venmo auth failed: {msg}")
                raise VenmoAPIError(f"Venmo API error {resp.status}: {msg}")

    async def get_identity(self) -> dict[str, Any]:
        return await self._request("GET", "https://api.venmo.com/v1/account", headers=self.headers)

    async def get_balance(self) -> float | None:
        identity = await self.get_identity()
        return identity.get("data", {}).get("balance")

    async def get_transactions(self) -> list[dict[str, Any]]:
        identity = await self.get_identity()
        user_id = identity.get("data", {}).get("user", {}).get("id")
        if not user_id:
            raise VenmoAPIError("Could not determine Venmo user id from /v1/account response")

        url = f"https://api.venmo.com/v1/payments"
        data = await self._request("GET", url, headers=self.headers)
        return data.get("data", [])

    async def get_payment_methods(self) -> list[dict[str, Any]]:
        data = await self._request("GET", "https://api.venmo.com/v1/payment-methods", headers=self.headers)
        return data.get("data", [])

    async def transfer_setup(self) -> dict[str, Any]:
        methods = await self.get_payment_methods()
        balance = await self.get_balance()

        venmo_balance = None
        bank_targets: list[dict[str, Any]] = []
        for m in methods:
            m_type = (m.get("type") or "").lower()
            if m_type == "balance" and venmo_balance is None:
                venmo_balance = {
                    "id": m.get("id"),
                    "name": m.get("name"),
                    "peer_payment_role": m.get("peer_payment_role"),
                }
            if m_type == "bank":
                bank_targets.append(
                    {
                        "id": m.get("id"),
                        "name": m.get("name"),
                        "last_four": m.get("last_four"),
                        "default_transfer_destination": m.get("default_transfer_destination"),
                        "is_verified": (m.get("bank_account") or {}).get("is_verified"),
                    }
                )

        default_bank = next((b for b in bank_targets if (b.get("default_transfer_destination") or "").lower() == "default"), None)

        return {
            "balance": balance,
            "venmo_balance_source": venmo_balance,
            "bank_targets": bank_targets,
            "default_bank": default_bank,
            "can_attempt_transfer": bool(venmo_balance and default_bank and balance and float(balance) > 0),
        }

    async def transfer_bank(self, amount: float, dry_run: bool = True) -> dict[str, Any]:
        setup = await self.transfer_setup()
        src = setup.get("venmo_balance_source") or {}
        dst = setup.get("default_bank") or {}
        if not src or not dst:
            raise VenmoAPIError("Transfer setup incomplete: missing Venmo balance source or default bank target")

        payload = {
            "funding_source_id": src.get("id"),
            "destination_id": dst.get("id"),
            # Venmo transfers endpoint expects cents in `amount`.
            "amount": int(round(amount * 100)),
            "transfer_type": "standard",
        }

        if dry_run:
            return {"dry_run": True, "endpoint": "https://api.venmo.com/v1/transfers", "payload": payload, "setup": setup}

        # Experimental endpoint: may change and can fail depending on account/server behavior.
        response = await self._request("POST", "https://api.venmo.com/v1/transfers", headers=self.headers, json=payload)
        return {"dry_run": False, "endpoint": "https://api.venmo.com/v1/transfers", "payload": payload, "response": response}


def _pretty_tx(tx: dict[str, Any]) -> dict[str, Any]:
    # /v1/payments uses flat structure: actor/target at top level, no "payment" wrapper
    # Story feed uses nested structure with "payment" key
    
    # Try flat /v1/payments structure first (actor/target at top level)
    actor_obj = tx.get("actor")
    target_obj = tx.get("target")
    
    # If not found at top level, try nested story feed structure
    if not actor_obj:
        payment = tx.get("payment") or {}
        actor_obj = payment.get("actor")
        target_obj = (payment.get("target") or {}).get("user")

    # Handle both formats - extract display_name or username
    if isinstance(actor_obj, dict):
        actor = actor_obj.get("display_name") or actor_obj.get("username")
    else:
        actor = str(actor_obj) if actor_obj else None
    
    if isinstance(target_obj, dict):
        target_user = target_obj.get("user") if isinstance(target_obj, dict) else target_obj
        if isinstance(target_user, dict):
            target = target_user.get("display_name") or target_user.get("username")
        else:
            target = target_obj.get("display_name") if isinstance(target_obj, dict) else str(target_obj) if target_obj else None
    else:
        target = str(target_obj) if target_obj else None

    # Get amount - try flat first, then nested
    amount = tx.get("amount")
    if amount is None:
        payment = tx.get("payment") or {}
        amount = payment.get("amount")
    
    # Get note - try flat first, then nested
    note = tx.get("note")
    if not note:
        payment = tx.get("payment") or {}
        note = payment.get("note")
    
    # Get created - try flat first, then nested
    created = tx.get("date_created")
    if not created:
        payment = tx.get("payment") or {}
        created = payment.get("date_created")
    
    status = tx.get("status") or tx.get("payment", {}).get("status")
    action = tx.get("action") or tx.get("type")

    return {
        "created_time": created,
        "amount": amount,
        "from": actor,
        "to": target,
        "action": action,
        "status": status,
        "note": note,
        "id": tx.get("id"),
    }


async def run() -> None:
    parser = argparse.ArgumentParser(description="Venmo helper")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_tx = sub.add_parser("transactions", help="List transactions")
    p_tx.add_argument("--limit", type=int, default=25)
    p_tx.add_argument("--json", action="store_true")

    p_bal = sub.add_parser("balance", help="Get Venmo balance")
    p_bal.add_argument("--json", action="store_true")

    p_setup = sub.add_parser("transfer-setup", help="Inspect transfer-to-bank setup")
    p_setup.add_argument("--json", action="store_true")

    p_xfer = sub.add_parser("transfer-bank", help="Transfer Venmo balance to linked bank (experimental)")
    p_xfer.add_argument("--amount", type=float, required=True, help="Amount in USD")
    p_xfer.add_argument("--dry-run", action="store_true", help="Show endpoint/payload only")
    p_xfer.add_argument("--json", action="store_true")

    args = parser.parse_args()

    token = (
        os.getenv("VENMO_ACCESS_TOKEN", "").strip()
        or os.getenv("VENMO_TOKEN", "").strip()
        or os.getenv("access_token", "").strip()
    )
    if not token:
        raise SystemExit("Missing VENMO_ACCESS_TOKEN (or VENMO_TOKEN/access_token) env var")

    client = VenmoClient(access_token=token)

    if args.cmd == "balance":
        balance = await client.get_balance()
        if args.json:
            print(json.dumps({"balance": balance}, indent=2))
        else:
            print(f"Venmo balance: {balance}")
        return

    if args.cmd == "transfer-setup":
        out = await client.transfer_setup()
        if args.json:
            print(json.dumps(out, indent=2))
        else:
            print(json.dumps(out, indent=2))
        return

    if args.cmd == "transfer-bank":
        out = await client.transfer_bank(amount=args.amount, dry_run=args.dry_run)
        if args.json:
            print(json.dumps(out, indent=2))
        else:
            print(json.dumps(out, indent=2))
        return

    if args.cmd == "transactions":
        txs = await client.get_transactions()
        out = [_pretty_tx(tx) for tx in txs[: args.limit]]
        if args.json:
            print(json.dumps(out, indent=2))
        else:
            for row in out:
                print(f"{row['created_time']} | {row['amount']} | {row['from']} -> {row['to']} | {row['note']}")
        return


if __name__ == "__main__":
    asyncio.run(run())
