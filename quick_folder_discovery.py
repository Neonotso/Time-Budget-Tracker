#!/usr/bin/env python3
"""
QUICK FOLDER DISCOVERY - Let's see what's actually accessible
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

print("🔍 QUICK FOLDER DISCOVERY")
print("=" * 40)

# Get first 50 folders to see what we're working with
print("📥 Fetching first 50 folders...")
results = svc.files().list(
    q="trashed=false and mimeType='application/vnd.google-apps.folder'",
    fields="files(id, name, parents)",
    pageSize=50
).execute()

folders = results.get('files', [])
print(f"📊 Found {len(folders)} folders in first batch")

# Show them
print(f"\n📋 FOLDERS FOUND:")
print("-" * 30)
for i, folder in enumerate(sorted(folders, key=lambda x: x['name'].lower()), 1):
    name = folder['name']
    folder_id = folder['id']
    parents = folder.get('parents', [])
    
    if parents:
        parent_info = f" (has {len(parents)} parent(s))"
    else:
        parent_info = " (root level or parent info unavailable)"
    
    print(f"{i:2d}. 📁 {name}")
    print(f"     ID: {folder_id}")
    print(f"     {parent_info}")
    print()

# Now let's specifically look for folders that might contain lessons
print("🔍 LOOKING FOR FOLDERS WITH DATE PATTERNS (lesson folders)...")
print("-" * 50)

import re
date_pattern = re.compile(r'\d{4} \d{2} [A-Z][a-z]+ \d{2}')

folders_with_dates = []

for folder in folders:
    folder_id = folder['id']
    folder_name = folder['name']
    
    try:
        # Check what's inside this folder
        contents = svc.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields="files(id, name, mimeType)",
            pageSize=100
        ).execute()
        
        items = contents.get('files', [])
        subfolders = [item for item in items if item['mimeType'] == 'application/vnd.google-apps.folder']
        
        # Look for date-formatted folders
        date_folders = [sf for sf in subfolders if date_pattern.match(sf['name'])]
        
        if date_folders:
            folders_with_dates.append({
                'name': folder_name,
                'id': folder_id,
                'date_count': len(date_folders),
                'date_folders': [df['name'] for sf in date_folders]
            })
            
    except Exception as e:
        # Skip if we can't read the folder
        continue

print(f"🎯 Found {len(folders_with_dates)} folders containing date-formatted subfolders:")
print()

for i, fd in enumerate(folders_with_dates, 1):
    print(f"{i:2d}. 📁 {fd['name']} (ID: {fd['id']})")
    print(f"    📅 Contains {fd['date_count']} date folders:")
    for date_folder in sorted(fd['date_folders']):
        print(f"       - {date_folder}")
    print()

# Also let's check for any folders that look like student names
print("👥 LOOKING FOR POTENTIAL STUDENT FOLDERS BY NAME:")
print("-" * 50)

student_indicators = [
    'Mike', 'Caleb', 'Tiffany', 'Evan', 'Eric', 'Greg', 'Mandy', 'Henry', 
    'Joy', 'Vegh', 'David', 'Jonathan', 'Stein', 'Lau', 'Kaitis', 'Maukaitis',
    'Valentino', 'Leah', 'Luke', 'Jim', 'Victoria'
]

potential_students = []

for folder in folders:
    folder_name = folder['name'].lower()
    matches = [indicator for indicator in student_indicators 
              if indicator.lower() in folder_name]
    if matches:
        potential_students.append({
            'name': folder['name'],
            'id': folder['id'],
            'matches': matches
        })

print(f"👥 Found {len(potential_students)} potential student folders by name:")
print()

for i, ps in enumerate(potential_students, 1):
    print(f"{i:2d}. 👤 {ps['name']} (ID: {ps['id']})")
    print(f"    Matches: {', '.join(ps['matches'])}")
    
    # Quick check of contents
    try:
        contents = svc.files().list(
            q=f"'{ps['id']}' in parents and trashed=false",
            fields="files(id, name, mimeType)",
            pageSize=20
        ).execute()
        
        items = contents.get('files', [])
        subfolders = [item for item in items if item['mimeType'] == 'application/vnd.google-apps.folder']
        files = [item for item in items if item['mimeType'] != 'application/vnd.google-apps.folder']
        
        print(f"    📁 Contains {len(subfolders)} folders, {len(files)} files")
        
        # Show date folders if any
        date_folders = [sf for sf in subfolders if date_pattern.match(sf['name'])]
        if date_folders:
            print(f"    📅 Date folders: {', '.join(sorted([df['name'] for df in date_folders]))}")
        print()
        
    except Exception as e:
        print(f"    ❌ Error checking contents: {e}")
        print()

print("=" * 50)
print("🏁 QUICK DISCOVERY COMPLETE")
print("=" * 50)