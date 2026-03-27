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

# Check what's inside the Caleb folder
student_folder_name = "Caleb"
results = svc.files().list(
    q=f"name='{student_folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
    pageSize=1,
    fields="files(id, name)"
).execute()

items = results.get('files', [])

if not items:
    print(f"No folder named '{student_folder_name}' found.")
else:
    folder = items[0]
    print(f"Folder: {folder['name']} (ID: {folder['id']})")
    
    # List contents
    contents = svc.files().list(
        q=f"'{folder['id']}' in parents and trashed=false",
        pageSize=50,
        fields="files(id, name, mimeType, createdTime)"
    ).execute()
    
    subitems = contents.get('files', [])
    print(f"Contents of {folder['name']}:")
    if not subitems:
        print("  (empty)")
    else:
        for subitem in sorted(subitems, key=lambda x: x['name']):
            type_label = "📁 Folder" if subitem['mimeType'] == 'application/vnd.google-apps.folder' else "📄 File"
            print(f"  {type_label}: {subitem['name']}")