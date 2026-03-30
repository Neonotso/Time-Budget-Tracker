from pathlib import Path
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

def find_folder(name):
    q=["trashed=false", f"name='{name}'", f"mimeType='{FOLDER}'"]
    r=svc.files().list(q=' and '.join(q),fields='files(id,name)',pageSize=10).execute().get('files',[])
    return r[0] if r else None

folder = find_folder('WorkingHours')
if folder:
    print(f"Found folder: {folder['name']} ({folder['id']})")
    items=svc.files().list(q=f"trashed=false and '{folder['id']}' in parents",fields='files(id,name,mimeType)',pageSize=300).execute().get('files',[])
    for it in sorted(items,key=lambda x:x['name']):
        print(f"- {it['name']} ({it['id']})")
else:
    print("Could not find 'WorkingHours' folder.")
