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

# Find the Lessons folder
lessons_q = "mimeType='application/vnd.google-apps.folder' and name='Lessons' and trashed=false"
lessons_resp = svc.files().list(q=lessons_q, fields="files(id,name)", pageSize=1).execute()
lessons_files = lessons_resp.get("files", [])

if not lessons_files:
    print("Lessons folder not found.")
else:
    lessons_id = lessons_files[0]["id"]
    print(f"Found Lessons folder (ID: {lessons_id})")
    
    # List all folders inside Lessons
    folders_q = f"mimeType='application/vnd.google-apps.folder' and '{lessons_id}' in parents and trashed=false"
    folders_resp = svc.files().list(q=folders_q, fields="files(id,name)", pageSize=100).execute()
    folders = folders_resp.get("files", [])
    
    if not folders:
        print("No folders found inside Lessons.")
    else:
        print(f"Found {len(folders)} folders in Lessons:")
        for folder in sorted(folders, key=lambda x: x['name']):
            print(f"- {folder['name']} (ID: {folder['id']})")