#!/usr/bin/env python3
"""
Debug the parent ID mystery: we see folders claiming to have parent 
1VtnKoXBgM2m3Y9RIzW4hHPflDu5dP5-J, but we can't access that ID directly.
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

# Let's take a specific example from the broad search output:
# "4. 2026 01 January 15 (parent: 1kQFue6a1EnOsHxvgNg0NrhFklNzbKbVN)"
# That's a date folder inside the Caleb folder

print("🔍 DEBUGGING THE PARENT ID MYSTERY")
print("=" * 50)

# Let's check the Caleb folder first (we know this works)
CALEB_ID = "1kQFue6a1EnOsHxvgNg0NrhFklNzbKbVN"
print(f"📁 Checking known good folder: Caleb (ID: {CALEB_ID})")

try:
    caleb_info = svc.files().get(fileId=CALEB_ID, fields="id, name, mimeType, parents").execute()
    print(f"✅ Caleb folder: {caleb_info['name']} (ID: {caleb_info['id']})")
    print(f"   Parents: {caleb_info.get('parents', [])}")
    
    # Now let's see what's inside Caleb
    print(f"\n📋 Contents of Caleb folder:")
    caleb_contents = svc.files().list(
        q=f"'{CALEB_ID}' in parents and trashed=false",
        fields="files(id, name, mimeType)",
        pageSize=50
    ).execute()
    
    caleb_items = caleb_contents.get('files', [])
    print(f"   Found {len(caleb_items)} items:")
    
    for item in sorted(caleb_items, key=lambda x: x['name']):
        type_icon = "📁" if item['mimeType'] == 'application/vnd.google-apps.folder' else "📄"
        print(f"     {type_icon} {item['name']}")
        
        # If it's a date folder, let's check ITS parent
        if item['mimeType'] == 'application/vnd.google-apps.folder' and re.match(r'\d{4} \d{2} [A-Z][a-z]+ \d{2}', item['name']):
            print(f"       🔍 Checking parent of date folder '{item['name']}'...")
            date_parents = item.get('parents', [])
            if date_parents:
                date_parent_id = date_parents[0]
                print(f"       📋 Date folder parent ID: {date_parent_id}")
                if date_parent_id == CALEB_ID:
                    print(f"       ✅ Matches Caleb ID - makes sense!")
                else:
                    print(f"       ❓ Different from Caleb ID: {date_parent_id}")
                    
except Exception as e:
    print(f"�Error with Caleb folder: {e}")

print("\n" + "=" * 50)
print("🔍 NOW LET'S CHECK THE MYSTERIOUS PARENT ID FROM THE BROAD SEARCH")
print("=" * 50)

# From the broad search, we saw:
# "👤 Caleb (parent: 1VtnKoXBgM2m3Y9RIzW4hHPflDu5dP5-J)"
MYSTERIOUS_ID = "1VtnKoXBgM2m3Y9RIzW4hHPflDu5dP5-J"

print(f"❓ Checking mysterious parent ID: {MYSTERIOUS_ID}")
print("   (This is what the broad search claimed was the parent of Caleb, Tiffany, etc.)")

try:
    mysterious_info = svc.files().get(
        fileId=MYSTERIOUS_ID, 
        fields="id, name, mimeType, parents"
    ).execute()
    print(f"✅ Mysterious folder: {mysterious_info['name']} (ID: {mysterious_info['id']})")
    print(f"   Type: {mysterious_info['mimeType']}")
    print(f"   Parents: {mysterious_info.get('parents', [])}")
    
except Exception as e:
    print(f"❌ Cannot access mysterious ID directly: {e}")
    print(f"   This suggests the ID might be:")
    print(f"   1. Wrong/misreported")
    print(f"   2. From a different drive/shared drive")
    print(f"   3. The folder was deleted but references remain in child folders")
    print(f"   4. There's some kind of permission/scoping issue")
    
    print(f"\n🔍 Let's try to understand what's happening by checking a child folder's claimed parent...")
    
    # Let's take one of those student folders from the broad search and check its actual parents
    # From broad search: "👤 Caleb (parent: 1VtnKoXBgM2m3Y9RIzW4hHPflDu5dP5-J)"
    # Let's get the ACTUAL Caleb folder and see what ITS parents say it is
    
    try:
        # Get Caleb folder again
        caleb_folder = svc.files().get(fileId=CALEB_ID, fields="id, name, parents").execute()
        actual_parents = caleb_folder.get('parents', [])
        print(f"📋 Actual Caleb folder parents: {actual_parents}")
        
        if actual_parents:
            actual_parent_id = actual_parents[0]
            print(f"🎯 Actual parent ID of Caleb: {actual_parent_id}")
            
            # Now let's check what THAT folder actually is
            try:
                actual_parent_info = svc.files().get(
                    fileId=actual_parent_id,
                    fields="id, name, mimeType"
                ).execute()
                print(f"✅ Actual parent folder: '{actual_parent_info['name']}' (ID: {actual_parent_info['id']})")
                print(f"   Type: {actual_parent_info['mimeType']}")
                
                if actual_parent_id == MYSTERIOUS_ID:
                    print(f"   🤯 This IS the mysterious ID! So it DOES work...")
                else:
                    print(f"   🔍 Different from mysterious ID: {MYSTERIOUS_ID}")
                    print(f"   Let's check what the mysterious ID supposedly contains vs what this contains...")
                    
            except Exception as e2:
                print(f"❌ Could not access actual parent folder: {e2}")
        else:
            print(f"🤷 Caleb folder has no parents - it's at root level")
            
    except Exception as e2:
        print(f"❌ Error getting Caleb folder info: {e2}")

print("\n" + "=" * 50)
print("🧪 ALTERNATIVE THEORY: LET'S SEARCH FOR FOLDERS BY THEIR ACTUAL CONTENTS")
print("=" * 50)

# Instead of trusting the parent IDs we see, let's find folders by looking for 
# the pattern we know should exist: student folders containing date folders

print("🔍 Looking for folders that CONTAIN date-formatted folders (like '2026 03 March 24')...")

try:
    # Get all folders
    all_folders_result = svc.files().list(
        q="trashed=false and mimeType='application/vnd.google-apps.folder'",
        fields="files(id, name)",
        pageSize=100
    ).execute()
    
    all_folders = all_folders_result.get('files', [])
    print(f"📊 Checking {len(all_folders)} total folders for date-containing children...")
    
    folders_with_date_children = []
    
    for folder in all_folders:
        folder_id = folder['id']
        folder_name = folder['name']
        
        # Check what's inside this folder
        try:
            contents = svc.files().list(
                q=f"'{folder_id}' in parents and trashed=false",
                fields="files(id, name, mimeType)",
                pageSize=50
            ).execute()
            
            items = contents.get('files', [])
            date_folders = [item for item in items 
                           if item['mimeType'] == 'application/vnd.google-apps.folder' 
                           and re.match(r'\d{4} \d{2} [A-Z][a-z]+ \d{2}', item['name'])]
            
            if date_folders:
                folders_with_date_children.append({
                    'id': folder_id,
                    'name': folder_name,
                    'date_children': [df['name'] for df in date_folders]
                })
                
        except Exception as e:
            # Skip folders we can't read
            continue
    
    print(f"🎯 Found {len(folders_with_date_children)} folders containing date-formatted subfolders:")
    
    for fd in folders_with_date_children:
        print(f"   📁 {fd['name']} (ID: {fd['id']})")
        print(f"      📅 Contains {len(fd['date_children'])} date folders: {fd['date_children'][:3]}{'...' if len(fd['date_children']) > 3 else ''}")
        
        # Check if this looks like a student folder
        student_indicators = ['Mike L', 'Caleb', 'Tiffany', 'Evan', 'Jonathan', 'David', 'Greg', 'Mandy', 'Henry', 'Joy', 'Vegh']
        is_student = any(indicator in fd['name'] for indicator in student_indicators)
        if is_student:
            print(f"      👥 IDENTIFIED AS STUDENT FOLDER!")
        print()
        
except Exception as e:
    print(f"❌ Error in alternative search: {e}")

print("\n" + "=" * 50)
print("🏁 PARENT ID DEBUG COMPLETE")
print("=" * 50)