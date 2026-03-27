from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import re

TZ=ZoneInfo('America/Detroit')
ENV=Path('/Users/ryantaylorvegh/.openclaw/workspace/.secrets/google_sheets & drive.env')
SHEET_ID='16f75U8IZjGkrgNeUyk7haDU-_isrBlmd6glnW0ah5BA'
SHEET_NAME='Sheet1'
vals={}
for raw in ENV.read_text().splitlines():
 s=raw.strip()
 if not s or s.startswith('#') or '=' not in s: continue
 k,v=s.split('=',1); vals[k.strip()]=v.strip().strip('"').strip("'")
creds=Credentials(token=vals.get('GOOGLE_SHEETS_ACCESS_TOKEN') or None,refresh_token=vals.get('GOOGLE_SHEETS_REFRESH_TOKEN'),token_uri='https://oauth2.googleapis.com/token',client_id=vals.get('GOOGLE_SHEETS_CLIENT_ID'),client_secret=vals.get('GOOGLE_SHEETS_CLIENT_SECRET'))
if not creds.valid: creds.refresh(Request())
svc=build('sheets','v4',credentials=creds)
rows=svc.spreadsheets().values().get(spreadsheetId=SHEET_ID,range=f'{SHEET_NAME}!A1:D200').execute().get('values',[])
now=datetime.now(TZ)
print('NOW',now.isoformat())

month_lookup={'jan':1,'january':1,'feb':2,'february':2,'mar':3,'march':3,'apr':4,'april':4,'may':5,'jun':6,'june':6,'jul':7,'july':7,'aug':8,'august':8,'sep':9,'sept':9,'september':9,'oct':10,'october':10,'nov':11,'november':11,'dec':12,'december':12}

def parse_date(section):
 if not section: return None
 left=section.split(' - ')[0].strip()
 m=re.match(r'^([A-Za-z]+)\s+(\d{1,2})$',left)
 if not m: return None
 mo=month_lookup.get(m.group(1).lower()); day=int(m.group(2))
 if not mo: return None
 dt=datetime(now.year,mo,day,tzinfo=TZ)
 if dt < now - timedelta(days=45): dt=datetime(now.year+1,mo,day,tzinfo=TZ)
 return dt

def parse_time(label):
 s=label.strip().upper()
 if s=='NOON': return (12,0)
 m=re.match(r'^(\d{1,2}):(\d{2})\s*(AM|PM)$',s)
 if not m: return None
 hh=int(m.group(1)); mm=int(m.group(2)); ap=m.group(3)
 if hh==12: hh=0
 if ap=='PM': hh+=12
 return (hh,mm)

section=''
for i,row in enumerate(rows,1):
 a=(row[0] if len(row)>0 else '').strip(); b=(row[1] if len(row)>1 else '').strip(); c=(row[2] if len(row)>2 else '').strip(); d=(row[3] if len(row)>3 else '').strip()
 if not a: continue
 if (' - ' in a) and ('First Name' in b):
  section=a; continue
 if not (b or c or d): continue
 ddate=parse_date(section); tt=parse_time(a)
 if not ddate or not tt: continue
 reading=ddate.replace(hour=tt[0],minute=tt[1])
 primary=((reading-timedelta(days=1)).replace(hour=18,minute=0,second=0,microsecond=0) if reading.hour<12 else reading.replace(hour=9,minute=0,second=0,microsecond=0))
 final=reading-timedelta(hours=1)
 print(i, section,'|',a,b,c,d,'| reading',reading.isoformat(),'| primary',primary.isoformat(),'| final',final.isoformat(),'| duePrimary',primary<=now<=primary+timedelta(minutes=20),'| dueFinal',final<=now<=final+timedelta(minutes=20))
