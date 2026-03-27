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

# Test the exact folder ID from the script
LESSONS_ROOT_FOLDER_ID = "1VtnKoXBgM2m3Y9RIzW4hHPflDu5dP5-J"

print(f"Testing access to Lessons folder ID: {LESSONS_ROOT_FOLDER_ID}")
print("=" * 60)

try:
    folder_info = svc.files().get(fileId=LESSONS_ROOT_FOLDER_ID, fields="id, name, mimeType, parents").execute()
    print(f"✅ SUCCESS: Found folder!")
    print(f"   Name: {folder_info['name']}")
    print(f"   ID: {folder_info['id']}")
    print(f"   Type: {folder_info['mimeType']}")
    print(f"   Parents: {folder_info.get('parents', 'None')}")
    
    # Now try to list what's inside this folder
    print(f"\n📂 Listing contents of Lessons folder:")
    contents = svc.files().list(
        q=f"'{LESSONS_ROOT_FOLDER_ID}' in parents and trashed=false",
        pageSize=100,
        fields="files(id, name, mimeType)"
    ).execute()
    
    items = contents.get('files', [])
    print(f"   Found {len(items)} items inside Lessons folder:")
    
    folders = [item for item in items if item['mimeType'] == 'application/vnd.google-apps.folder']
    files = [item for item in items if item['mimeType'] != 'application/vnd.google-apps.folder']
    
    print(f"   📁 Folders ({len(folders)}):")
    for folder in sorted(folders, key=lambda x: x['name']):
        print(f"     - {folder['name']}")
    
    print(f"   📄 Files ({len(files)}):")
    for file_item in sorted(files, key=lambda x: x['name']):
        print(f"     - {file_item['name']}")
        
except Exception as e:
    print(f"❌ ERROR: {e}")
    print(f"   This confirms the folder is not accessible with current credentials.")
    
    print(f"\n🔍 Let's see what we CAN access by checking the known student folders:")
    # Check if we can at least see what's in the student folders we know about
    known_students = ["Mike L", "Caleb", "Tiffany"]
    
    for student_name in known_students:
        print(f"\n   Checking {student_name} folder:")
        try:
            results = svc.files().list(
                q=f"name='{student_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
                pageSize=1,
                fields="files(id, name, parents)"
            ).execute()
            
            student_items = results.get('files', [])
            if student_items:
                student_folder = student_items[0]
                print(f"     ✅ Found: {student_folder['name']} (ID: {student_folder['id']})")
                
                # Check what's inside this student folder
                contents = svc.files().list(
                    q=f"'{student_folder['id']}' in parents and trashed=false",
                    pageSize=20,
                    fields="files(id, name, mimeType)"
                ).execute()
                
                subitems = contents.get('files', [])
                subfolders = [item for item in subitems if item['mimeType'] == 'application/vnd.google-apps.folder']
                files = [item for item in subitems if item['mimeType'] != 'application/vnd.google-apps.folder']
                
                print(f"     📁 Contains {len(subfolders)} folders and {len(files)} files")
                if subfolders:
                    # Show first few date folders
                    date_folders = [f for f in subfolders if re.match(r'\d{4} \d{2} [A-Z][a-z]+ \d{2}', f['name'])]
                    print(f"     📅 Date folders (showing first 5): {sorted([f['name'] for f in date_folders])[:5]}")
                    
            else:
                print(f"     ❌ {student_name} folder not found")
                
        except Exception as e2:
            print(f"     ❌ Error checking {student_name}: {e2}")

# Import regex for the date matching
import re