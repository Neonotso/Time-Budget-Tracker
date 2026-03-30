#!/usr/bin/env python3
"""
TEST: Can we access OLD folders by their EXACT ID?
This tests Theory 2: Can we bypass the listing issue by using direct ID access?
"""

from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import re

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

print("🧪 TESTING DIRECT FOLDER ACCESS BY ID")
print("=" * 50)

# First, let's get a list of some folders we CAN see via listing
print("📥 Getting visible folders via API listing...")
results = svc.files().list(
    q="trashed=false and mimeType='application/vnd.google-apps.folder'",
    fields="files(id, name)",
    pageSize=20
).execute()

visible_folders = results.get('files', [])
print(f"👁️  Found {len(visible_folders)} folders visible via listing")

# Show what we can see
print("\n👁️  VISIBLE FOLDERS (via listing):")
for folder in visible_folders[:10]:  # Show first 10
    print(f"   📁 {folder['name']} (ID: {folder['id']})")

# Now let's try to access some OLD date folders we know should exist
# Based on our earlier findings, we saw folders like:
# "2026 01 January 09", "2026 01 January 15", etc.

print("\n🔍 TESTING ACCESS TO KNOWN OLD FOLDERS BY ID:")
print("-" * 50)

# Let's try to construct some IDs for old folders we know should exist
# Based on the pattern we saw, let's try to access some January folders

test_dates = [
    "2026 01 January 09",
    "2026 01 January 15", 
    "2026 01 January 16",
    "2026 02 February 03",
    "2026 02 February 10"
]

# Since we don't know the exact IDs, let's try to find them by name first
print("🔎 First, let's try to FIND these folders by name:")

found_via_name = []
not_found_via_name = []

for date_name in test_dates:
    try:
        results = svc.files().list(
            q=f"name='{date_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
            fields="files(id, name)",
            pageSize=1
        ).execute()
        
        folders = results.get('files', [])
        if folders:
            folder = folders[0]
            found_via_name.append((date_name, folder['id'], folder['name']))
            print(f"   ✅ FOUND: '{date_name}' -> ID: {folder['id']}")
        else:
            not_found_via_name.append(date_name)
            print(f"   ❌ NOT FOUND: '{date_name}'")
            
    except Exception as e:
        not_found_via_name.append(date_name)
        print(f"   ⚠️  ERROR searching for '{date_name}': {e}")

print(f"\n📊 SUMMARY:")
print(f"   Found via name search: {len(found_via_name)}")
print(f"   Not found via name search: {len(not_found_via_name)}")

# Now let's test DIRECT ACCESS to the folders we found by name
if found_via_name:
    print(f"\n🎯 TESTING DIRECT ACCESS TO FOUND FOLDERS:")
    print("-" * 40)
    
    accessible_count = 0
    inaccessible_count = 0
    
    for date_name, folder_id, folder_name in found_via_name:
        try:
            # Try to access the folder directly by ID
            folder_info = svc.files().get(
                fileId=folder_id,
                fields="id, name, mimeType"
            ).execute()
            
            print(f"   ✅ DIRECT ACCESS WORKS: {folder_name} (ID: {folder_id})")
            accessible_count += 1
            
        except Exception as e:
            print(f"   ❌ DIRECT ACCESS FAILED: {folder_name} (ID: {folder_id})")
            print(f"      Error: {e}")
            inaccessible_count += 1
    
    print(f"\n📊 DIRECT ACCESS RESULTS:")
    print(f"   ✅ Accessible directly: {accessible_count}")
    print(f"   ❌ Inaccessible directly: {inaccessible_count}")

# Test 2: Let's see if we can find ANY folders by searching for a broader pattern
print(f"\n🔍 BROADER SEARCH FOR OLDER CONTENT:")
print("-" * 40)

# Search for any folders containing "January" or "February" 
try:
    jan_results = svc.files().list(
        q="name contains 'January' and mimeType='application/vnd.google-apps.folder' and trashed=false",
        fields="files(id, name)",
        pageSize=20
    ).execute()
    
    jan_folders = jan_results.get('files', [])
    print(f"📅 Found {len(jan_folders)} folders containing 'January':")
    for folder in jan_folders[:5]:
        print(f"   📁 {folder['name']} (ID: {folder['id']})")
        
except Exception as e:
    print(f"❌ Error searching for January folders: {e}")

print("\n" + "=" * 50)
print("🏁 TEST COMPLETE")
print("=" * 50)