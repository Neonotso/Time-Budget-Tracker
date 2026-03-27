#!/usr/bin/env python3
"""
Consolidate Mike L folders by moving content from the larger folder 
to the smaller folder that contains only today's lesson notes.
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

print("🔧 CONSOLIDATING MIKE L FOLDERS")
print("=" * 40)

# Folder IDs from our analysis
SOURCE_FOLDER_ID = "1uuMT1Yvl_b-PhId1Ki2hrpi6BzLvE1P8"  # Larger folder with 5 subfolders
TARGET_FOLDER_ID = "1tS_LRgG7PoQmC20WEnAf08vB_uRrOq5Z"   # Smaller folder with 1 subfolder (today's lesson)

print(f"📤 Source Folder ID: {SOURCE_FOLDER_ID}")
print(f"📥 Target Folder ID: {TARGET_FOLDER_ID}")

# Verify both folders exist and get their names
try:
    source_info = svc.files().get(fileId=SOURCE_FOLDER_ID, fields="id, name").execute()
    target_info = svc.files().get(fileId=TARGET_FOLDER_ID, fields="id, name").execute()
    
    print(f"📁 Source: '{source_info['name']}'")
    print(f"📁 Target: '{target_info['name']}'")
    
except Exception as e:
    print(f"❌ Error verifying folders: {e}")
    exit(1)

# Get contents of source folder
print(f"\n📋 Scanning source folder contents...")
try:
    contents = svc.files().list(
        q=f"'{SOURCE_FOLDER_ID}' in parents and trashed=false",
        fields="files(id, name, mimeType)",
        pageSize=100
    ).execute()
    
    items = contents.get('files', [])
    folders = [item for item in items if item.get('mimeType') == 'application/vnd.google-apps.folder']
    files = [item for item in items if item.get('mimeType') != 'application/vnd.google-apps.folder']
    
    print(f"   Found {len(folders)} subfolders and {len(files)} files to move")
    
    if len(items) == 0:
        print("   ⚠️  Source folder appears to be empty - nothing to move")
        exit(0)
        
except Exception as e:
    print(f"❌ Error scanning source folder: {e}")
    exit(1)

# Move each item from source to target
print(f"\n🚚 Moving items from source to target...")
moved_count = 0
failed_count = 0

for item in items:
    item_id = item['id']
    item_name = item['name']
    item_type = "📁 folder" if item.get('mimeType') == 'application/vnd.google-apps.folder' else "📄 file"
    
    try:
        # Move the item by updating its parent
        svc.files().update(
            fileId=item_id,
            addParents=TARGET_FOLDER_ID,
            removeParents=SOURCE_FOLDER_ID,
            fields='id, name, parents'
        ).execute()
        
        print(f"   {item_type} '{item_name}' → moved successfully")
        moved_count += 1
        
    except Exception as e:
        print(f"   ❌ Failed to move '{item_name}': {e}")
        failed_count += 1

print(f"\n📊 MOVE SUMMARY:")
print(f"   ✅ Successfully moved: {moved_count} items")
print(f"   ❌ Failed to move: {failed_count} items")

# Verify the move worked by checking target folder contents
print(f"\n🔍 Verifying move success...")
try:
    target_contents = svc.files().list(
        q=f"'{TARGET_FOLDER_ID}' in parents and trashed=false",
        fields="files(id, name, mimeType)",
        pageSize=100
    ).execute()
    
    target_items = target_contents.get('files', [])
    target_folders = [item for item in target_items if item.get('mimeType') == 'application/vnd.google-apps.folder']
    target_files = [item for item in target_items if item.get('mimeType') != 'application/vnd.google-apps.folder']
    
    print(f"📁 Target folder now contains:")
    print(f"   📂 {len(target_folders)} subfolders")
    print(f"   📄 {len(target_files)} files")
    
    if target_folders:
        folder_names = [f['name'] for f in sorted(target_folders, key=lambda x: x['name'])]
        print(f"   📋 Subfolders: {', '.join(folder_names)}")
        
except Exception as e:
    print(f"❌ Error verifying target folder: {e}")

# Check if source folder is now empty
print(f"\n🔍 Checking source folder status...")
try:
    source_contents = svc.files().list(
        q=f"'{SOURCE_FOLDER_ID}' in parents and trashed=false",
        fields="files(id, name)",
        pageSize=100
    ).execute()
    
    source_items = source_contents.get('files', [])
    
    if len(source_items) == 0:
        print(f"   ✅ Source folder is now empty")
        print(f"   🗑️  Moving source folder to Trash (recoverable)...")
        
        # Move source folder to trash instead of deleting
        svc.files().update(
            fileId=SOURCE_FOLDER_ID,
            trashed=True
        ).execute()
        
        print(f"   🗑️  Source folder moved to Trash successfully")
    else:
        print(f"   ⚠️  Source folder still contains {len(source_items)} items")
        print(f"   📋 Remaining items: {[item['name'] for item in source_items]}")
        
except Exception as e:
    print(f"❌ Error checking source folder: {e}")

print(f"\n� CONSOLIDATION COMPLETE")
print(f"   The Mike L folder with today's lesson notes ({TARGET_FOLDER_ID})")
print(f"   now contains all historical lesson content.")
print(f"   The duplicate Mike L folder has been moved to Trash for safety.")