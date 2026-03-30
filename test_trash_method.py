#!/usr/bin/env python3
"""
Test the correct way to trash a file in Google Drive API.
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

print("🧪 TESTING TRASH METHODS")
print("=" * 30)

# Create a temporary test folder to practice on
print("📁 Creating test folder...")
try:
    test_folder = svc.files().create(
        body={
            'name': 'TEST_FOLDER_TO_DELETE',
            'mimeType': 'application/vnd.google-apps.folder'
        },
        fields='id, name'
    ).execute()
    
    test_folder_id = test_folder['id']
    print(f"   Created: '{test_folder['name']}' (ID: {test_folder_id})")
    
except Exception as e:
    print(f"   ❌ Failed to create test folder: {e}")
    exit(1)

# Test different ways to trash it
print(f"\n🗑️  Testing different trash methods on test folder...")

# Method 1: Try with trashed parameter
print(f"   Method 1: files().update with trashed=True")
try:
    svc.files().update(
        fileId=test_folder_id,
        trashed=True
    ).execute()
    print(f"      ✅ Success!")
    
    # Verify it's trashed
    check = svc.files().get(fileId=test_folder_id, fields="trashed").execute()
    if check.get('trashed'):
        print(f"      ✅ Verified: Folder is now in trash")
    else:
        print(f"      ⚠️  Verification failed: Not showing as trashed")
        
except Exception as e:
    print(f"      ❌ Failed: {e}")

# Clean up - restore and delete properly
print(f"   🔄 Restoring test folder for cleanup...")
try:
    svc.files().update(
        fileId=test_folder_id,
        trashed=False
    ).execute()
    print(f"      ✅ Folder restored from trash")
    
    # Now permanently delete it
    svc.files().delete(fileId=test_folder_id).execute()
    print(f"      🗑️  Test folder permanently deleted")
    
except Exception as e:
    print(f"      ❌ Cleanup error: {e}")

print()
print("🏁 TRASH TEST COMPLETE")