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

# Search for Mum folder anywhere
results = svc.files().list(
    q="name='Mum' and mimeType='application/vnd.google-apps.folder' and trashed=false",
    pageSize=10,
    fields="files(id, name, parents)"
).execute()

items = results.get('files', [])

if not items:
    print("No folder named 'Mum' found.")
else:
    print(f"Found {len(items)} folder(s) named 'Mum':")
    for folder in items:
        print(f"- {folder['name']} (ID: {folder['id']})")
        parents = folder.get('parents', [])
        if parents:
            print(f"  Parent IDs: {parents}")
            # Get parent info
            for parent_id in parents:
                try:
                    parent_info = svc.files().get(fileId=parent_id, fields="id, name").execute()
                    print(f"  Parent folder: {parent_info['name']} (ID: {parent_info['id']})")
                except Exception as e:
                    print(f"  Could not get parent info: {e}")
        else:
            print("  (in root)")