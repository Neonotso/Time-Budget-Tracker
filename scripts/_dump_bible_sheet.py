from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

ENV=Path('/Users/ryantaylorvegh/.openclaw/workspace/.secrets/google_sheets & drive.env')
vals={}
for raw in ENV.read_text().splitlines():
 s=raw.strip()
 if not s or s.startswith('#') or '=' not in s: continue
 k,v=s.split('=',1); vals[k.strip()]=v.strip().strip('"').strip("'")
creds=Credentials(token=vals.get('GOOGLE_SHEETS_ACCESS_TOKEN') or None,refresh_token=vals.get('GOOGLE_SHEETS_REFRESH_TOKEN'),token_uri='https://oauth2.googleapis.com/token',client_id=vals.get('GOOGLE_SHEETS_CLIENT_ID'),client_secret=vals.get('GOOGLE_SHEETS_CLIENT_SECRET'))
if not creds.valid: creds.refresh(Request())
svc=build('sheets','v4',credentials=creds)
rows=svc.spreadsheets().values().get(spreadsheetId='16f75U8IZjGkrgNeUyk7haDU-_isrBlmd6glnW0ah5BA',range='Sheet1!A1:H80').execute().get('values',[])
for i,r in enumerate(rows,1):
 print(i,r)
