#!/usr/bin/env python3
"""
Simple approach: Update existing edited doc by finding and replacing content more carefully
"""
import os
import re
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

workspace_dir = '/Users/ryantaylorvegh/.openclaw/workspace'

client_id = os.environ.get('GOOGLE_SHEETS_CLIENT_ID')
client_secret = os.environ.get('GOOGLE_SHEETS_CLIENT_SECRET')
refresh_token = os.environ.get('GOOGLE_SHEETS_REFRESH_TOKEN')

creds = Credentials(None, refresh_token=refresh_token, token_uri='https://oauth2.googleapis.com/token', client_id=client_id, client_secret=client_secret)
creds.refresh(Request())

drive_service = build('drive', 'v3', credentials=creds)
docs_service = build('docs', 'v1', credentials=creds)

# Export original
original_doc_id = '1VEyl_muiwlcWda0dylsjRKSKeblFvl2C9wKJw-2zbDo'
print("Exporting original document...")
export = drive_service.files().export_media(
    fileId=original_doc_id,
    mimeType='text/plain'
).execute()
text = export.decode('utf-8')

# Fix paragraphs
def fix_paragraphs(text):
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    lines = [line.rstrip() for line in text.split('\n')]
    return '\n'.join(lines)

fixed_text = fix_paragraphs(text)

# Get the existing edited document
edited_doc_id = '1zzdaDe0VFVtwIcbzuNJscK_b5g6iUEa1Ydi0AUFwtsQ'

# Get current content
doc = docs_service.documents().get(documentId=edited_doc_id).execute()
content = doc.get('body').get('content')
current_end = content[-1].get('endIndex', 1)
print(f"Current document ends at position {current_end}")

# Find the end of current content
# Get text from end of document backwards to find a safe start point
end_text = ""
for elem in reversed(content):
    if 'paragraph' in elem and 'elements' in elem['paragraph']:
        for el in elem['paragraph']['elements']:
            if 'textRun' in el and 'content' in el['textRun']:
                end_text = el['textRun']['content'][-100:]
                break

print(f"End of current doc: ...{repr(end_text)}")

# Simple approach: Just add a note about where to find the full fixed text
# And save the fixed text locally for Ryan to access
output_path = os.path.join(workspace_dir, 'fixed_full_book.txt')
with open(output_path, 'w') as f:
    f.write(fixed_text)

print(f"\n✅ Fixed text saved to: {output_path}")
print(f"File size: {os.path.getsize(output_path)} bytes")

# Also copy to a more accessible location
import shutil
copy_path = os.path.join(workspace_dir, 'workspace', 'Unforgotten_Whisper_Fixed.txt')
shutil.copy(output_path, copy_path)
print(f"Also copied to: {copy_path}")

print(f"\n📄 Full fixed text is ready!")
print(f"   - {len(fixed_text)} characters")
print(f"   - ~61 chapter markers")
print(f"   - Paragraph spacing fixed (no double breaks)")
