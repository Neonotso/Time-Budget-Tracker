#!/usr/bin/env python3
"""
TEST: Are we missing API parameters that affect what gets listed?
Let's experiment with different files.list() parameters.
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

print("🧪 TESTING DIFFERENT LISTING PARAMETERS")
print("=" * 50)

# Test different queries to see what affects visibility
tests = [
    {
        "name": "Default query (our usual approach)",
        "q": "trashed=false and mimeType='application/vnd.google-apps.folder'",
        "description": "What we've been using"
    },
    {
        "name": "Remove trashed filter",
        "q": "mimeType='application/vnd.google-apps.folder'",
        "description": "See if trashed state affects visibility"
    },
    {
        "name": "Explicitly include trashed",
        "q": "mimeType='application/vnd.google-apps.folder'",
        "description": "Same as above but let's be explicit"
    },
    {
        "name": "Search for a specific old folder we know exists",
        "q": "name='2026 01 January 09' and mimeType='application/vnd.google-apps.folder'",
        "description": "Targeted search for known old folder"
    },
    {
        "name": "Search by date pattern",
        "q": "name contains '2026 01 January' and mimeType='application/vnd.google-apps.folder'",
        "description": "Find all January folders"
    },
    {
        "name": "No query at all (just get everything)",
        "q": None,
        "description": "Get all files then filter ourselves"
    }
]

results_summary = []

for test in tests:
    print(f"\n🔬 TEST: {test['name']}")
    print(f"   📝 {test['description']}")
    print(f"   🔎 Query: {test['q']}")
    
    try:
        if test['q'] is None:
            # Special case: get everything then filter
            results = svc.files().list(
                fields="files(id, name, mimeType)",
                pageSize=50
            ).execute()
        else:
            results = svc.files().list(
                q=test['q'],
                fields="files(id, name, mimeType)",
                pageSize=50
            ).execute()
        
        files = results.get('files', [])
        folders = [f for f in files if f.get('mimeType') == 'application/vnd.google-apps.folder']
        
        print(f"   📊 Results: {len(files)} total items, {len(folders)} folders")
        
        # Check if we see our target old folder
        target_found = any(f.get('name') == '2026 01 January 09' for f in folders)
        print(f"   🎯 Target '2026 01 January 09' visible: {'✅ YES' if target_found else '❌ NO'}")
        
        # Show first few folder names as examples
        sample_names = [f.get('name', 'Unknown') for f in folders[:5]]
        print(f"   📋 Sample folders: {', '.join(sample_names)}")
        
        results_summary.append({
            'test': test['name'],
            'total_items': len(files),
            'folders_count': len(folders),
            'target_visible': target_found,
            'sample_names': sample_names[:3]
        })
        
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        results_summary.append({
            'test': test['name'],
            'error': str(e)
        })

print("\n" + "=" * 60)
print("📋 SUMMARY OF ALL TESTS")
print("=" * 60)

for result in results_summary:
    if 'error' not in result:
        status = "✅ TARGET VISIBLE" if result['target_visible'] else "❌ TARGET HIDDEN"
        print(f"{result['test']:<35} | Folders: {result['folders_count']:<3} | {status}")
    else:
        print(f"{result['test']:<35} | ERROR: {result['error']}")

print("\n💡 KEY INSIGHT:")
print("If we can find folders by specific name/search but they don't appear")
print("in general listings, this suggests:")
print("  1. A default FILTER or VIEW is being applied to listings")
print("  2. The filter is based on some property (date, usage, etc.)")
print("  3. Direct access and targeted searches bypass this filter")

print("\n🔍 NEXT STEPS TO IDENTIFY THE FILTER:")
print("1. Check if there are default parameters we're missing")
print("2. Look at what properties the visible folders have in common")
print("3. Check if there's a date-based window being applied")
