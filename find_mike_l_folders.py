#!/usr/bin/env python3
"""
Find all Mike L folders and analyze their contents to identify which one has more content.
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

print("🔍 FINDING ALL MIKE L FOLDERS")
print("=" * 40)

# Find all folders named "Mike L"
results = svc.files().list(
    q="name='Mike L' and mimeType='application/vnd.google-apps.folder' and trashed=false",
    fields="files(id, name)",
    pageSize=10
).execute()

mike_l_folders = results.get('files', [])

print(f"📊 Found {len(mike_l_folders)} folders named 'Mike L':")

mike_l_details = []

for i, folder in enumerate(mike_l_folders, 1):
    folder_id = folder['id']
    folder_name = folder['name']
    
    print(f"\n{i}. 📁 {folder_name}")
    print(f"   ID: {folder_id}")
    
    # Get contents of this folder
    try:
        contents = svc.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields="files(id, name, mimeType, size, modifiedTime)",
            pageSize=100
        ).execute()
        
        files = contents.get('files', [])
        subfolders = [f for f in files if f.get('mimeType') == 'application/vnd.google-apps.folder']
        regular_files = [f for f in files if f.get('mimeType') != 'application/vnd.google-apps.folder']
        
        print(f"   📋 Contents: {len(subfolders)} subfolders, {len(regular_files)} files")
        
        # Show subfolders (likely date folders)
        if subfolders:
            subfolder_names = [f['name'] for f in sorted(subfolders, key=lambda x: x['name'])]
            print(f"   📂 Subfolders: {', '.join(subfolder_names[:5])}{'...' if len(subfolder_names) > 5 else ''}")
        
        # Show some files if any
        if regular_files:
            file_names = [f['name'] for f in regular_files[:3]]
            print(f"   📄 Sample files: {', '.join(file_names)}{'...' if len(regular_files) > 3 else ''}")
        
        # Calculate total size if available
        total_size = 0
        for f in files:
            size_str = f.get('size')
            if size_str and size_str.isdigit():
                total_size += int(size_str)
        
        if total_size > 0:
            size_mb = total_size / (1024 * 1024)
            print(f"   💾 Estimated size: {size_mb:.2f} MB")
        
        mike_l_details.append({
            'id': folder_id,
            'name': folder_name,
            'subfolders_count': len(subfolders),
            'files_count': len(regular_files),
            'total_items': len(files),
            'total_size_bytes': total_size,
            'subfolders': subfolders,
            'files': regular_files
        })
        
    except Exception as e:
        print(f"   ❌ Error reading contents: {e}")
        mike_l_details.append({
            'id': folder_id,
            'name': folder_name,
            'error': str(e)
        })

print("\n" + "=" * 50)
print("📊 SUMMARY AND RECOMMENDATION")
print("=" * 50)

# Sort by total items (descending) to find the one with more content
valid_folders = [f for f in mike_l_details if 'error' not in f]
if len(valid_folders) >= 2:
    sorted_folders = sorted(valid_folders, key=lambda x: x['total_items'], reverse=True)
    
    print(f"📁 FOLDER WITH MORE CONTENT:")
    source = sorted_folders[0]
    print(f"   ID: {source['id']}")
    print(f"   Items: {source['total_items']} ({source['subfolders_count']} subfolders, {source['files_count']} files)")
    
    print(f"\n📁 FOLDER WITH LESS CONTENT (TARGET):")
    target = sorted_folders[-1] 
    print(f"   ID: {target['id']}")
    print(f"   Items: {target['total_items']} ({target['subfolders_count']} subfolders, {target['files_count']} files)")
    
    print(f"\n🎯 RECOMMENDED ACTION:")
    print(f"   Move contents from:")
    print(f"      {source['name']} (ID: {source['id']})")
    print(f"   TO:")
    print(f"      {target['name']} (ID: {target['id']})")
    
    # Also check which one might be newer based on modification time or folder names
    print(f"\n💡 ADDITIONAL CONSIDERATIONS:")
    print(f"   - Consider which folder has more recent content")
    print(f"   - The user mentioned one folder has 'only today's lesson notes'")
    print(f"   - Today is 2026-03-24, so look for '2026 03 March 24' folder")
    
else:
    print("❌ Could not find sufficient Mike L folders for comparison")

print(f"\n🔧 NEXT STEPS:")
print(f"   If you want me to proceed with the move, I will:")
print(f"   1. Move all subfolders from source to target")
print(f"   2. Move all files from source to target") 
print(f"   3. Verify the move was successful")
print(f"   4. Optionally move the source folder to Trash (not delete)")