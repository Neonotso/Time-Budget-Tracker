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
folder_name = "WorkingHours"
q = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and trashed=false"
resp = svc.files().list(q=q, fields="files(id,name)", pageSize=1).execute()
files = resp.get("files", [])

if not files:
    print(f"Folder '{folder_name}' not found.")
else:
    f_id = files[0]["id"]
    print(f"Found folder '{folder_name}' (ID: {f_id})")
    q = f"'{f_id}' in parents and trashed=false"
    items = svc.files().list(q=q, fields="files(id,name,mimeType)", pageSize=100).execute().get("files", [])
    for it in items:
        print(f"- {it['name']} (ID: {it['id']})")
