#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import re
from datetime import datetime
from pathlib import Path

from agentmail import AgentMail
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

EXPENSE_DROPDOWN_RANGE = "📊 Summary!B27:C46"
INCOME_DROPDOWN_RANGE = "📊 Summary!G27:H33"

WORKDIR = Path('/Users/ryantaylorvegh/.openclaw/workspace')
AGENTMAIL_ENV = WORKDIR / '.secrets/agentmail.env'
GOOGLE_ENV = WORKDIR / '.secrets/google_sheets & drive.env'
STATE_PATH = WORKDIR / 'memory/receipt_email_state.json'

INBOX = 'sallysquirrel@agentmail.to'
RYAN_EMAIL = 'ryan.vegh@gmail.com'
SHEET_ID = '1Eg5hKm2xSDf6-mEYYG9pR1X7kFtiO6C5jeRO4zDzw90'
SHEET_NAME = '💰 Transactions'


def load_env(path: Path) -> dict:
    d = {}
    for raw in path.read_text().splitlines():
        s = raw.strip()
        if not s or s.startswith('#') or '=' not in s:
            continue
        k, v = s.split('=', 1)
        d[k.strip()] = v.strip().strip('"').strip("'")
    return d


def load_state() -> dict:
    if not STATE_PATH.exists():
        return {'processed': {}}
    try:
        return json.loads(STATE_PATH.read_text())
    except Exception:
        return {'processed': {}}


def save_state(state: dict):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2) + '\n')


def get_agentmail_client() -> AgentMail:
    env = load_env(AGENTMAIL_ENV)
    api_key = env.get('AGENTMAIL_API_KEY') or env.get('API_KEY')
    return AgentMail(api_key=api_key)


def get_sheets_service():
    env = load_env(GOOGLE_ENV)
    creds = Credentials(
        token=env.get('GOOGLE_SHEETS_ACCESS_TOKEN') or None,
        refresh_token=env.get('GOOGLE_SHEETS_REFRESH_TOKEN'),
        token_uri='https://oauth2.googleapis.com/token',
        client_id=env.get('GOOGLE_SHEETS_CLIENT_ID'),
        client_secret=env.get('GOOGLE_SHEETS_CLIENT_SECRET'),
    )
    if not creds.valid:
        creds.refresh(Request())
    return build('sheets', 'v4', credentials=creds)


def find_next_expense_row(svc) -> int:
    vals = svc.spreadsheets().values().get(
        spreadsheetId=SHEET_ID,
        range=f'{SHEET_NAME}!B4:E500'
    ).execute().get('values', [])
    row = 4
    for r in vals:
        b = (r[0] if len(r) > 0 else '').strip()
        c = (r[1] if len(r) > 1 else '').strip()
        d = (r[2] if len(r) > 2 else '').strip()
        e = (r[3] if len(r) > 3 else '').strip()
        if not (b or c or d or e):
            return row
        row += 1
    return row

def find_next_income_row(svc) -> int:
    vals = svc.spreadsheets().values().get(
        spreadsheetId=SHEET_ID,
        range=f'{SHEET_NAME}!G4:J500'
    ).execute().get('values', [])
    row = 4
    for r in vals:
        g = (r[0] if len(r) > 0 else '').strip()
        h = (r[1] if len(r) > 1 else '').strip()
        i = (r[2] if len(r) > 2 else '').strip()
        j = (r[3] if len(r) > 3 else '').strip()
        if not (g or h or i or j):
            return row
        row += 1
    return row


def parse_date(text: str) -> str:
    # From forwarded header: Date: Tue, Mar 10, 2026 at 8:13 PM
    m = re.search(r'Date:\s+[^\n]*?([A-Z][a-z]{2,9})\s+(\d{1,2}),\s+(\d{4})', text)
    if m:
        month, day, year = m.group(1), int(m.group(2)), int(m.group(3))
        try:
            dt = datetime.strptime(f'{month} {day} {year}', '%b %d %Y')
        except ValueError:
            dt = datetime.strptime(f'{month} {day} {year}', '%B %d %Y')
        return dt.strftime('%m/%d/%Y')
    return datetime.now().strftime('%m/%d/%Y')


def parse_amount(text: str) -> float | None:
    patterns = [
        r'Order Total\s*[:\-]?\s*\$\s*([0-9]+(?:\.[0-9]{2})?)',
        r'Total\s*[:\-]?\s*\$\s*([0-9]+(?:\.[0-9]{2})?)',
        r'TOTAL\s*\$\s*([0-9]+(?:\.[0-9]{2})?)',
        r'Grand Total\s*[:\-]?\s*([0-9]+(?:\.[0-9]{2})?)\s*USD',
        r'Total\s*[:\-]?\s*([0-9]+(?:\.[0-9]{2})?)\s*USD',
        r'\+\$\s*([0-9]+(?:\.[0-9]{2})?)',
        r'paid you\s*\$\s*([0-9]+(?:\.[0-9]{2})?)',
    ]
    for p in patterns:
        m = re.search(p, text, flags=re.IGNORECASE)
        if m:
            return float(m.group(1))
    return None


def round_expense(amount: float, description: str) -> float:
    lower = description.lower()
    utility_like = any(k in lower for k in ['utility', 'electric', 'gas bill', 'internet', 'water'])
    if utility_like or amount >= 100:
        return float(int(math.ceil(amount / 5.0) * 5))
    return float(int(math.ceil(amount)))


def classify_receipt(subject: str, text: str) -> tuple[str, str, bool] | None:
    combined = (subject + '\n' + text).lower()

    refund_like = any(k in combined for k in [
        'refund', 'refunded', 'reimbursement', 'reimburse', 'reimbursed',
        'return completed', 'return received', 'your refund', 'amazon refund',
        'credit issued', 'credited', 'merchant refund',
    ])

    if refund_like:
        if 'amazon' in combined:
            return ('Reimbursement', 'Amazon refund', True)
        return ('Reimbursement', 'Refund / reimbursement', True)

    cash_app_income = (
        ('cash app' in combined or 'cash@square.com' in combined or 'notifications.cash.app' in combined)
        and ('payment received' in combined or 'paid you' in combined)
    )
    if cash_app_income:
        return ('Reimbursement', 'Cash App reimbursement', True)

    # Explicit merchant cues
    if 'amazon' in combined:
        if 'prime video' in combined or re.search(r'amazon\.com order of ', subject, flags=re.IGNORECASE):
            return ('Entertainment', 'Amazon Prime Video purchase', False)
        return ('Household Items', 'Amazon purchase', False)
    if 'apple' in combined and 'receipt' in combined:
        return ('My Music Career', 'Apple App Store purchase', False)

    # Generic forwarded receipt from Ryan: if it looks like a receipt and has a total, accept.
    if ('receipt' in combined or 'order total' in combined or 'total $' in combined):
        return ('Other', 'Forwarded receipt purchase', False)

    return None


def extract_amazon_items(subject: str, text: str) -> list[str]:
    items: list[str] = []
    seen: set[str] = set()

    def add(item: str):
        item = re.sub(r'\s+', ' ', item).strip(' .-*\t\r\n')
        low = item.lower()
        if not item or len(item) < 3:
            return
        banned = [
            'amazon', 'hello ryan', 'order details', 'view order details', 'view or edit order',
            'ordered', 'shipped', 'out for delivery', 'delivered', 'sold by:', 'grand total:',
            'item subtotal:', 'total before tax:', 'tax collected:', 'order #', 'arriving',
        ]
        if any(low == b or low.startswith(b) for b in banned):
            return
        if re.fullmatch(r'\$?[0-9]+(?:\.[0-9]{2})?', item):
            return
        if low.startswith('quantity:'):
            return
        for existing in list(items):
            ex_low = existing.lower()
            if low == ex_low or low in ex_low:
                return
            if ex_low in low:
                items.remove(existing)
                seen.discard(existing)
                break
        if item not in seen:
            seen.add(item)
            items.append(item)

    # Physical-order plaintext items: lines beginning with "* "
    for ln in (text or '').splitlines():
        t = ln.strip()
        if t.startswith('* '):
            add(t[2:])

    # Digital Amazon order subject: "Amazon.com order of Tenet."
    m = re.search(r'Amazon\.com order of\s+(.+?)\.?$', subject.strip(), flags=re.IGNORECASE)
    if m:
        add(m.group(1))

    # Forwarded subject fallback: Ordered: "Item..." and 1 more item
    m = re.search(r'Ordered:\s*"([^"]+)"', subject, flags=re.IGNORECASE)
    if m:
        add(m.group(1))

    # Digital order body: title usually appears immediately before "Sold by:"
    for m in re.finditer(r'\n([^\n]{3,200})\n\nSold by:', text or '', flags=re.IGNORECASE):
        add(m.group(1))

    return items


def infer_description(subject: str, text: str, fallback: str) -> str:
    s = subject.strip()
    combined = (subject + '\n' + text).lower()
    refund_like = any(k in combined for k in [
        'refund', 'refunded', 'reimbursement', 'reimburse', 'reimbursed',
        'return completed', 'return received', 'your refund', 'amazon refund',
        'credit issued', 'credited', 'merchant refund',
    ])
    cash_app_income = (
        ('cash app' in combined or 'cash@square.com' in combined or 'notifications.cash.app' in combined)
        and ('payment received' in combined or 'paid you' in combined)
    )

    if cash_app_income:
        payer = None
        note = None
        m = re.search(r'\n([^\n]+?)\s+paid you\s+\$[0-9]+(?:\.[0-9]{2})?', text, flags=re.IGNORECASE)
        if m:
            payer = m.group(1).strip(' .-\t\r\n')
        m = re.search(r'\nFor\s+(.+)', text, flags=re.IGNORECASE)
        if m:
            note = m.group(1).strip(' .-\t\r\n')
        if payer and note:
            return f"{payer} - {note[:100]}"
        if payer:
            return f"{payer} - Cash App reimbursement"
        return 'Cash App reimbursement'

    # Prefer concrete item names from message body/subject when available.
    items = extract_amazon_items(subject, text)
    if items:
        if refund_like:
            prefix = 'Amazon refund'
        else:
            prefix = 'Amazon Prime Video' if 'prime video' in combined or re.search(r'amazon\.com order of ', s, flags=re.IGNORECASE) else 'Amazon'
        if len(items) == 1:
            return f"{prefix} - {items[0][:120]}"
        if len(items) == 2:
            return f"{prefix} - {items[0][:70]} + {items[1][:70]}"
        return f"{prefix} - {items[0][:60]} + {items[1][:60]} + {len(items)-2} more"

    # Subject fallback: Example "Ordered: "Mayfair..." and 1 more item"
    m = re.search(r'Ordered:\s*"([^"]+)"\s*(and\s+\d+\s+more\s+item[s]?)?', s, flags=re.IGNORECASE)
    if m:
        item = m.group(1).strip()
        extra = m.group(2).strip() if m.group(2) else ''
        prefix = 'Amazon refund' if refund_like else 'Amazon'
        if extra:
            return f"{prefix} - {item} ({extra})"
        return f"{prefix} - {item}"

    # Specific fallback for refunds: avoid dumb forwarded-header descriptions.
    if refund_like:
        for ln in (text or '').splitlines():
            t = re.sub(r'\s+', ' ', ln).strip(' .-\t\r\n')
            low = t.lower()
            if not t or len(t) < 4:
                continue
            if any(bad in low for bad in [
                'forwarded message', 'from:', 'subject:', 'date:', 'to:',
                'amazon.com', 'refund issued', 'your refund has been processed',
                'your refund', 'refund total', 'order total', 'total',
            ]):
                continue
            if re.fullmatch(r'\$?[0-9]+(?:\.[0-9]{2})?', t):
                continue
            return f"Amazon refund - {t[:100]}"
        return 'Amazon refund'

    # Fallback: use first meaningful non-empty line from body when available
    for ln in (text or '').splitlines():
        t = ln.strip()
        if t and len(t) > 6 and 'forwarded message' not in t.lower():
            return f"Receipt - {t[:80]}"

    return fallback

def get_expense_categories(svc) -> set[str]:
    vals = svc.spreadsheets().values().get(
        spreadsheetId=SHEET_ID,
        range=EXPENSE_DROPDOWN_RANGE
    ).execute().get('values', [])
    return {r[0].strip() for r in vals if r and r[0].strip()}


def get_income_categories(svc) -> set[str]:
    vals = svc.spreadsheets().values().get(
        spreadsheetId=SHEET_ID,
        range=INCOME_DROPDOWN_RANGE
    ).execute().get('values', [])
    return {r[0].strip() for r in vals if r and r[0].strip()}


def get_sheet_id(svc, title: str) -> int:
    meta = svc.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
    return next(s['properties']['sheetId'] for s in meta['sheets'] if s['properties']['title'] == title)


def append_expense(svc, date_str: str, amount: float, description: str, category: str):
    row = find_next_expense_row(svc)
    sheet_id = get_sheet_id(svc, SHEET_NAME)
    row_idx = row - 1

    # Copy the exact visual formatting from the previous expense row before writing values.
    # This preserves alignment, borders, font, fills, and any row-specific styling.
    source_row_idx = max(3, row_idx - 1)
    requests = [
        {
            'copyPaste': {
                'source': {
                    'sheetId': sheet_id,
                    'startRowIndex': source_row_idx,
                    'endRowIndex': source_row_idx + 1,
                    'startColumnIndex': 1,
                    'endColumnIndex': 5,
                },
                'destination': {
                    'sheetId': sheet_id,
                    'startRowIndex': row_idx,
                    'endRowIndex': row_idx + 1,
                    'startColumnIndex': 1,
                    'endColumnIndex': 5,
                },
                'pasteType': 'PASTE_FORMAT',
            }
        },
        {
            'repeatCell': {
                'range': {
                    'sheetId': sheet_id,
                    'startRowIndex': row_idx,
                    'endRowIndex': row_idx + 1,
                    'startColumnIndex': 1,
                    'endColumnIndex': 5,
                },
                'cell': {
                    'userEnteredFormat': {
                        'horizontalAlignment': 'LEFT'
                    }
                },
                'fields': 'userEnteredFormat.horizontalAlignment'
            }
        }
    ]
    svc.spreadsheets().batchUpdate(spreadsheetId=SHEET_ID, body={'requests': requests}).execute()

    rng = f"{SHEET_NAME}!B{row}:E{row}"
    svc.spreadsheets().values().update(
        spreadsheetId=SHEET_ID,
        range=rng,
        valueInputOption='USER_ENTERED',
        body={'values': [[date_str, amount, description, category]]}
    ).execute()
    return row


def append_income(svc, date_str: str, amount: float, description: str, category: str):
    row = find_next_income_row(svc)
    sheet_id = get_sheet_id(svc, SHEET_NAME)
    row_idx = row - 1

    source_row_idx = max(3, row_idx - 1)
    requests = [
        {
            'copyPaste': {
                'source': {
                    'sheetId': sheet_id,
                    'startRowIndex': source_row_idx,
                    'endRowIndex': source_row_idx + 1,
                    'startColumnIndex': 6,
                    'endColumnIndex': 10,
                },
                'destination': {
                    'sheetId': sheet_id,
                    'startRowIndex': row_idx,
                    'endRowIndex': row_idx + 1,
                    'startColumnIndex': 6,
                    'endColumnIndex': 10,
                },
                'pasteType': 'PASTE_FORMAT',
            }
        },
        {
            'repeatCell': {
                'range': {
                    'sheetId': sheet_id,
                    'startRowIndex': row_idx,
                    'endRowIndex': row_idx + 1,
                    'startColumnIndex': 6,
                    'endColumnIndex': 10,
                },
                'cell': {
                    'userEnteredFormat': {
                        'horizontalAlignment': 'LEFT'
                    }
                },
                'fields': 'userEnteredFormat.horizontalAlignment'
            }
        }
    ]
    svc.spreadsheets().batchUpdate(spreadsheetId=SHEET_ID, body={'requests': requests}).execute()

    rng = f"{SHEET_NAME}!G{row}:J{row}"
    svc.spreadsheets().values().update(
        spreadsheetId=SHEET_ID,
        range=rng,
        valueInputOption='USER_ENTERED',
        body={'values': [[date_str, amount, description, category]]}
    ).execute()
    return row


def main():
    state = load_state()
    processed = state.setdefault('processed', {})

    client = get_agentmail_client()
    msgs = client.inboxes.messages.list(inbox_id=INBOX, limit=40).messages
    svc = get_sheets_service()
    valid_expense_categories = get_expense_categories(svc)
    valid_income_categories = get_income_categories(svc)

    added = 0
    skipped = 0

    for m in msgs:
        d = m.model_dump()
        mid = d.get('message_id')
        if not mid or mid in processed:
            continue

        from_line = d.get('from_') or ''

        subject = d.get('subject') or ''
        detail = client.inboxes.messages.get(inbox_id=INBOX, message_id=mid).model_dump()
        text = (detail.get('text') or '').strip()
        if not text:
            skipped += 1
            processed[mid] = {'status': 'skip_no_text'}
            continue

        cls = classify_receipt(subject, text)
        if not cls:
            skipped += 1
            processed[mid] = {'status': 'skip_unclassified', 'subject': subject}
            continue

        category, desc_base, is_income = cls
        if is_income:
            if category not in valid_income_categories:
                category = 'Reimbursement' if 'Reimbursement' in valid_income_categories else 'Other'
        else:
            if category not in valid_expense_categories:
                category = 'Other'
        amount = parse_amount(text)
        if amount is None:
            skipped += 1
            processed[mid] = {'status': 'skip_no_amount', 'subject': subject}
            continue

        date_str = parse_date(text)
        description = infer_description(subject, text, desc_base)

        if is_income:
            stored_amount = float(amount)
            row = append_income(svc, date_str, stored_amount, description, category)
        else:
            # Apply Ryan's rounding preference for expenses
            stored_amount = round_expense(amount, description)
            row = append_expense(svc, date_str, stored_amount, description, category)

        processed[mid] = {
            'status': 'added',
            'sheet_section': 'income' if is_income else 'expense',
            'row': row,
            'date': date_str,
            'amount_raw': amount,
            'amount_stored': stored_amount,
            'description': description,
            'category': category,
            'subject': subject,
        }
        added += 1

    save_state(state)
    print(f'added={added}; skipped={skipped}; processed_total={len(processed)}')


if __name__ == '__main__':
    main()
