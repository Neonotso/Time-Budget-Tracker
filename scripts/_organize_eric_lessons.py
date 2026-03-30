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

FOLDER='application/vnd.google-apps.folder'

def find_folder(name,parent=None):
    q=["trashed=false", f"name='{name}'", f"mimeType='{FOLDER}'"]
    if parent: q.append(f"'{parent}' in parents")
    r=svc.files().list(q=' and '.join(q),fields='files(id,name)',pageSize=10).execute().get('files',[])
    return r[0] if r else None

def ensure_folder(name,parent):
    f=find_folder(name,parent)
    if f: return f['id']
    return svc.files().create(body={'name':name,'mimeType':FOLDER,'parents':[parent]},fields='id').execute()['id']

lessons=find_folder('Lessons')
eric=find_folder('Eric V',lessons['id']) if lessons else None
if not eric: raise SystemExit('Eric folder not found')
eric_id=eric['id']
items=svc.files().list(q=f"trashed=false and '{eric_id}' in parents",fields='files(id,name,mimeType)',pageSize=200).execute().get('files',[])

png_by_page={}
audio_by_date={}
for it in items:
    n=it['name']
    nl=n.lower()
    if nl.endswith('.png') and 'page ' in nl:
        try:
            p=int(nl.split('page ')[1].split('.')[0])
            png_by_page[p]=it
        except Exception:
            pass
    if any(nl.endswith(ext) for ext in ('.m4a','.mp3','.wav','.aiff')):
        # Eric — 01-15-26.m4a
        import re
        m=re.search(r'(\d{2})-(\d{2})-(\d{2})', n)
        if m:
            mm,dd,yy=m.groups()
            dt=datetime.strptime(f"20{yy}-{mm}-{dd}",'%Y-%m-%d')
            audio_by_date[dt]=it

sorted_dates=sorted(audio_by_date.keys())
pages=[1,2,3]
if len(sorted_dates)<3:
    raise SystemExit(f'Need 3 audio dates, found {len(sorted_dates)}')

moves=[]
for page,dt in zip(pages,sorted_dates):
    folder_name=dt.strftime('%Y %m %B %d')
    folder_id=ensure_folder(folder_name, eric_id)
    png=png_by_page.get(page)
    aud=audio_by_date.get(dt)
    if png:
        svc.files().update(fileId=png['id'], addParents=folder_id, removeParents=eric_id, fields='id').execute()
        moves.append(f"Moved {png['name']} -> {folder_name}")
    if aud:
        svc.files().update(fileId=aud['id'], addParents=folder_id, removeParents=eric_id, fields='id').execute()
        moves.append(f"Moved {aud['name']} -> {folder_name}")

print('\n'.join(moves))
