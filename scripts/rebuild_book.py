#!/usr/bin/env python3
"""
Full book editor - export, fix all chapters, create new document
"""
import os
import re
import json
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
print(f"Got {len(text)} characters")

# Fix the text
print("Fixing text...")

def fix_paragraphs(text):
    """Fix paragraph spacing - single blank line between paragraphs"""
    # Replace multiple blank lines with single blank line
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    # Remove trailing whitespace from lines
    lines = [line.rstrip() for line in text.split('\n')]
    # Join with single newlines
    return '\n'.join(lines)

# Apply fixes
fixed_text = fix_paragraphs(text)

# Count chapters
chapter_count = fixed_text.count('Chapter ')
print(f"Found approximately {chapter_count} chapter markers")

# Save fixed text locally
output_path = os.path.join(workspace_dir, 'fixed_full_book.txt')
with open(output_path, 'w') as f:
    f.write(fixed_text)
print(f"Saved fixed text to {output_path}")

# Create new document
print("Creating new Google Doc...")
body = {
    'title': 'Unforgotten Whisper (Draft 2) - Fully Edited'
}
new_doc = docs_service.documents().create(body=body).execute()
new_doc_id = new_doc['documentId']
print(f"Created new document: {new_doc_id}")
print(f"URL: https://docs.google.com/document/d/{new_doc_id}")

# Insert content - insert at end each time
# First insert empty paragraph at start to establish position 1
requests = [{
    'insertText': {
        'location': {'index': 1},
        'text': '\n'
    }
}]
docs_service.documents().batchUpdate(documentId=new_doc_id, body={'requests': requests}).execute()

# Now insert at end (position increases each time)
chunk_size = 50000  # Safe chunk size

print(f"Inserting content in chunks...")
for i in range(0, len(fixed_text), chunk_size):
    chunk = fixed_text[i:i+chunk_size]
    
    # Get current doc length to find end position
    doc = docs_service.documents().get(documentId=new_doc_id).execute()
    content = doc.get('body').get('content')
    end_index = content[-1].get('endIndex', 1)
    
    # Insert at end
    requests = [{
        'insertText': {
            'location': {'index': end_index},
            'text': chunk
        }
    }]
    
    docs_service.documents().batchUpdate(documentId=new_doc_id, body={'requests': requests}).execute()
    print(f"Inserted {min(i+chunk_size, len(fixed_text))}/{len(fixed_text)} chars")

print(f"\n✅ Complete!")
print(f"New document: https://docs.google.com/document/d/{new_doc_id}")
