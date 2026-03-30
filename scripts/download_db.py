from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import gzip
from pathlib import Path

WORKSPACE = Path("/Users/ryantaylorvegh/.openclaw/workspace")
GOOGLE_ENV = WORKSPACE / ".secrets" / "google_sheets & drive.env"

def _load_env(path: Path) -> dict[str, str]:
    vals = {}
    for raw in path.read_text().splitlines():
        s = raw.strip()
        if not s or s.startswith("#") or "=" not in s: continue
        k, v = s.split("=", 1)
        vals[k.strip()] = v.strip().strip('"').strip("'")
    return vals

vals = _load_env(GOOGLE_ENV)
creds = Credentials(
    token=vals.get("GOOGLE_SHEETS_ACCESS_TOKEN"),
    refresh_token=vals.get("GOOGLE_SHEETS_REFRESH_TOKEN"),
    token_uri="https://oauth2.googleapis.com/token",
    client_id=vals.get("GOOGLE_SHEETS_CLIENT_ID"),
    client_secret=vals.get("GOOGLE_SHEETS_CLIENT_SECRET"),
)
svc = build("drive", "v3", credentials=creds)

file_id = '1HjQbISDShR9k0vX5RehVPZV5SwKraVtc'
request = svc.files().get_media(fileId=file_id)
fh = io.BytesIO()
downloader = MediaIoBaseDownload(fh, request)
done = False
while done is False:
    status, done = downloader.next_chunk()

fh.seek(0)
with gzip.GzipFile(fileobj=fh) as gz:
    with open(WORKSPACE / "backup_2026-03-13_v4.db", "wb") as f:
        f.write(gz.read())
print("Downloaded and decompressed to backup_2026-03-13_v4.db")
