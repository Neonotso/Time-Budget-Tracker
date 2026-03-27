# Monthly Budget Reset Workflow

## Overview
At the end of each month, duplicate the current Summary and Transactions sheets as frozen snapshots, then reset the active Transactions sheet for the new month.

## Steps to Perform Each Month

### 1. Create Frozen Snapshots (do this BEFORE clearing transactions)

**Goal:** Copy 📊 Summary → `YYYY_MM` and 💰 Transactions → `YYYY_MMtrans

**Steps:**
1. Copy 📊 Summary sheet (preserves formatting, charts, sparklines)
2. Rename copy to `YYYY_MM` (e.g., 2026_03 for March)
3. Copy 💰 Transactions sheet
4. Rename copy to `YYYY_MMtrans`

**Important:** The Google Sheets API copy method is:
```python
service.spreadsheets().sheets().copyTo(
    spreadsheetId=spreadsheet_id,
    sheetId=source_sheet_id,
    body={'destinationSpreadsheetId': spreadsheet_id}
)
```

### 2. Freeze the Data (Convert Formulas to Values)

**Goal:** Make snapshots completely static so they don't change

**Steps:**
1. Get data with `valueRenderOption='UNFORMATTED_VALUE'`
2. Clear the sheet
3. Write back with `valueInputOption='RAW'`
4. Restore sparkline formulas manually (find them in original with `valueRenderOption='FORMULA'`)
5. Protect the sheets:
```python
requests = [{'addProtectedRange': {'protectedRange': {'range': {'sheetId': sheet_id}, 'description': 'Frozen snapshot', 'editors': {'users': []}}}}}]
```

### 3. Reorder Sheets (Optional)

**Goal:** Most recent month (YYYY_MM, YYYY_MMtrans) should appear before the previous month

**Current desired order:**
- Active sheets first (Bank Accounts, Upcoming Payments, Summary, Transactions, etc.)
- Then current month snapshot (YYYY_MM, YYYY_MMtrans)
- Then previous month (YYYY_MM-1, YYYY_MM-1trans)
- Then older months in reverse chronological order

### 4. Update Summary Sheet Reference

**Goal:** Make the Summary sheet reference last month's ending balance

**Steps:**
1. Find cell M3 in 📊 Summary (contains previous month name)
2. Change from old month (e.g., "2026_02") to new previous month (e.g., "2026_01")
3. The formula in M2 already references M3: `=INDIRECT("'" & M3 & "'!E13")`

### 5. Reset Transactions Sheet

**Goal:** Clear all non-recurring transactions for the new month

**Steps:**
1. Keep row 3 (recurring transactions: expenses, income, savings)
2. Clear rows 4 onwards in columns B-F (Expenses), G-J (Income), K-N (Savings)
3. Verify the recurring amounts are correct

### 6. Ensure Amounts Are Numbers (Not Text)

**Critical:** The API must store amounts as numbers, not text with $ signs

**When adding transactions:**
- Use `valueInputOption='USER_ENTERED'` so Google Sheets interprets the values
- Store as plain numbers: `30` not `"$30.00"`

**If amounts get stored as text (with $ or commas):**
```python
def parse_amount(val):
    if isinstance(val, (int, float)):
        return val
    import re
    try:
        return float(re.sub(r'[$,]', '', str(val)))
    except:
        return val
```

## Google Sheets API Setup

**Credentials location:** `~/.openclaw/workspace/.secrets/google_sheets & drive.env`

**Spreadsheet ID:** `1Eg5hKm2xSDf6-mEYYG9pR1X7kFtiO6C5jeRO4zDzw90`

## Notes

- Transactions with dates like "3/1/2026" are stored as Excel date serial numbers (e.g., 46082) when using UNFORMATTED_VALUE
- Sparklines are formulas containing "SPARKLINE" - preserve these when freezing
- The frozen snapshots should be protected to prevent accidental edits

---

## Adding Transactions (Runtime)

### Preserving Formatting

When adding new transactions, always copy the formatting from an existing row to maintain consistency:

1. **First, copy formatting** from a neighboring row using `copyPaste`:
```python
requests = [
    {
        'copyPaste': {
            'source': {
                'sheetId': sheet_id,
                'startRowIndex': source_row - 1,  # 0-indexed
                'endRowIndex': source_row,
                'startColumnIndex': 1 if Expenses else 6,  # B=1 for Expenses, G=6 for Income
                'endColumnIndex': 5 if Expenses else 10   # E for Expenses, J for Income
            },
            'destination': {
                'sheetId': sheet_id,
                'startRowIndex': target_row - 1,
                'endRowIndex': target_row,
                'startColumnIndex': 1 if Expenses else 6,
                'endColumnIndex': 5 if Expenses else 10
            },
            'pasteType': 'PASTE_FORMAT'
        }
    }
]
service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={'requests': requests}).execute()
```

2. **Then, update values** (after formatting is applied):
```python
service.spreadsheets().values().update(
    spreadsheetId=spreadsheet_id,
    range=f"'💰 Transactions'!B{target_row}:E{target_row}",  # or G:J for Income
    valueInputOption='USER_ENTERED',
    body={'values': [['3/14/2026', 17, 'Description', 'Category']]}
).execute()
```

### Handling Refunds

**Rule:** Refunds always go in the **Income** section (columns G:J), not Expenses.

- **Category:** Use "Reimbursement" for Amazon/merchant refunds
- **Placement:** Add as a new row immediately after the last Income entry (not in a blank row below)
- **Formatting:** Copy from the row above to match font (Lato), borders (dotted), alignment, etc.

---

### Adding Amazon Transactions (CRITICAL)

When adding Amazon purchases to the budget:

1. **Always check the Amazon order confirmation email** for the actual item description
2. **Parse the email body** to get the specific product name(s), not just "Amazon.com *"
3. **Use the correct category** based on what was purchased:
   - **Entertainment:** Movies, TV shows, digital media, video games
   - **Household Items:** Physical products for the home (bulbs, toilet seats, etc.)
   - **Books/Media:** Physical books, CDs, DVDs
4. **If the email shows "$X.XX" (just the total with asterisk)**, this is a placeholder - search for the actual order confirmation email to get the real description
5. **Round expenses to nearest $1** (or $5 for larger purchases) - but keep the description accurate

---

### Adding Any New Transaction (CRITICAL)

**NEVER overwrite an existing row! Always append to the next empty row.**

1. First, read the existing data to find the last row with data in the expense (B:E) or income (G:J) columns
2. Add the new transaction to the next available row (last_row + 1)
3. Use hardcoded row numbers only when explicitly restoring a known value (like restoring "recurring" from history)
4. For recurring expenses like "Fixed Expenses", check the frozen monthly sheets to find the correct template value

**Expense Categories:**
- Groceries
- Dining Out
- Gas for Car
- Household Items
- Entertainment
- Other
- Gas Bill
- Electric Bill
- Fixed Expenses
- Misc Helpfulness
- My Music Career
- Lesson Advertising
- Car Expenses
- Healthcare
- Church Expenses
- Clothes
- Gifts

**Income Categories:**
- Lessons
- PIER Church
- Reimbursement
- Other

### Adding Gas/Petroleum Transactions

When adding gas purchases, include:
- Station name and loyalty program (e.g., "Club Citgo")
- Price per gallon
- Total gallons (if calculable)
- Do NOT include dollar amount in description (it's in the amount column)
- Example: "Citgo - Club Citgo, $3.869/gal, 12.4 gallons"

**Example:**
- ❌ Bad: "Amazon - Amazon.com *"
- ❌ Bad: "Amazon - $4.00"
- ✅ Good: "Amazon Prime Video - The Hunger Games: The Ballad of Songbirds and Snakes"
