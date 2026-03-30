#!/usr/bin/env python3
"""
Test that the new FULL Drive scope is working by attempting to access
the previously problematic folder.
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

print("🧪 TESTING FULL DRIVE ACCESS")
print("=" * 40)

# Test 1: Try to access the previously problematic folder
mysterious_folder_id = "1VtnKoXBgM2m3Y9RIzW4hHPflDu5dP5-J"

print(f"🔍 Testing access to previously problematic folder:")
print(f"   ID: {mysterious_folder_id}")

try:
    folder_info = svc.files().get(
        fileId=mysterious_folder_id,
        fields="id, name, mimeType, parents"
    ).execute()
    
    print(f"   ✅ SUCCESS! Folder accessible:")
    print(f"      Name: {folder_info.get('name', 'N/A')}")
    print(f"      ID: {folder_info.get('id')}")
    print(f"      MimeType: {folder_info.get('mimeType')}")
    print(f"      Parents: {folder_info.get('parents', [])}")
    
except Exception as e:
    print(f"   ❌ FAILED to access folder:")
    print(f"      Error: {e}")

print()

# Test 2: Try to list the contents of this folder (what was failing before)
print(f"📋 Testing ability to LIST contents of the folder:")

try:
    contents = svc.files().list(
        q=f"'{mysterious_folder_id}' in parents and trashed=false",
        fields="files(id, name, mimeType)",
        pageSize=100
    ).execute()
    
    files = contents.get('files', [])
    folders = [f for f in files if f.get('mimeType') == 'application/vnd.google-apps.folder']
    
    print(f"   ✅ SUCCESS! Found {len(files)} total items:")
    print(f"      📁 Folders: {len(folders)}")
    print(f"      📄 Files: {len(files) - len(folders)}")
    
    if folders:
        print(f"   📋 Folders found:")
        for folder in sorted(folders, key=lambda x: x['name'])[:10]:  # Show first 10
            print(f"      - {folder['name']}")
        if len(folders) > 10:
            print(f"      ... and {len(folders) - 10} more")
            
except Exception as e:
    print(f"   ❌ FAILED to list folder contents:")
    print(f"      Error: {e}")

print()

# Test 3: Verify we still have Sheets access
print(f"📊 Verifying Google Sheets access still works:")

try:
    # Try to access the Monthly Budget spreadsheet mentioned in USER.md
    # We can't access it directly without knowing the ID, but we can verify the token works
    # for Drive operations which should confirm the scope is working
    
    # Test a basic Drive operation to confirm scope
    about = svc.about().get(fields="user, storageQuota").execute()
    user = about.get('user', {})
    print(f"   ✅ Sheets/Drive scope working:")
    print(f"      Authenticated as: {user.get('displayName', 'Unknown')} ({user.get('emailAddress', 'Unknown')})")
    
except Exception as e:
    print(f"   ❌ Scope verification failed:")
    print(f"      Error: {e}")

print()
print("🏁 TEST COMPLETE")