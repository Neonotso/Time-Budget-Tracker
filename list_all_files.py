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

# Try to get more information about the connected account
try:
    about = svc.about().get(fields="user,storageQuota").execute()
    print(f"Connected as: {about.get('user', {}).get('displayName', 'Unknown')} ({about.get('user', {}).get('emailAddress', 'No email')})")
except Exception as e:
    print(f"Could not get account info: {e}")

print("\n=== Listing ALL files (first 30) ===")
results = svc.files().list(
    pageSize=30,
    fields="files(id, name, mimeType, parents, trashed)"
).execute()

items = results.get('files', [])

if not items:
    print('No files found.')
else:
    print(f"Found {len(items)} items:")
    folders = []
    files = []
    for item in items:
        if item.get('trashed', False):
            continue
        if item['mimeType'] == 'application/vnd.google-apps.folder':
            folders.append(item)
        else:
            files.append(item)
    
    print(f"\n📁 Folders ({len(folders)}):")
    for folder in sorted(folders, key=lambda x: x['name']):
        parents = folder.get('parents', [])
        parent_info = f" (in root)" if not parents else f" (has {len(parents)} parent(s))"
        print(f"  - {folder['name']}{parent_info}")
    
    print(f"\n📄 Files ({len(files)}):")
    for file_item in sorted(files, key=lambda x: x['name'])[:10]:  # Show first 10 files
        print(f"  - {file_item['name']} ({file_item['mimeType']})")
    if len(files) > 10:
        print(f"  ... and {len(files) - 10} more files")