from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

WORKSPACE = Path("/Users/ryantaylorvegh/.openclaw/workspace")
GOOGLE_ENV = WORKSPACE / ".secrets" / "google_sheets & drive.env"

def _load_env(path: Path) -> dict[str, str]:
    vals: dict[str, str] = {}
    if not path.exists():
        return vals
    for raw in path.read_text().splitlines():
        s = raw.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        vals[k.strip()] = v.strip().strip('"').strip("'")
    return vals

def drive_service():
    vals = _load_env(GOOGLE_ENV)
    creds = Credentials(
        token=vals.get("GOOGLE_SHEETS_ACCESS_TOKEN") or None,
        refresh_token=vals.get("GOOGLE_SHEETS_REFRESH_TOKEN"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=vals.get("GOOGLE_SHEETS_CLIENT_ID"),
        client_secret=vals.get("GOOGLE_SHEETS_CLIENT_SECRET"),
    )
    if not creds.valid:
        creds.refresh(Request())
    return build("drive", "v3", credentials=creds)

svc = drive_service()

# Search for folder named Lessons anywhere
results = svc.files().list(
    q="mimeType='application/vnd.google-apps.folder' and name='Lessons' and trashed=false",
    pageSize=10,
    fields="files(id, name)"
).execute()

items = results.get('files', [])

if not items:
    print('No folder named "Lessons" found.')
else:
    print(f'Found {len(items)} folder(s) named "Lessons":')
    for item in items:
        print(f"- {item['name']} (ID: {item['id']})")
        
        # Now list contents of this Lessons folder
        contents = svc.files().list(
            q=f"'{item['id']}' in parents and trashed=false",
            pageSize=50,
            fields="files(id, name, mimeType)"
        ).execute()
        
        subitems = contents.get('files', [])
        if not subitems:
            print(f"  (No contents in {item['name']} folder)")
        else:
            print(f"  Contents of {item['name']}:")
            for subitem in subitems:
                type_label = "📁 Folder" if subitem['mimeType'] == 'application/vnd.google-apps.folder' else "📄 File"
                print(f"  {type_label}: {subitem['name']}")