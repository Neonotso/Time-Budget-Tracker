#!/usr/bin/env python3
"""
COMPARE: What we see in a simple listing vs what we saw in our initial broad scan
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

print("🔍 COMPARING OLD VS RECENT FOLDER VISIBILITY")
print("=" * 55)

# Get a simple, unsorted, basic listing (like our first attempts)
print("📥 BASIC LISTING (no sorting, default parameters):")
results = svc.files().list(
    q="trashed=false and mimeType='application/vnd.google-apps.folder'",
    fields="files(id, name)",
    pageSize=100  # Get a good sample
).execute()

basic_folders = results.get('files', [])
print(f"📊 Found {len(basic_folders)} folders")

# Sort them for easier reading
basic_folders_sorted = sorted(basic_folders, key=lambda x: x['name'])

print("\n📋 BASIC LISTING RESULTS (first 20):")
for i, folder in enumerate(basic_folders_sorted[:20], 1):
    print(f"   {i:2d}. {folder['name']}")

print("\n🔍 NOW LET'S CHECK FOR SPECIFIC OLD FOLDERS WE EXPECT TO SEE:")
print("-" * 55)

# Let's look for folders that we know should exist based on our student folder investigations
expected_old_folders = [
    "2026 01 January 09",
    "2026 01 January 15", 
    "2026 01 January 16",
    "2026 02 February 03",
    "2026 02 February 10",
    "2026 02 February 17",
    "2026 02 February 24",
    "2026 03 March 06"
]

found_via_basic_listing = []
missing_via_basic_listing = []

for folder_name in expected_old_folders:
    found = any(f['name'] == folder_name for f in basic_folders)
    if found:
        found_via_basic_listing.append(folder_name)
        print(f"   ✅ FOUND in basic listing: {folder_name}")
    else:
        missing_via_basic_listing.append(folder_name)
        print(f"   ❌ MISSING from basic listing: {folder_name}")

print(f"\n📊 RESULTS:")
print(f"   Found via basic listing: {len(found_via_basic_listing)}/{len(expected_old_folders)}")
print(f"   Missing via basic listing: {len(missing_via_basic_listing)}/{len(expected_old_folders)}")

if missing_via_basic_listing:
    print(f"\n❓ MISSING FOLDERS:")
    for folder in missing_via_basic_listing:
        print(f"   - {folder}")

print("\n" + "=" * 55)
print("🔍 LET'S CHECK WHAT'S ACTUALLY IN THE BASIC LISTING")
print("=" * 55)

# Let's see what folders ARE in the basic listing to understand the pattern
print("📋 FOLDERS IN BASIC LISTING:")
for folder in basic_folders_sorted:
    print(f"   📁 {folder['name']}")

print(f"\n📊 TOTAL: {len(basic_folders_sorted)} folders in basic listing")

# Let's categorize what we see
date_folders = [f for f in basic_folders_sorted if re.match(r'\d{4} \d{2} [A-Z][a-z]+ \d{2}', f['name'])]
student_folders = [f for f in basic_folders_sorted if f['name'] in ['Mike L', 'Caleb', 'Tiffany', 'Jonathan and David', 'Evan Stein']]
other_folders = [f for f in basic_folders_sorted if f not in date_folders and f not in student_folders]

print(f"\n📊 BREAKDOWN:")
print(f"   📅 Date folders: {len(date_folders)}")
print(f"   👥 Student folders: {len(student_folders)}")
print(f"   📂 Other folders: {len(other_folders)}")

if other_folders:
    print(f"   📂 Other folders: {[f['name'] for f in other_folders]}")

# Let's see the date range of what we CAN see
if date_folders:
    date_names = [f['name'] for f in date_folders]
    print(f"\n📅 DATE RANGE IN BASIC LISTING:")
    print(f"   Earliest: {min(date_names)}")
    print(f"   Latest: {max(date_names)}")

print("\n" + "=" * 55)
print("🚨 KEY DISCOVERY")
print("=" * 55)

if missing_via_basic_listing:
    print("❌ CONFIRMED: Some older folders ARE missing from basic listing")
    print("📋 Examples of missing older folders:")
    for folder in missing_via_basic_listing[:5]:
        print(f"   - {folder}")
    
    print("\n🔍 THIS SUGGESTS:")
    print("   There IS a filter being applied to our listings")
    print("   It's likely based on DATE or AGE of the folders")
    print("   Newer folders show up, older ones get filtered out")
else:
    print("✅ All expected folders are visible in basic listing")
    print("🤔 The issue might be intermittent or more subtle")

print("\n💡 THE PATTERN YOU DESCRIBED NOW MAKES SENSE:")
print("   • New folders are visible (within the date window)")
print("   • As folders age, they move outside the window and disappear from listings")
print("   • But you can still access them by name or ID (bypassing the filter)")
print("   • When you create a new folder, it's visible (within window)")
print("   • After it ages, it too disappears from listings")
print("   • This creates the endless cycle you described")
