from pathlib import Path
from datetime import datetime
import re
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
    r=svc.files().list(q=' and '.join(q),fields='files(id,name)',pageSize=20).execute().get('files',[])
    return r[0] if r else None

def ensure_folder(name,parent):
    f=find_folder(name,parent)
    if f: return f['id']
    return svc.files().create(body={'name':name,'mimeType':FOLDER,'parents':[parent]},fields='id').execute()['id']

lessons=find_folder('Lessons')
mum=find_folder('Mum', lessons['id']) if lessons else None
if not mum: raise SystemExit('Mum folder not found')
mum_id=mum['id']
items=svc.files().list(q=f"trashed=false and '{mum_id}' in parents",fields='files(id,name,mimeType)',pageSize=300).execute().get('files',[])

png_by_page={}
audio_by_date=[]
for it in items:
    n=it['name']
    nl=n.lower()
    if nl.endswith('.png'):
        m=re.search(r'page\s*(\d+)', nl)
        if m:
            page=int(m.group(1))
            png_by_page.setdefault(page,[]).append(it)
    if any(nl.endswith(ext) for ext in ('.m4a','.mp3','.wav','.aiff')):
        m=re.search(r'(\d{2})-(\d{2})-(\d{2})', n)
        if m:
            mm,dd,yy=m.groups()
            dt=datetime.strptime(f"20{yy}-{mm}-{dd}",'%Y-%m-%d')
            audio_by_date.append((dt,it))

audio_by_date.sort(key=lambda x:x[0])
if len(audio_by_date) < 4:
    raise SystemExit(f'Expected 4 audio files, found {len(audio_by_date)}')

moves=[]
for idx,(dt,audio) in enumerate(audio_by_date[:4], start=1):
    folder_name=dt.strftime('%Y %m %B %d')
    folder_id=ensure_folder(folder_name, mum_id)
    # move 2 note pages labeled with this page index
    for png in sorted(png_by_page.get(idx,[]), key=lambda x:x['name']):
        svc.files().update(fileId=png['id'], addParents=folder_id, removeParents=mum_id, fields='id').execute()
        moves.append(f"Moved {png['name']} -> {folder_name}")
    svc.files().update(fileId=audio['id'], addParents=folder_id, removeParents=mum_id, fields='id').execute()
    moves.append(f"Moved {audio['name']} -> {folder_name}")

print('\n'.join(moves))
