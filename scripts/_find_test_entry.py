from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from pathlib import Path
import json

ENV = Path('/Users/ryantaylorvegh/.openclaw/workspace/.secrets/google_sheets & drive.env')
vals = {}
for raw in ENV.read_text().splitlines():
    s = raw.strip()
    if not s or s.startswith('#') or '=' not in s: continue
    k,v = s.split('=',1); vals[k.strip()] = v.strip().strip('"').strip("'")
creds = Credentials(token=vals.get('GOOGLE_SHEETS_ACCESS_TOKEN') or None, refresh_token=vals.get('GOOGLE_SHEETS_REFRESH_TOKEN'), token_uri='https://oauth2.googleapis.com/token', client_id=vals.get('GOOGLE_SHEETS_CLIENT_ID'), client_secret=vals.get('GOOGLE_SHEETS_CLIENT_SECRET'))
if not creds.valid: creds.refresh(Request())
svc = build('sheets','v4',credentials=creds)

# Get all rows to find test entry
result = svc.spreadsheets().get(spreadsheetId='16f75U8IZjGkrgNeUyk7haDU-_isrBlmd6glnW0ah5BA', ranges=['Sheet1!A1:Z2000'], includeGridData=True).execute()

data = []
for sheet in result.get('sheets', []):
    for row in sheet.get('data', [{}])[0].get('rowData', []):
        row_vals = []
        for val in row.get('values', []):
            if 'formattedValue' in val:
                row_vals.append(val['formattedValue'])
            elif 'effectiveValue' in val:
                eff = val['effectiveValue']
                if 'stringValue' in eff:
                    row_vals.append(eff['stringValue'])
                elif 'numberValue' in eff:
                    row_vals.append(str(eff['numberValue']))
                else:
                    row_vals.append(str(eff))
            else:
                row_vals.append('')
        data.append(row_vals)

# Find rows with "Ryan" or "Vegh" or "Test"
matches = []
for i, row in enumerate(data):
    row_str = ' '.join(str(v) for v in row).lower()
    if 'ryan' in row_str or 'vegh' in row_str or 'test' in row_str:
        matches.append({'row': i+1, 'data': row[:5]})

Path('/Users/ryantaylorvegh/.openclaw/workspace/memory/_test_entries.json').write_text(json.dumps(matches, indent=2))
print(f'Found {len(matches)} matches')