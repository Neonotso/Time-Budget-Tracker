from pathlib import Path
from datetime import datetime
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

ENV = Path('/Users/ryantaylorvegh/.openclaw/workspace/.secrets/google_sheets & drive.env')
vals = {}
for line in ENV.read_text().splitlines():
    s=line.strip()
    if not s or s.startswith('#') or '=' not in s: continue
    k,v=s.split('=',1)
    vals[k.strip()] = v.strip().strip('"').strip("'")

creds = Credentials(
    token=vals.get('GOOGLE_SHEETS_ACCESS_TOKEN') or None,
    refresh_token=vals.get('GOOGLE_SHEETS_REFRESH_TOKEN'),
    token_uri='https://oauth2.googleapis.com/token',
    client_id=vals.get('GOOGLE_SHEETS_CLIENT_ID'),
    client_secret=vals.get('GOOGLE_SHEETS_CLIENT_SECRET'),
)
if not creds.valid:
    creds.refresh(Request())
svc = build('drive','v3',credentials=creds)

def q(name,parent=None,folder=False):
    cond=["trashed=false", f"name='{name}'"]
    if folder: cond.append("mimeType='application/vnd.google-apps.folder'")
    if parent: cond.append(f"'{parent}' in parents")
    return ' and '.join(cond)

lessons = svc.files().list(q=q('Lessons',folder=True),fields='files(id,name)').execute().get('files',[])
print('Lessons',lessons)
if not lessons: raise SystemExit(1)
lessons_id=lessons[0]['id']
eric = svc.files().list(q=q('Eric V',lessons_id,folder=True),fields='files(id,name)').execute().get('files',[])
if not eric:
    eric = svc.files().list(q=q('Eric',lessons_id,folder=True),fields='files(id,name)').execute().get('files',[])
print('EricFolder',eric)
if not eric: raise SystemExit(2)
eric_id=eric[0]['id']
children = svc.files().list(q=f"trashed=false and '{eric_id}' in parents",fields='files(id,name,mimeType,createdTime)',pageSize=200).execute().get('files',[])
print('Children:')
for f in sorted(children,key=lambda x:x['name']):
    print(f"- {f['name']} | {f['mimeType']} | {f['id']}")
    if f['mimeType']=='application/vnd.google-apps.folder':
        sub = svc.files().list(q=f"trashed=false and '{f['id']}' in parents",fields='files(id,name,mimeType)',pageSize=200).execute().get('files',[])
        for s in sorted(sub,key=lambda x:x['name']):
            print(f"    - {s['name']} | {s['mimeType']} | {s['id']}")
