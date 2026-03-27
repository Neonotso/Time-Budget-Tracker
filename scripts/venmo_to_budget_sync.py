#!/usr/bin/env python3
"""
Venmo to Budget Sync Script
Automatically adds new Venmo transactions to Google Sheets monthly budget.
- Payments TO Ryan (from others) → Income section (columns G-J)
- Payments FROM Ryan (to others) → Expense section (columns B-E)
"""

import os
import json
import asyncio
from datetime import datetime
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Import our working Venmo client
import sys
sys.path.append('/Users/ryantaylorvegh/.openclaw/workspace/scripts')
from venmo_transactions import VenmoClient, _pretty_tx

WORKDIR = Path('/Users/ryantaylorvegh/.openclaw/workspace')
GOOGLE_ENV = WORKDIR / '.secrets/google_sheets & drive.env'
STATE_PATH = WORKDIR / 'memory/venmo_budget_sync_state.json'

# Budget spreadsheet configuration
SHEET_ID = '1Eg5hKm2xSDf6-mEYYG9pR1X7kFtiO6C5jeRO4zDzw90'
SHEET_NAME = '💰 Transactions'

# Valid categories from the budget
INCOME_CATEGORIES = {'Lessons', 'PIER Church', 'Reimbursement', 'Other'}
EXPENSE_CATEGORIES = {'Gas for Car', 'Household Items', 'Entertainment', 'Dining Out', 'Other', 'Gas Bill', 'My Music Career', 'Misc Helpfulness', 'Fixed Expenses'}

def load_env(path: Path) -> dict:
    """Load environment variables from file."""
    d = {}
    if not path.exists():
        return d
    for raw in path.read_text().splitlines():
        if '=' in raw and not raw.startswith('#'):
            k, v = raw.split('=', 1)
            d[k.strip()] = v.strip().strip('"')
    return d

def load_state() -> dict:
    """Load last sync state to avoid duplicates."""
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text())
        except:
            return {"last_sync": None, "processed_ids": [], "venmo_ids": []}
    return {"last_sync": None, "processed_ids": [], "venmo_ids": []}

def save_state(state: dict):
    """Save state."""
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2))

def get_google_sheets_service():
    """Initialize Google Sheets API service."""
    env = load_env(GOOGLE_ENV)
    
    creds = Credentials(
        token=None,
        refresh_token=env.get('GOOGLE_SHEETS_REFRESH_TOKEN'),
        token_uri='https://oauth2.googleapis.com/token',
        client_id=env.get('GOOGLE_SHEETS_CLIENT_ID'),
        client_secret=env.get('GOOGLE_SHEETS_CLIENT_SECRET'),
    )
    
    creds.refresh(Request())
    return build('sheets', 'v4', credentials=creds)

def get_sheet_id(svc, title: str) -> int:
    """Get sheet ID by title."""
    meta = svc.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
    return next(s['properties']['sheetId'] for s in meta['sheets'] if s['properties']['title'] == title)

def find_next_row(svc, range_str: str, start_row: int = 4) -> int:
    """Find the next empty row in a given range."""
    result = svc.spreadsheets().values().get(
        spreadsheetId=SHEET_ID,
        range=range_str
    ).execute()
    values = result.get('values', [])
    
    # Find the last row that has actual content
    row = start_row
    for r in values:
        # Check if this row has any non-empty content
        if any(cell.strip() for cell in r if cell):
            row += 1
    return row

def normalize_amount(amount_str: str) -> float:
    """Convert amount string to float, handling $, commas, etc."""
    if not amount_str:
        return 0.0
    # Remove $ and commas
    cleaned = amount_str.replace('$', '').replace(',', '').strip()
    try:
        return float(cleaned)
    except ValueError:
        return 0.0

def normalize_date(date_str: str) -> str:
    """Convert date to MM/DD/YYYY format for consistent comparison (no leading zeros)."""
    if not date_str:
        return ''
    
    # Handle ISO format: 2026-03-24T22:36:10
    if 'T' in date_str:
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', ''))
            return dt.strftime('%-m/%d/%Y')  # No leading zero on month
        except:
            pass
    
    # Handle ISO date: 2026-03-24
    if len(date_str) == 10 and date_str[4] == '-':
        try:
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            return dt.strftime('%-m/%d/%Y')  # No leading zero on month
        except:
            pass
    
    # Already in MM/DD/YYYY - remove leading zeros
    if '/' in date_str:
        try:
            parts = date_str.strip().split('/')
            if len(parts) == 3:
                month = int(parts[0])
                day = int(parts[1])
                year = parts[2]
                return f'{month}/{day}/{year}'
        except:
            pass
    
    return date_str.strip()

def is_current_month(date_str: str, now: datetime | None = None) -> bool:
    """Return True only for transactions in the active calendar month."""
    normalized = normalize_date(date_str)
    if not normalized:
        return False
    try:
        month_s, day_s, year_s = normalized.split('/')
        dt = datetime(int(year_s), int(month_s), int(day_s))
    except Exception:
        return False

    now = now or datetime.now()
    return dt.year == now.year and dt.month == now.month

def get_existing_transaction_ids(svc) -> set:
    """Get identifiers of existing transactions to prevent duplicates.
    
    Uses normalized date + amount + partial description to identify transactions.
    Checks both Expense and Income sections.
    """
    existing_ids = set()
    
    # Check Expense section (B:E)
    try:
        result = svc.spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range=f'{SHEET_NAME}!B4:E500'
        ).execute()
        values = result.get('values', [])
        for row in values:
            if len(row) >= 3:
                date_val = normalize_date(row[0].strip() if row[0] else '')
                amount_val = normalize_amount(row[1].strip() if row[1] else '')
                desc_val = (row[2].strip() if len(row) > 2 and row[2] else '').lower()[:50]
                # Use date + amount as primary key (descriptions may differ)
                tx_id = f"EXPENSE|{date_val}|{amount_val}"
                existing_ids.add(tx_id)
    except Exception as e:
        print(f"Warning: Could not read expense transactions: {e}")
    
    # Check Income section (G:J)
    try:
        result = svc.spreadsheets().values().get(
            spreadsheetId=SHEET_ID,
            range=f'{SHEET_NAME}!G4:J500'
        ).execute()
        values = result.get('values', [])
        for row in values:
            if len(row) >= 3:
                date_val = normalize_date(row[0].strip() if row[0] else '')
                amount_val = normalize_amount(row[1].strip() if row[1] else '')
                desc_val = (row[2].strip() if len(row) > 2 and row[2] else '').lower()[:50]
                # Use date + amount as primary key
                tx_id = f"INCOME|{date_val}|{amount_val}"
                existing_ids.add(tx_id)
    except Exception as e:
        print(f"Warning: Could not read income transactions: {e}")
    
    return existing_ids

def infer_category(note: str, is_income: bool) -> str:
    """Infer transaction category based on note/description."""
    note_lower = (note or '').lower()
    
    if is_income:
        # Income categories
        if 'lesson' in note_lower or 'piano' in note_lower or 'guitar' in note_lower or 'drum' in note_lower or 'voice' in note_lower:
            return 'Lessons'
        if 'pier' in note_lower or 'church' in note_lower:
            return 'PIER Church'
        if 'refund' in note_lower or 'reimburse' in note_lower:
            return 'Reimbursement'
        return 'Lessons'  # Default for Venmo payments (mostly lessons)
    else:
        # Expense categories
        if 'gas' in note_lower and ('car' in note_lower or 'station' in note_lower):
            return 'Gas for Car'
        if 'food' in note_lower or 'dinner' in note_lower or 'lunch' in note_lower or 'restaurant' in note_lower:
            return 'Dining Out'
        if 'music' in note_lower or 'lesson' in note_lower:
            return 'My Music Career'
        return 'Other'

def format_date(date_str: str) -> str:
    """Convert dates to M/D/YYYY format for stable duplicate matching."""
    if not date_str:
        now = datetime.now()
        return f"{now.month}/{now.day}/{now.year}"

    try:
        if 'T' in date_str:
            dt = datetime.fromisoformat(date_str.replace('Z', ''))
            return f"{dt.month}/{dt.day}/{dt.year}"
        if len(date_str) == 10 and date_str[4] == '-':
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            return f"{dt.month}/{dt.day}/{dt.year}"
        if '/' in date_str:
            parts = date_str.strip().split('/')
            if len(parts) == 3:
                month = int(parts[0])
                day = int(parts[1])
                year = int(parts[2])
                return f"{month}/{day}/{year}"
        return date_str.strip()
    except:
        return date_str.strip()

def format_amount(amount: float) -> float:
    """Store amounts as numbers so Sheets formatting can render currency."""
    return round(float(amount), 2)

def build_description(tx: dict, is_income: bool) -> str:
    """Create a clearer human-friendly description than raw Venmo notes."""
    note = (tx.get('note') or '').strip()
    payer = (tx.get('from') or '').strip()
    payee = (tx.get('to') or '').strip()

    if is_income:
        actor = payer or 'Unknown sender'
        if not note:
            return actor
        low = note.lower()
        if low in {'lesson', 'lessons'}:
            return f"{actor} lesson"
        if actor.lower() in low:
            return note
        return f"{actor} - {note}"

    actor = payee or payer or 'Venmo payment'
    if not note:
        return actor
    if actor.lower() in note.lower():
        return note
    return f"{actor} - {note}"

def copy_row_format(svc, sheet_name: str, source_row: int, dest_row: int, start_col: int, end_col: int):
    """Copy formatting from a known-good template row into the destination row."""
    sheet_id = get_sheet_id(svc, sheet_name)
    source_row_idx = max(3, source_row - 1)
    dest_row_idx = dest_row - 1
    svc.spreadsheets().batchUpdate(
        spreadsheetId=SHEET_ID,
        body={
            'requests': [{
                'copyPaste': {
                    'source': {
                        'sheetId': sheet_id,
                        'startRowIndex': source_row_idx,
                        'endRowIndex': source_row_idx + 1,
                        'startColumnIndex': start_col,
                        'endColumnIndex': end_col,
                    },
                    'destination': {
                        'sheetId': sheet_id,
                        'startRowIndex': dest_row_idx,
                        'endRowIndex': dest_row_idx + 1,
                        'startColumnIndex': start_col,
                        'endColumnIndex': end_col,
                    },
                    'pasteType': 'PASTE_FORMAT',
                }
            }]
        }
    ).execute()

def find_first_empty_row(svc, sheet_name: str, column: str) -> int:
    """Find the first empty row in a specific column."""
    result = svc.spreadsheets().values().get(
        spreadsheetId=SHEET_ID,
        range=f'{sheet_name}!{column}4:{column}1000'
    ).execute()
    values = result.get('values', [])
    
    # Find first row without content
    for i, r in enumerate(values):
        row_num = i + 4
        if not (r and r[0] and str(r[0]).strip()):
            return row_num
    # All rows have content, return next row
    return len(values) + 4

def add_transactions_to_sheet(svc, transactions: list, existing_ids: set, processed_venmo_ids: set) -> dict:
    """Add new transactions to the budget sheet.
    
    Returns dict with counts: {'income_added': N, 'expense_added': M, 'venmo_ids': [... newly processed IDs]}
    """
    if not transactions:
        return {'income_added': 0, 'expense_added': 0, 'venmo_ids': []}
    
    new_venmo_ids = []  # Track new Venmo IDs for state file
    
    income_rows = []
    expense_rows = []
    income_count = 0
    expense_count = 0
    
    for tx in transactions:
        # Skip transfers (bank transfers have no amount/from/to)
        if tx['amount'] is None:
            continue

        # Only sync the active month into the current month's budget sheet.
        if not is_current_month(tx['created_time']):
            continue
        
        # Determine direction: money TO Ryan = income, money FROM Ryan = expense
        to_ryan = tx['to'] and 'Ryan' in tx['to']
        from_ryan = tx['from'] and 'Ryan' in tx['from']
        
        is_income = to_ryan and not from_ryan
        is_expense = from_ryan and not to_ryan
        
        if not is_income and not is_expense:
            continue  # Skip ambiguous transactions
        
        # Format the transaction
        date_str = format_date(tx['created_time'])
        amount_str = format_amount(tx['amount'])
        description = build_description(tx, is_income)
        category = infer_category(tx['note'] or description, is_income)

        # Get sender for duplicate check (to prevent James Luke's $30 blocking Valentino's $30)
        sender = (tx.get('from') or '').strip() or (tx.get('to') or '').strip() or 'unknown'
        
        # Create ID for duplicate check using normalized date + amount + sender.
        # This prevents same-amount transactions from different people on same day being treated as duplicates.
        tx_type = "INCOME" if is_income else "EXPENSE"
        tx_id = f"{tx_type}|{normalize_date(date_str)}|{round(float(tx['amount']), 2)}|{sender}"
        
        if tx_id in existing_ids:
            continue  # Skip duplicate
        
        existing_ids.add(tx_id)
        
        # Also track Venmo transaction ID to prevent re-adding the same Venmo transaction
        venmo_id = tx.get('id')
        if venmo_id and venmo_id in processed_venmo_ids:
            continue  # Already processed this Venmo ID
        if venmo_id:
            new_venmo_ids.append(venmo_id)
        
        if is_income:
            income_rows.append([date_str, amount_str, description, category])
            income_count += 1
        else:
            expense_rows.append([date_str, amount_str, description, category])
            expense_count += 1
    
    # Add to appropriate sections
    result = {'income_added': 0, 'expense_added': 0}
    
    # Add income transactions
    if income_rows:
        start_row = find_first_empty_row(svc, SHEET_NAME, 'G')
        template_row = max(4, start_row - 1)
        for offset in range(len(income_rows)):
            copy_row_format(svc, SHEET_NAME, template_row, start_row + offset, 6, 10)

        income_range = f'{SHEET_NAME}!G{start_row}:J{start_row + len(income_rows) - 1}'
        svc.spreadsheets().values().update(
            spreadsheetId=SHEET_ID,
            range=income_range,
            valueInputOption='USER_ENTERED',
            body={'values': income_rows}
        ).execute()
        result['income_added'] = income_count
        print(f"Added {income_count} income transaction(s) at row {start_row}")

    # Add expense transactions
    if expense_rows:
        start_row = find_first_empty_row(svc, SHEET_NAME, 'B')
        template_row = max(4, start_row - 1)
        for offset in range(len(expense_rows)):
            copy_row_format(svc, SHEET_NAME, template_row, start_row + offset, 1, 5)

        expense_range = f"{SHEET_NAME}!B{start_row}:E{start_row + len(expense_rows) - 1}"
        svc.spreadsheets().values().update(
            spreadsheetId=SHEET_ID,
            range=expense_range,
            valueInputOption='USER_ENTERED',
            body={'values': expense_rows}
        ).execute()
        result['expense_added'] = expense_count
        print(f"Added {expense_count} expense transaction(s) at row {start_row}")
    
    # Include newly processed Venmo IDs in return value
    result['venmo_ids'] = new_venmo_ids
    
    return result

async def main_async():
    """Main async function."""
    print("Starting Venmo to Budget sync...")
    
    # Load Venmo credentials
    venmo_env = load_env(WORKDIR / '.secrets/venmo_creds.env')
    access_token = (
        venmo_env.get('VENMO_ACCESS_TOKEN') or 
        venmo_env.get('VENMO_TOKEN') or 
        venmo_env.get('access_token')
    )
    
    if not access_token:
        print("Error: Missing VENMO_ACCESS_TOKEN (or VENMO_TOKEN/access_token)")
        return 1
    
    # Initialize Venmo client
    try:
        client = VenmoClient(access_token=access_token.strip())
    except Exception as e:
        print(f"Error initializing Venmo client: {e}")
        return 1
    
    # Get recent Venmo transactions
    try:
        print("Fetching recent Venmo transactions...")
        txs_raw = await client.get_transactions()
        if not txs_raw:
            print("No Venmo transactions found")
            return 0
        
        # Format transactions using _pretty_tx
        txs = [_pretty_tx(tx) for tx in txs_raw[:50]]
        print(f"Found {len(txs)} recent Venmo transactions")
        
        # Show sample for logging
        for tx in txs[:10]:
            if tx['amount'] is not None:
                direction = "→ Ryan" if tx['to'] and 'Ryan' in tx['to'] else "Ryan →"
                print(f"  {tx['created_time'][:10]} | ${tx['amount']:.2f} | {direction} | {tx['note'] or tx['from']}")
        
    except Exception as e:
        print(f"Error fetching Venmo transactions: {e}")
        return 1
    
    # Initialize Google Sheets service
    try:
        print("Connecting to Google Sheets...")
        svc = get_google_sheets_service()
    except Exception as e:
        print(f"Error connecting to Google Sheets: {e}")
        return 1
    
    # Get existing transaction IDs to prevent duplicates
    try:
        print("Checking for existing transactions in budget...")
        existing_ids = get_existing_transaction_ids(svc)
        print(f"Found {len(existing_ids)} existing transactions in budget")
    except Exception as e:
        print(f"Warning: Could not check existing transactions: {e}")
        existing_ids = set()
    
    # Load previously processed Venmo IDs from state
    state = load_state()
    processed_venmo_ids = set(state.get('venmo_ids', []))
    print(f"Loaded {len(processed_venmo_ids)} previously processed Venmo IDs from state")
    
    # Add new transactions to budget
    try:
        print("Adding new transactions to budget...")
        result = add_transactions_to_sheet(svc, txs, existing_ids, processed_venmo_ids)
        
        total_added = result['income_added'] + result['expense_added']
        print(f"Successfully added {total_added} transaction(s)")
        print(f"  - Income: {result['income_added']}")
        print(f"  - Expense: {result['expense_added']}")
        
        # Save state with processed Venmo IDs for deduplication
        all_venmo_ids = list(set(processed_venmo_ids) | set(result.get('venmo_ids', [])))
        state = {
            "last_sync": datetime.now().isoformat(),
            "income_added": result['income_added'],
            "expense_added": result['expense_added'],
            "total_processed": len(txs),
            "venmo_ids": all_venmo_ids
        }
        save_state(state)
        
        return 0
        
    except Exception as e:
        print(f"Error during transaction sync: {e}")
        import traceback
        traceback.print_exc()
        return 1

def main():
    """Entry point."""
    return asyncio.run(main_async())

if __name__ == "__main__":
    exit(main())