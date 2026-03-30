#!/usr/bin/env python3
"""
Direct check of the Lessons folder using the EXACT same approach 
as the working _drive_list_mum.py script, but with maximum verbosity.
"""

from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Use the EXACT same path as the working scripts
ENV = Path('/Users/ryantaylorvegh/.openclaw/workspace/.secrets/google_sheets & drive.env')

print("🔧 Loading environment from:", ENV)
print("📂 Environment file exists:", ENV.exists())

if not ENV.exists():
    print("❌ ERROR: Environment file not found!")
    exit(1)

# Load environment exactly as the working scripts do
vals = {}
print("📖 Reading environment file...")
for line_num, line in enumerate(ENV.read_text().splitlines(), 1):
    s = line.strip()
    if not s or s.startswith('#') or '=' not in s:
        continue
    k, v = s.split('=', 1)
    vals[k.strip()] = v.strip().strip('"').strip("'")
    print(f"   Line {line_num}: {k.strip()} = [{'*' * len(v)}]")  # Mask the values

print(f"🔑 Loaded {len(vals)} environment variables")

# Create credentials exactly as the working scripts do
creds = Credentials(
    token=vals.get('GOOGLE_SHEETS_ACCESS_TOKEN') or None,
    refresh_token=vals.get('GOOGLE_SHEETS_REFRESH_TOKEN'),
    token_uri='https://oauth2.googleapis.com/token',
    client_id=vals.get('GOOGLE_SHEETS_CLIENT_ID'),
    client_secret=vals.get('GOOGLE_SHEETS_CLIENT_SECRET'),
)

print("🔐 Checking credentials validity...")
if not creds.valid:
    print("🔄 Refreshing credentials...")
    try:
        creds.refresh(Request())
        print("✅ Credentials refreshed successfully")
    except Exception as e:
        print(f"❌ ERROR refreshing credentials: {e}")
        exit(1)
else:
    print("✅ Credentials are already valid")

# Build the service exactly as the working scripts do
print("🔧 Building Drive service...")
try:
    svc = build('drive', 'v3', credentials=creds)
    print("✅ Drive service built successfully")
except Exception as e:
    print(f"❌ ERROR building Drive service: {e}")
    exit(1)

# Use the EXACT same folder search approach as the working scripts
FOLDER = 'application/vnd.google-apps.folder'

def find_folder(name, parent=None):
    print(f"🔍 Searching for folder: '{name}'" + (f" in parent '{parent}'" if parent else ""))
    q = ["trashed=false", f"name='{name}'", f"mimeType='{FOLDER}'"]
    if parent:
        q.append(f"'{parent}' in parents")
    query = ' and '.join(q)
    print(f"🔎 Query: {query}")
    
    try:
        result = svc.files().list(
            q=query,
            fields='files(id,name)',
            pageSize=10
        ).execute()
        files = result.get('files', [])
        print(f"📊 Found {len(files)} matching folders")
        for i, f in enumerate(files):
            print(f"   {i+1}. {f['name']} (ID: {f['id']})")
        return files[0] if files else None
    except Exception as e:
        print(f"❌ ERROR during folder search: {e}")
        return None

print("\n" + "="*60)
print("🚀 STARTING DIRECT LESSONS FOLDER SEARCH")
print("="*60)

# Step 1: Find the Lessons folder (exactly as _drive_list_mum.py does)
print("\n📋 STEP 1: Looking for 'Lessons' folder...")
lessons = find_folder('Lessons')
print(f"🎯 Result: Lessons = {lessons}")

if lessons is None:
    print("\n⚠️  Lessons folder not found with exact name match. Trying variations...")
    
    # Try case variations and common alternatives
    variations = [
        'lessons', 'LESSONS', 'Lesson', 'lesson',
        'Lessons ', ' Lessons',  # With spaces
        'LessonsFolder', 'Lessons_Folder'
    ]
    
    for variation in variations:
        print(f"\n🔍 Trying variation: '{variation}'")
        result = find_folder(variation)
        if result is not None:
            lessons = result
            print(f"✅ Found with variation '{variation}'!")
            break
        else:
            print(f"❌ Not found with '{variation}'")

# Step 2: If we found Lessons, look for Mum inside it (exactly as _drive_list_mum.py does)
if lessons is not None:
    print(f"\n📋 STEP 2: Looking for 'Mum' folder inside Lessons (ID: {lessons['id']})...")
    mum = find_folder('Mum', lessons['id'])
    print(f"🎯 Result: Mum = {mum}")
    
    # Step 3: If we found Mum, list its contents (exactly as _drive_list_mum.py does)
    if mum is not None:
        print(f"\n📋 STEP 3: Listing contents of Mum folder (ID: {mum['id']})...")
        print(f"🔍 Query: trashed=false and '{mum['id']}' in parents")
        try:
            items = svc.files().list(
                q=f"trashed=false and '{mum['id']}' in parents",
                fields='files(id,name,mimeType,createdTime)',
                pageSize=300
            ).execute().get('files', [])
            
            print(f"📊 Found {len(items)} items in Mum folder:")
            if not items:
                print("   (folder is empty)")
            else:
                for it in sorted(items, key=lambda x: x['name']):
                    mime_type = it['mimeType']
                    if mime_type == FOLDER:
                        type_icon = "📁"
                    else:
                        type_icon = "📄"
                    print(f"   {type_icon} {it['name']} | {mime_type} | {it['id']}")
                    
                    # If it's a folder, show its contents too (like the original script)
                    if mime_type == FOLDER:
                        try:
                            sub_items = svc.files().list(
                                q=f"trashed=false and '{it['id']}' in parents",
                                fields='files(id,name,mimeType)',
                                pageSize=300
                            ).execute().get('files', [])
                            for sub_item in sorted(sub_items, key=lambda x: x['name']):
                                sub_type_icon = "📁" if sub_item['mimeType'] == FOLDER else "📄"
                                print(f"     {sub_type_icon} {sub_item['name']} | {sub_item['mimeType']} | {sub_item['id']}")
                        except Exception as e:
                            print(f"     ❌ Error listing sub-contents: {e}")
        except Exception as e:
            print(f"❌ ERROR listing Mum folder contents: {e}")
    else:
        print("ℹ️  Mum folder not found inside Lessons")
else:
    print("\n❌ CRITICAL: Could not find Lessons folder at all")
    print("💡 This suggests either:")
    print("   1. The folder name is different than 'Lessons'")
    print("   2. There are permission issues") 
    print("   3. The folder is in a different location/shared drive")
    print("   4. The folder has been deleted or moved")
    
    print("\n🔍 Let's try a broader search to see what folders WE CAN see...")
    
    # Let's see what folders are actually visible
    print("\n🔍 BROAD SEARCH: Looking for ALL accessible folders...")
    try:
        all_results = svc.files().list(
            q="trashed=false and mimeType='application/vnd.google-apps.folder'",
            fields='files(id,name,parents)',
            pageSize=100
        ).execute()
        
        all_folders = all_results.get('files', [])
        print(f"📊 Found {len(all_folders)} accessible folders total")
        
        # Show first 20
        print("\n📋 First 20 accessible folders:")
        for i, folder in enumerate(sorted(all_folders, key=lambda x: x['name'])[:20]):
            parents = folder.get('parents', [])
            parent_info = f" (parent: {parents[0] if parents else 'None/Root'})"
            print(f"   {i+1:2d}. {folder['name']}{parent_info}")
        
        if len(all_folders) > 20:
            print(f"   ... and {len(all_folders) - 20} more folders")
            
        # Look for folders that might be Lessons-related
        print("\n🎯 Looking for folders with 'lesson' in name (case-insensitive):")
        lesson_related = [f for f in all_folders if 'lesson' in f['name'].lower()]
        if lesson_related:
            print(f"   Found {len(lesson_related)} lesson-related folders:")
            for folder in lesson_related:
                parents = folder.get('parents', [])
                parent_info = f" (parent: {parents[0] if parents else 'None/Root'})"
                print(f"   📁 {folder['name']}{parent_info}")
        else:
            print("   No folders with 'lesson' in name found")
            
        # Look for student-like folders
        print("\n👥 Looking for potential student folders:")
        # Based on what we've seen: Mike L, Caleb, Tiffany
        student_indicators = ['Mike', 'Caleb', 'Tiffany', 'Evan', 'Eric', 'Greg', 'Mandy', 'Henry', 'Joy', 'Vegh', 'David', 'Jonathan']
        potential_students = []
        for indicator in student_indicators:
            matches = [f for f in all_folders if indicator.lower() in f['name'].lower()]
            potential_students.extend(matches)
        
        if potential_students:
            # Remove duplicates
            unique_students = list({f['id']: f for f in potential_students}.values())
            print(f"   Found {len(unique_students)} potential student folders:")
            for folder in sorted(unique_students, key=lambda x: x['name']):
                parents = folder.get('parents', [])
                parent_info = f" (parent: {parents[0] if parents else 'None/Root'})"
                print(f"   👤 {folder['name']}{parent_info}")
        else:
            print("   No obvious student folders found")
            
    except Exception as e:
        print(f"❌ ERROR during broad search: {e}")

print("\n" + "="*60)
print("🏁 DIRECT LESSONS FOLDER CHECK COMPLETE")
print("="*60)