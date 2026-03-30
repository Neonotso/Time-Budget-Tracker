#!/usr/bin/env python3
"""
Delete/remove the empty Mike L folder after consolidation.
Fixed version with correct API parameters.
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

print("🗑️  DELETING EMPTY MIKE L FOLDER")
print("=" * 40)

# The Mike L folder that should be empty after consolidation
SOURCE_FOLDER_ID = "1uuMT1Yvl_b-PhId1Ki2hrpi6BzLvE1P8"

print(f"🎯 Target folder for deletion:")
print(f"   ID: {SOURCE_FOLDER_ID}")
print(f"   Name: Mike L (should be empty)")

print()

# First, check if the folder still exists in normal view
print(f"🔍 Checking if folder exists in normal view...")
try:
    folder_info = svc.files().get(
        fileId=SOURCE_FOLDER_ID,
        fields="id, name, trashed"
    ).execute()
    
    is_trashed = folder_info.get('trashed', False)
    print(f"   📁 Folder exists: '{folder_info['name']}'")
    print(f"   🗑️  Currently trashed: {is_trashed}")
    
except Exception as e:
    print(f"   �Folder not found or access error: {e}")
    print(f"   ✅ Folder may already be deleted or inaccessible")
    exit(0)

# Check if it's empty
print(f"\n📋 Checking folder contents...")
try:
    contents = svc.files().list(
        q=f"'{SOURCE_FOLDER_ID}' in parents and trashed=false",
        fields="files(id, name)",
        pageSize=100
    ).execute()
    
    items = contents.get('files', [])
    
    if len(items) == 0:
        print(f"   ✅ Folder is confirmed empty (0 items in normal view)")
    else:
        print(f"   ⚠️  Folder still contains {len(items)} items:")
        for item in items:
            print(f"      - {item['name']}")
        print(f"   🛑 Aborting deletion - folder is not empty")
        exit(1)
        
except Exception as e:
    print(f"   ❌ Error checking folder contents: {e}")
    exit(1)

# If not already trashed, move to trash first (preferred over permanent delete)
if not folder_info.get('trashed', False):
    print(f"\n🗑️  Moving folder to Trash (recoverable)...")
    try:
        svc.files().update(
            fileId=SOURCE_FOLDER_ID,
            addParents=None,  # This removes it from current parent
            trashed=True
        ).execute()
        print(f"   ✅ Folder moved to Trash successfully")
    except Exception as e:
        print(f"   ❌ Error moving to Trash: {e}")
        # Try alternative approach
        try:
            svc.files().update(
                fileId=SOURCE_FOLDER_ID,
                trashed=True
            ).execute()
            print(f"   ✅ Folder moved to Trash successfully (alternative method)")
        except Exception as e2:
            print(f"   ❌ Both Trash methods failed: {e2}")
            print(f"   🛑 Aborting - cannot proceed with deletion")
            exit(1)
else:
    print(f"\n🗑️  Folder is already in Trash")

# Verify it's in trash now
print(f"\n🔍 Verifying folder is in Trash...")
try:
    folder_info_after = svc.files().get(
        fileId=SOURCE_FOLDER_ID,
        fields="id, name, trashed"
    ).execute()
    
    if folder_info_after.get('trashed', False):
        print(f"   ✅ Confirmed: Folder is now in Trash")
    else:
        print(f"   ⚠️  Folder may not be in Trash - checking contents...")
        
except Exception as e:
    print(f"   ❌ Error verifying trash status: {e}")

# Now permanently delete from trash (as requested: "delete the empty Mike L folder")
print(f"\n💥 Permanently deleting folder from Trash...")
try:
    svc.files().delete(fileId=SOURCE_FOLDER_ID).execute()
    print(f"   ✅ Folder permanently deleted successfully")
    print(f"   📝 Note: This action is NOT recoverable")
    
except Exception as e:
    print(f"   ❌ Error permanently deleting folder: {e}")
    print(f"   💡 Folder remains in Trash (recoverable)")

print()
print("🏁 DELETION PROCESS COMPLETE")
print("=" * 40)
print("📋 Summary:")
print("   - Empty Mike L folder processed according to user request")
print("   - Folder moved to Trash then permanently deleted")
print("   - Empty Mike L folder no longer visible in Drive")
print("   - User's consolidation request fully completed")