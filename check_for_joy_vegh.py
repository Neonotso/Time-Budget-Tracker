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

# Search for folders that might be related to Joy Vegh
search_terms = ['Joy', 'Vegh', 'joy', 'vegh', 'MUM', 'mum']

for term in search_terms:
    results = svc.files().list(
        q=f"name contains '{term}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
        pageSize=10,
        fields="files(id, name)"
    ).execute()
    
    items = results.get('files', [])
    
    if items:
        print(f"Found {len(items)} folder(s) containing '{term}':")
        for folder in items:
            print(f"- {folder['name']} (ID: {folder['id']})")
    else:
        print(f"No folders found containing '{term}'")