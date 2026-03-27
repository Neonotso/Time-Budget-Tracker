#!/usr/bin/env python3
"""
Add character name bolding and upload
"""
import re
import os

workspace_dir = '/Users/ryantaylorvegh/.openclaw/workspace'
input_file = os.path.join(workspace_dir, 'formatted_book_final.txt')
output_file = os.path.join(workspace_dir, 'formatted_book_bold.txt')

with open(input_file, 'r', encoding='utf-8') as f:
    text = f.read()

print(f"Loaded {len(text)} characters")

# Add bold markers for character names
# Character names appear as single words on their own line, followed by paragraph
lines = text.split('\n')
processed_lines = []

# Known character names to look for
character_names = [
    'Zara', 'Flora', 'Nathan', 'Alfred', 'Letzier', 'Zeb', 'Daisy', 
    'Colten', 'Reanna', 'Rheanna', 'Azreal', 'Stone', 'Dan', 'Blade',
    'Andrew', 'Nalie', 'Nova', 'Amika', 'Sileth', 'Julie', 'Elora',
    'Lunna', 'Ava', 'Joy', 'Mike', 'Eric', 'Greg', 'Tiffany'
]

i = 0
while i < len(lines):
    line = lines[i]
    stripped = line.strip()
    
    # Check if this looks like a character name heading
    # Rules: single word, title case, known character name, followed by paragraph
    next_line_has_content = i + 1 < len(lines) and lines[i+1].strip()
    is_chapter_header = stripped.startswith('Chapter')
    is_pov = 'P.O.V' in stripped or 'Pov' in stripped
    
    if (stripped in character_names and 
        next_line_has_content and 
        not is_chapter_header and
        not is_pov and
        len(stripped) > 1):
        # This is a character name - bold it
        processed_lines.append(f"**{stripped}**")
    else:
        processed_lines.append(line)
    
    i += 1

text = '\n'.join(processed_lines)

# Save
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(text)

print(f"Saved to {output_file}")

# Upload to Google Docs
print("\n=== Uploading to Google Docs ===")
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import io
from googleapiclient.http import MediaIoBaseUpload

client_id = os.environ.get('GOOGLE_SHEETS_CLIENT_ID')
client_secret = os.environ.get('GOOGLE_SHEETS_CLIENT_SECRET')
refresh_token = os.environ.get('GOOGLE_SHEETS_REFRESH_TOKEN')

creds = Credentials(None, refresh_token=refresh_token, token_uri='https://oauth2.googleapis.com/token', client_id=client_id, client_secret=client_secret)
creds.refresh(Request())

drive_service = build('drive', 'v3', credentials=creds)
docs_service = build('docs', 'v1', credentials=creds)

with open(output_file, 'rb') as f:
    file_content = f.read()

media = MediaIoBaseUpload(io.BytesIO(file_content), mimetype='text/plain', resumable=True)

file_metadata = {
    'name': 'Unforgotten Whisper (Draft 2) - Formatted FINAL',
    'mimeType': 'application/vnd.google-apps.document'
}

created = drive_service.files().create(
    body=file_metadata,
    media_body=media,
    fields='id, webViewLink'
).execute()

print(f"✅ Final: {created.get('webViewLink')}")
print(f"Document ID: {created.get('id')}")
