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

FOLDER='application/vnd.google-apps.folder'

def find_folder(name,parent=None):
    q=["trashed=false", f"name='{name}'", f"mimeType='{FOLDER}'"]
    if parent: q.append(f"'{parent}' in parents")
    print(f"Searching for: {name}" + (f" in parent {parent}" if parent else ""))
    print(f"Query: {' and '.join(q)}")
    r=svc.files().list(q=' and '.join(q),fields='files(id,name)',pageSize=10).execute().get('files',[])
    print(f"Found {len(r)} results")
    for item in r:
        print(f"  - {item['name']} (ID: {item['id']})")
    return r[0] if r else None

# First, let's see what's in the root
print("=== Checking root folder ===")
results = svc.files().list(
    q="trashed=false",
    pageSize=20,
    fields="files(id, name, mimeType)"
).execute()

items = results.get('files', [])

folders = [item for item in items if item['mimeType'] == 'application/vnd.google-apps.folder']
print(f"Found {len(folders)} folders in root:")
for folder in folders:
    print(f"  - {folder['name']} (ID: {folder['id']})")

print("\n=== Searching for Lessons ===")
lessons=find_folder('Lessons')
print(f"Lessons result: {lessons}")

print("\n=== Searching for Mum ===")
mum=find_folder('Mum')
print(f"Mum result: {mum}")

# Try variations
print("\n=== Trying variations ===")
variations = ['lessons', 'LESSONS', 'Lesson', 'lesson']
for var in variations:
    result = find_folder(var)
    print(f"'{var}': {result}")

print("\n=== Searching for Mum in potential Lessons folder ===")
if lessons:
    mum_in_lessons = find_folder('Mum', lessons['id'])
    print(f"Mum in Lessons: {mum_in_lessons}")
else:
    print("No Lessons folder found to search in")