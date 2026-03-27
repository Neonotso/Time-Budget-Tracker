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

print("=== EXPLORING THE ACTUAL FOLDER STRUCTURE ===\n")

# Let's check what's in the root by looking for folders with no accessible parents
# or by checking the "My Drive" equivalent

# First, let's see what happens if we try to list files with no parent constraint
print("1. Checking for folders that might be at the top level:")
results = svc.files().list(
    q="trashed=false",
    pageSize=50,
    fields="files(id, name, mimeType, parents)"
).execute()

items = results.get('files', [])

# Group items by whether they have parents
items_with_parents = []
items_without_parents = []

for item in items:
    if item.get('parents'):
        items_with_parents.append(item)
    else:
        items_without_parents.append(item)

print(f"   Items with parents: {len(items_with_parents)}")
print(f"   Items without parents: {len(items_without_parents)}")

if items_without_parents:
    print("\n   Items without parents (potential top-level):")
    for item in items_without_parents:
        print(f"     - {item['name']} ({item['mimeType']})")

# Let's also try to look for shared drives
print("\n2. Checking for shared drives:")
try:
    drives = svc.drives().list(pageSize=10).execute()
    drive_items = drives.get('drives', [])
    if drive_items:
        print(f"   Found {len(drive_items)} shared drives:")
        for drive in drive_items:
            print(f"     - {drive['name']} (ID: {drive['id']})")
    else:
        print("   No shared drives found.")
except Exception as e:
    print(f"   Error checking shared drives: {e}")

# Let's check the specific folder structure mentioned in USER.md for Lessons
print("\n3. Searching for 'Lessons' folder anywhere:")
results = svc.files().list(
    q="name='Lessons' and mimeType='application/vnd.google-apps.folder' and trashed=false",
    pageSize=10,
    fields="files(id, name, parents)"
).execute()

lessons_items = results.get('files', [])
print(f"   Found {len(lessons_items)} folders named 'Lessons':")
for item in lessons_items:
    print(f"     - {item['name']} (ID: {item['id']})")
    if item.get('parents'):
        print(f"       Parents: {item['parents']}")

print("\n4. Let's try a different approach - let's see what's accessible by looking at recent files:")
results = svc.files().list(
    q="trashed=false",
    orderBy="modifiedTime desc",
    pageSize=20,
    fields="files(id, name, mimeType, parents)"
).execute()

recent_items = results.get('files', [])
print(f"   Most recently modified items:")
for item in recent_items[:10]:
    indent = "  " * len(item.get('parents', [])) if item.get('parents') else ""
    print(f"     {indent}- {item['name']} ({item['mimeType']})")

print("\n5. Finally, let's check if we can find the actual root by going up from a known folder:")
# Start from Mike L and go up as far as we can
current_folder_name = "Mike L"
current_results = svc.files().list(
    q=f"name='{current_folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
    pageSize=1,
    fields="files(id, name, parents)"
).execute()

current_items = current_results.get('files', [])
if current_items:
    current_folder = current_items[0]
    print(f"   Starting from: {current_folder['name']} (ID: {current_folder['id']})")
    
    path_parts = [current_folder['name']]
    current_id = current_folder['id']
    
    # Go up the chain
    for i in range(5):  # Go up max 5 levels
        parents = current_folder.get('parents', [])
        if not parents:
            print(f"     Reached top level after {i} steps")
            break
            
        parent_id = parents[0]
        try:
            parent_folder = svc.files().get(fileId=parent_id, fields="id, name, mimeType, parents").execute()
            print(f"     Level {i+1}: {parent_folder['name']} (ID: {parent_folder['id']})")
            path_parts.insert(0, parent_folder['name'])
            current_folder = parent_folder
            
            # Check if this parent has parents
            if not parent_folder.get('parents'):
                print(f"       This appears to be the top-level folder")
                break
        except Exception as e:
            print(f"     Error getting parent {i+1}: {e}")
            break
    
    print(f"   Constructed path: {' / '.join(path_parts)}")
else:
    print(f"   Could not find folder '{current_folder_name}'")
