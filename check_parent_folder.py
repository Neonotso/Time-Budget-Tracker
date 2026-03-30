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

# Check the parent of a date folder
folder_name = "2026 03 March 24"
results = svc.files().list(
    q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
    pageSize=1,
    fields="files(id, name, parents)"
).execute()

items = results.get('files', [])

if not items:
    print(f"No folder named '{folder_name}' found.")
else:
    folder = items[0]
    print(f"Folder: {folder['name']} (ID: {folder['id']})")
    parents = folder.get('parents', [])
    print(f"Parent IDs: {parents}")
    
    if parents:
        parent_id = parents[0]
        print(f"\nGetting info for parent ID: {parent_id}")
        try:
            parent_info = svc.files().get(fileId=parent_id, fields="id, name, mimeType, parents").execute()
            print(f"Parent folder: {parent_info['name']} (ID: {parent_info['id']})")
            print(f"Parent mimeType: {parent_info['mimeType']}")
            
            # Check if parent has parents (to see if we're getting closer to root)
            parent_parents = parent_info.get('parents', [])
            if parent_parents:
                print(f"Parent has {len(parent_parents)} parent(s): {parent_parents}")
                # Get the grandparent
                grandparent_id = parent_parents[0]
                print(f"\nGetting info for grandparent ID: {grandparent_id}")
                grandparent_info = svc.files().get(fileId=grandparent_id, fields="id, name, mimeType").execute()
                print(f"Grandparent folder: {grandparent_info['name']} (ID: {grandparent_info['id']})")
                print(f"Grandparent mimeType: {grandparent_info['mimeType']}")
            else:
                print("Parent is in root (no grandparents)")
        except Exception as e:
            print(f"Error getting parent info: {e}")
    else:
        print("Folder is in root (no parents)")

print("\n" + "="*50)
print("NOW LET'S CHECK WHAT'S IN THE PARENT FOLDER")
print("="*50)

# Now let's see what's actually in the parent folder
if items and folder.get('parents'):
    parent_id = folder['parents'][0]
    print(f"Listing contents of parent folder (ID: {parent_id}):")
    
    contents = svc.files().list(
        q=f"'{parent_id}' in parents and trashed=false",
        pageSize=50,
        fields="files(id, name, mimeType)"
    ).execute()
    
    subitems = contents.get('files', [])
    print(f"Found {len(subitems)} items in parent folder:")
    
    folders_in_parent = [item for item in subitems if item['mimeType'] == 'application/vnd.google-apps.folder']
    files_in_parent = [item for item in subitems if item['mimeType'] != 'application/vnd.google-apps.folder']
    
    print(f"\n📁 Folders in parent ({len(folders_in_parent)}):")
    for folder_item in sorted(folders_in_parent, key=lambda x: x['name']):
        print(f"  - {folder_item['name']}")
    
    print(f"\n📄 Files in parent ({len(files_in_parent)}):")
    for file_item in sorted(files_in_parent, key=lambda x: x['name']):
        print(f"  - {file_item['name']}")