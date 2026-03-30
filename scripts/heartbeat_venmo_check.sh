#!/bin/bash
# Heartbeat Venmo-to-budget check wrapper
# Ensures VENMO_ACCESS_TOKEN is set before running venmo_transactions.py

# Load Venmo credentials from secrets
if [[ -f "/Users/ryantaylorvegh/.openclaw/workspace/.secrets/venmo_creds.env" ]]; then
    export VENMO_ACCESS_TOKEN=$(grep access_token /Users/ryantaylorvegh/.openclaw/workspace/.secrets/venmo_creds.env | cut -d= -f2)
fi

# Run the Venmo transactions check
exec /Users/ryantaylorvegh/.openclaw/workspace/venv/bin/python /Users/ryantaylorvegh/.openclaw/workspace/scripts/venmo_transactions.py transactions --limit 20