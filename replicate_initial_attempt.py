#!/usr/bin/env python3
"""
REPLICATE: Let's try to exactly replicate what we did in our very first attempt
to see if we can reproduce the original issue where old folders were missing.
"""

from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Use the EXACT same path as the working scripts
ENV = Path('/Users/ryantaylorvegh/.openclaw/workspace/.secrets/google_sheets & drive.env')

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
    vals = _load_env(ENV)
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

print("🧪 REPLICATING INITIAL ATTEMPT")
print("=" * 40)

# Let's try to exactly replicate what we did in our first script
# In our first attempt, we did a basic search for folders

print("📥 REPLICATING FIRST APPROACH:")
print("   Using: files().list(q='trashed=false and mimeType='application/vnd.google-apps.folder'', fields='files(id,name)')")

results = svc.files().list(
    q="trashed=false and mimeType='application/vnd.google-apps.folder'",
    fields="files(id, name)",
    pageSize=100
).execute()

folders = results.get('files', [])
print(f"📊 Found {len(folders)} folders")

# Let's see what we got
print("\n📋 RESULTS FROM REPLICATED FIRST ATTEMPT:")
folders_sorted = sorted(folders, key=lambda x: x['name'])
for i, folder in enumerate(folders_sorted[:20], 1):
    print(f"   {i:2d}. {folder['name']}")

# Check for specific old folders
print("\n🔍 CHECKING FOR OLD FOLDERS IN REPLICATED ATTEMPT:")
old_folders_to_check = [
    "2026 01 January 09",
    "2026 01 January 15",
    "2026 02 February 03", 
    "2026 03 March 10"
]

for folder_name in old_folders_to_check:
    found = any(f['name'] == folder_name for f in folders)
    status = "✅ FOUND" if found else "❌ MISSING"
    print(f"   {status}: {folder_name}")

print("\n" + "=" * 40)
print("🔍 NOW LET'S TRY THE SECOND APPROACH FROM OUR FIRST INVESTIGATION")
print("=" * 40)

# In our first investigation, we tried the _drive_list_mum.py approach
# Let's replicate that exactly

print("📥 REPLICATING _drive_list_mum.py APPROACH:")
print("   Searching for 'Lessons' folder first, then looking inside")

FOLDER = 'application/vnd.google-apps.folder'

def find_folder(name, parent=None):
    q = ["trashed=false", f"name='{name}'", f"mimeType='{FOLDER}'"]
    if parent: q.append(f"'{parent}' in parents")
    r = svc.files().list(q=' and '.join(q), fields='files(id,name)', pageSize=10).execute().get('files',[])
    return r[0] if r else None

print("   Step 1: Looking for 'Lessons' folder...")
lessons = find_folder('Lessons')
print(f"   Result: Lessons = {lessons}")

if lessons is None:
    print("   🔍 Lessons not found, let's see what's actually in the root by looking at what we can access...")
    
    # Let's see what folders we CAN access by looking at what's in a known student folder's parent
    # We know from earlier that student folders have parent ID: 1VtnKoXBgM2m3Y9RIzW4hHPflDu5dP5-J
    
    # Let's check what's in a student folder to understand the structure
    print("   🔍 Checking structure via known student folder (Caleb):")
    try:
        # Get Caleb folder
        caleb_results = svc.files().list(
            q="name='Caleb' and mimeType='application/vnd.google-apps.folder' and trashed=false",
            fields="files(id, name, parents)",
            pageSize=1
        ).execute()
        
        caleb_folders = caleb_results.get('files', [])
        if caleb_folders:
            caleb_folder = caleb_folders[0]
            print(f"      Caleb folder: {caleb_folder['name']} (ID: {caleb_folder['id']})")
            print(f"      Caleb parents: {caleb_folder.get('parents', [])}")
            
            # The parent ID should be the mysterious one
            if caleb_folder.get('parents'):
                parent_id = caleb_folder['parents'][0]
                print(f"      Parent ID: {parent_id}")
                
                # Now let's see what's in THAT parent folder by looking at its children
                # We can do this by searching for folders that have THIS as their parent
                print(f"      🔍 Looking for folders that have parent ID {parent_id}:")
                children_results = svc.files().list(
                    q=f"'{parent_id}' in parents and trashed=false",
                    fields="files(id, name)",
                    pageSize=100
                ).execute()
                
                children = children_results.get('files', [])
                print(f"      Found {len(children)} folders with this parent:")
                
                # Sort and show them
                children_sorted = sorted(children, key=lambda x: x['name'])
                for i, child in enumerate(children_sorted[:15], 1):
                    print(f"         {i:2d}. {child['name']}")
                
                if len(children_sorted) > 15:
                    print(f"         ... and {len(children_sorted) - 15} more")
                    
                # Check if we see old folders in this list
                old_in_children = [c for c in children if c['name'] in [
                    "2026 01 January 09", "2026 01 January 15", "2026 01 January 16",
                    "2026 02 February 03", "2026 02 February 10"
                ]]
                
                print(f"      📅 Old folders found in parent's children: {len(old_in_children)}")
                for folder in old_in_children:
                    print(f"         - {folder['name']}")
                    
    except Exception as e:
        print(f"      ❌ Error checking Caleb structure: {e}")

else:
    print(f"   🔍 Found Lessons folder: {lessons['name']} (ID: {lessons['id']})")
    print("   Step 2: Looking for contents inside Lessons...")
    try:
        contents = svc.files().list(
            q=f"trashed=false and '{lessons['id']}' in parents",
            fields='files(id,name,mimeType)',
            pageSize=100
        ).execute().get('files', [])
        
        print(f"      Found {len(contents)} items in Lessons folder")
        if contents:
            print("      📋 Contents:")
            for item in sorted(contents, key=lambda x: x['name'])[:10]:
                type_icon = "📁" if item['mimeType'] == 'application/vnd.google-apps.folder' else "📄"
                print(f"         {type_icon} {item['name']}")
        else:
            print("      📂 Lessons folder appears to be empty")
            
    except Exception as e:
        print(f"      ❌ Error listing Lessons contents: {e}")

print("\n" + "=" * 50)
print("🏁 REPLICATION COMPLETE")
print("=" * 50)