#!/usr/bin/env python3
"""
COMPLETE SCAN OF ALL ACCESSIBLE FOLDERS IN GOOGLE DRIVE
No assumptions, no filtering - just discover everything we can see.
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

print("🔍 STARTING COMPLETE GOOGLE DRIVE FOLDER SCAN")
print("=" * 60)
print("📋 Goal: Discover EVERY accessible folder - no assumptions!")
print("📋 Method: Iterative pagination to get ALL folders")
print("📋 Output: Complete list of folders with hierarchical info")
print()

# Get ALL folders with pagination
all_folders = []
page_token = None
page_count = 0

print("📥 Fetching all folders (this may take a moment)...")

while True:
    page_count += 1
    print(f"   📄 Fetching page {page_count}...")
    
    try:
        if page_token:
            results = svc.files().list(
                q="trashed=false and mimeType='application/vnd.google-apps.folder'",
                fields="files(id, name, parents)",
                pageSize=1000,  # Maximum page size
                pageToken=page_token
            ).execute()
        else:
            results = svc.files().list(
                q="trashed=false and mimeType='application/vnd.google-apps.folder'",
                fields="files(id, name, parents)",
                pageSize=1000
            ).execute()
        
        folders = results.get('files', [])
        all_folders.extend(folders)
        
        print(f"      ✅ Found {len(folders)} folders in page {page_count}")
        
        page_token = results.get('nextPageToken')
        if not page_token:
            print(f"      🏁 No more pages - finished!")
            break
            
    except Exception as e:
        print(f"      ❌ Error fetching page {page_count}: {e}")
        break

print(f"\n📊 TOTAL FOLDERS FOUND: {len(all_folders)}")
print("=" * 60)

# Now let's analyze what we found
if all_folders:
    print("🔍 ANALYZING FOLDER STRUCTURE...")
    
    # Build a lookup dictionary for fast access
    folder_lookup = {folder['id']: folder for folder in all_folders}
    
    # Categorize folders
    root_level_folders = []  # Folders with no parents or inaccessible parents
    child_folders = []       # Folders with accessible parents
    problematic_folders = [] # Folders that reference parents we can't find
    
    for folder in all_folders:
        folder_id = folder['id']
        folder_name = folder['name']
        parents = folder.get('parents', [])
        
        if not parents:
            # No parents listed - could be root level
            root_level_folders.append(folder)
        else:
            # Check if all parents are accessible
            accessible_parents = []
            inaccessible_parents = []
            
            for parent_id in parents:
                if parent_id in folder_lookup:
                    accessible_parents.append(parent_id)
                else:
                    inaccessible_parents.append(parent_id)
            
            if not inaccessible_parents:
                # All parents accessible
                child_folders.append(folder)
            else:
                # Some parents inaccessible - problematic
                problematic_folders.append({
                    'folder': folder,
                    'accessible_parents': accessible_parents,
                    'inaccessible_parents': inaccessible_parents
                })
    
    print(f"📁 Root-level folders (no parents): {len(root_level_folders)}")
    print(f"📂 Child folders (accessible parents): {len(child_folders)}")
    print(f"⚠️  Problematic folders (broken parent refs): {len(problematic_folders)}")
    
    # Show root level folders
    print(f"\n🌳 ROOT LEVEL FOLDERS:")
    print("-" * 40)
    for folder in sorted(root_level_folders, key=lambda x: x['name'].lower()):
        print(f"   📁 {folder['name']}")
        print(f"      ID: {folder['id']}")
    
    # Show problematic folders (these are the interesting ones!)
    print(f"\n⚠️  PROBLEMATIC FOLDERS (reference parents we can't access):")
    print("-" * 50)
    for i, pf in enumerate(problematic_folders, 1):
        folder = pf['folder']
        accessible = pf['accessible_parents']
        inaccessible = pf['inaccessible_parents']
        
        print(f"{i:2d}. 📁 {folder['name']} (ID: {folder['id']})")
        if accessible:
            print(f"      ✅ Accessible parents: {accessible}")
        if inaccessible:
            print(f"      ❌ Inaccessible parents: {inaccessible}")
        
        # Try to get info about the inaccessible parents
        for parent_id in inaccessible:
            print(f"      🔍 Checking inaccessible parent ID {parent_id}...")
            try:
                # We know this will fail, but let's see the exact error
                svc.files().get(fileId=parent_id, fields="id").execute()
                print(f"         🤯 Actually accessible?!)")
            except Exception as e:
                if "File not found" in str(e):
                    print(f"         💀 Confirmed: Parent folder truly doesn't exist")
                elif "insufficientPermissions" in str(e):
                    print(f"         🔒 Permission denied to access parent")
                else:
                    print(f"         ❓ Other error: {str(e)[:100]}...")
        print()
    
    # Now let's look for patterns that might indicate student folders
    print(f"\n🎯 SEARCHING FOR POTENTIAL STUDENT FOLDERS:")
    print("-" * 50)
    
    # Common indicators of student folders based on what we know
    student_name_indicators = [
        'Mike', 'Caleb', 'Tiffany', 'Evan', 'Eric', 'Greg', 'Mandy', 'Henry', 
        'Joy', 'Vegh', 'David', 'Jonathan', 'Stein', 'Lau', 'Kaitis', 'Maukaitis',
        'Valentino', 'Leah', 'Luke', 'Jim', 'Victoria'
    ]
    
    potential_students = []
    
    for folder in all_folders:
        folder_name = folder['name'].lower()
        # Check if folder name contains any student indicators
        matches = [indicator for indicator in student_name_indicators 
                  if indicator.lower() in folder_name]
        if matches:
            potential_students.append({
                'folder': folder,
                'matches': matches
            })
    
    print(f"👥 Found {len(potential_students)} potential student folders:")
    for i, ps in enumerate(potential_students, 1):
        folder = ps['folder']
        matches = ps['matches']
        print(f"   {i:2d}. 📁 {folder['name']} (ID: {folder['id']})")
        print(f"       Matches: {', '.join(matches)}")
        
        # Show what's inside this folder
        try:
            contents = svc.files().list(
                q=f"'{folder['id']}' in parents and trashed=false",
                fields="files(id, name, mimeType)",
                pageSize=100
            ).execute()
            
            items = contents.get('files', [])
            subfolders = [item for item in items if item['mimeType'] == 'application/vnd.google-apps.folder']
            files = [item for item in items if item['mimeType'] != 'application/vnd.google-apps.folder']
            
            # Look for date folders
            date_pattern = re.compile(r'\d{4} \d{2} [A-Z][a-z]+ \d{2}')
            date_folders = [sf for sf in subfolders if date_pattern.match(sf['name'])]
            
            print(f"       📁 Contains {len(subfolders)} folders, {len(files)} files")
            if date_folders:
                print(f"       📅 Date folders ({len(date_folders)}): {sorted([df['name'] for df in date_folders])}")
            elif subfolders:
                print(f"       📂 Subfolders: {[sf['name'] for sf in subfolders[:5]]}{'...' if len(subfolders) > 5 else ''}")
            print()
        except Exception as e:
            print(f"       ❌ Error listing contents: {e}")
            print()
    
    # Let's also look for ANY folders that contain date patterns (regardless of name)
    print(f"\n📅 FOLDERS CONTAINING DATE-FORMATTED SUBFOLDERS:")
    print("-" * 50)
    
    date_container_folders = []
    
    for folder in all_folders:
        try:
            contents = svc.files().list(
                q=f"'{folder['id']}' in parents and trashed=false",
                fields="files(id, name, mimeType)",
                pageSize=100
            ).execute()
            
            items = contents.get('files', [])
            subfolders = [item for item in items if item['mimeType'] == 'application/vnd.google-apps.folder']
            date_pattern = re.compile(r'\d{4} \d{2} [A-Z][a-z]+ \d{2}')
            date_folders = [sf for sf in subfolders if date_pattern.match(sf['name'])]
            
            if date_folders:
                date_container_folders.append({
                    'folder': folder,
                    'date_folders': date_folders
                })
        except Exception as e:
            # Skip folders we can't read
            continue
    
    print(f"📅 Found {len(date_container_folders)} folders containing date-formatted subfolders:")
    for i, dcf in enumerate(date_container_folders, 1):
        folder = dcf['folder']
        date_folders = dcf['date_folders']
        print(f"   {i:2d}. 📁 {folder['name']} (ID: {folder['id']})")
        print(f"       📅 Date folders ({len(date_folders)}):")
        for df in sorted(date_folders, key=lambda x: x['name']):
            print(f"          - {df['name']}")
        print()
    
    # SUMMARY
    print("=" * 60)
    print("📋 SCAN SUMMARY")
    print("=" * 60)
    print(f"📁 Total folders discovered: {len(all_folders)}")
    print(f"🌳 Root-level folders: {len(root_level_folders)}")
    print(f"📂 Child folders: {len(child_folders)}")
    print(f"⚠️  Folders with broken parent references: {len(problematic_folders)}")
    print(f"👥 Potential student folders (by name): {len(potential_students)}")
    print(f"📅 Folders containing date-formatted lesson folders: {len(date_container_folders)}")
    
    if date_container_folders:
        print(f"\n🏆 LIKELY LESSON STRUCTURE FOLDERS:")
        print("-" * 40)
        total_date_folders = sum(len(dcf['date_folders']) for dcf in date_container_folders)
        print(f"📅 Total date-formatted lesson folders found: {total_date_folders}")
        print(f"👥 Folders containing lesson dates: {len(date_container_folders)}")
        
        print(f"\n📝 DETAILS:")
        for i, dcf in enumerate(date_container_folders, 1):
            folder = dcf['folder']
            date_folders = dcf['date_folders']
            print(f"   {i}. {folder['name']}: {len(date_folders)} lesson dates")
            # Show first few dates
            displayed_dates = sorted([df['name'] for df in date_folders])[:3]
            if len(date_folders) > 3:
                displayed_dates.append(f"...and {len(date_folders)-3} more")
            print(f"      Dates: {', '.join(displayed_dates)}")

else:
    print("❌ No folders found!")

print("\n" + "=" * 60)
print("🏁 COMPLETE DRIVE SCAN FINISHED")
print("=" * 60)