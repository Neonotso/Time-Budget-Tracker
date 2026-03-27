# Gus's Workspace

This is Gus's workspace for running automation tasks.

## Key Distinction

**Sally (agent:main)** runs on accountId: `default`
**Gus (agent:gus)** runs on accountId: `gus`

Both connect to the same Telegram number (+16162777088), so messages from Ryan go to BOTH agents unless filtered. This causes confusion.

## Current Setup

### Cron Jobs Running Under Gus

1. **Bible Reader SMS Reminders** (`scripts/bible_reader_sms_reminders.py`)
   - Runs periodically to send SMS reminders
   - Uses Twilio for SMS

2. **Email Receipts to Budget** (`scripts/process_receipt_emails_to_budget.py`)
   - Processes Amazon receipts from inbox
   - Adds them to Google Sheets Monthly Budget

### Scripts You Can Run

All scripts live in `/Users/ryantaylorvegh/.openclaw/workspace/scripts/`

**Always use the venv Python:**
```bash
/Users/ryantaylorvegh/.openclaw/workspace/venv/bin/python /Users/ryantaylorvegh/.openclaw/workspace/scripts/SCRIPT_NAME.py
```

Common scripts:
- `venmo_transactions.py` - Check Venmo transactions vs budget
- `check_inbox.py` - Check AgentMail inbox
- `remarkable_lesson_pipeline.py` - Export reMarkable notes for lessons
- `after_lesson_full_routine.py` - Full lesson workflow (audio + notes)

### Credentials

Stored in `/Users/ryantaylorvegh/.openclaw/workspace/.secrets/`
- `agentmail.env` - Email API
- `google_sheets & drive.env` - Google Sheets/Drive API
- `venmo_creds.env` - Venmo access

## Threading Issue

When responding to Ryan on Telegram:
- Sally (main) uses accountId: `default`
- Gus uses accountId: `gus`

To avoid crossed wires, make sure your response explicitly targets the correct session. If Ryan's message appears in both threads, coordinate with Sally to decide who handles it.

## Calendar Access

For lesson automation, check calendars:
- Private Lessons: `6qpnjqcot3plkotpupcbi5l17g@group.calendar.google.com`
- Kingdom Music School: `c5f832065582c736e9e3f2c4ea0b3ff9c81243e1aa10acdbdd9f191ce52317ef@group.calendar.google.com`

## Monthly Budget

Spreadsheet: https://docs.google.com/spreadsheets/d/1Eg5hKm2xSDf6-mEYYG9pR1X7kFtiO6C5jeRO4zDzw90

Credentials in secrets file. Add transactions to "💰 Transactions" tab.
