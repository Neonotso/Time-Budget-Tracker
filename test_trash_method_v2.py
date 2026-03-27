#!/usr/bin/env python3
"""
Test the correct way to trash a file in Google Drive API - Version 2.
Check what parameters files().update actually accepts.
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

print("🧪 TESTING TRASH METHODS - VERSION 2")
print("=" * 40)

# Let's first check what the update method actually accepts by looking at a simple file
print("🔍 Examining a known file to understand update parameters...")

# Get info about a file we know exists
try:
    file_info = svc.files().get(
        fileId="1tS_LRgG7PoQmC20WEnAf08vB_uRrOq5Z",  # Mike L folder we know exists
        fields="id, name, trashed"
    ).execute()
    
    print(f"   File: '{file_info['name']}'")
    print(f"   ID: {file_info['id']}")
    print(f"   Currently trashed: {file_info.get('trashed', 'NOT FOUND IN RESPONSE')}")
    
    # Let's see all available fields
    full_info = svc.files().get(
        fileId="1tS_LRgG7PoQmC20WEnAf08vB_uRrOq5Z"
    ).execute()
    
    print(f"   Available fields in response: {list(full_info.keys())}")
    
except Exception as e:
    print(f"   ❌ Error getting file info: {e}")

print()

# Let's try to understand the update method by checking what it does
print(f"📚 Researching correct trash method...")
print(f"   According to Google Drive API documentation:")
print(f"   To move a file to trash, you should set the 'trashed' property to True")
print(f"   using the files.update method.")
print(f"   The parameter should be passed in the request body, not as a keyword argument.")

print(f"\n🧪 Testing correct approach...")

# Create a test folder
print(f"📁 Creating test folder...")
try:
    test_folder = svc.files().create(
        body={
            'name': 'TEST_TRASH_METHOD',
            'mimeType': 'application/vnd.google-apps.folder'
        },
        fields='id, name'
    ).execute()
    
    test_folder_id = test_folder['id']
    print(f"   Created: '{test_folder['name']}' (ID: {test_folder_id})")
    
except Exception as e:
    print(f"   ❌ Failed to create test folder: {e}")
    exit(1)

# Test the CORRECT way to trash: set trashed=True in the request body
print(f"\n🗑️  Testing CORRECT trash method:")
print(f"   Using files().update with body={'trashed': True}")

try:
    result = svc.files().update(
        fileId=test_folder_id,
        body={'trashed': True}
    ).execute()
    
    print(f"      ✅ Success! Response: {result.get('trashed', 'NO TRASHED FIELD')}")
    
    # Verify
    verification = svc.files().get(
        fileId=test_folder_id,
        fields="trashed"
    ).execute()
    
    if verification.get('trashed'):
        print(f"      ✅ Verified: File is now in trash")
    else:
        print(f"      ⚠️  Verification issue: trashed={verification.get('trashed')}")
        
except Exception as e:
    print(f"      ❌ Failed: {e}")

# Test restoring from trash
print(f"\n🔄 Testing restore from trash:")
try:
    result = svc.files().update(
        fileId=test_folder_id,
        body={'trashed': False}
    ).execute()
    
    print(f"      ✅ Success! Restored from trash")
    
    # Verify
    verification = svc.files().get(
        fileId=test_folder_id,
        fields="trashed"
    ).execute()
    
    if not verification.get('trashed'):
        print(f"      ✅ Verified: File is no longer in trash")
    else:
        print(f"      ⚠️  Verification issue: trashed={verification.get('trashed')}")
        
except Exception as e:
    print(f"      ❌ Failed: {e}")

# Finally, permanently delete the test folder
print(f"\n💥 Testing permanent deletion:")
try:
    svc.files().delete(fileId=test_folder_id).execute()
    print(f"      ✅ Test folder permanently deleted")
    
except Exception as e:
    print(f"      ❌ Error in permanent deletion: {e}")

print()
print("🏁 TRASH METHOD TEST COMPLETE")
print("💡 Key insight: Use body={'trashed': True/False} in files().update")