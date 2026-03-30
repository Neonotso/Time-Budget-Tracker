#!/usr/bin/env python3
"""
Final book cleanup - polish the text
"""
import re
import os

workspace_dir = '/Users/ryantaylorvegh/.openclaw/workspace'
input_file = os.path.join(workspace_dir, 'edited_book_final.txt')
output_file = os.path.join(workspace_dir, 'edited_book_final.txt')

# Read
with open(input_file, 'r', encoding='utf-8') as f:
    text = f.read()

print(f"Loaded {len(text)} characters")

# Final cleanup passes
# Fix leading spaces on lines
lines = text.split('\n')
fixed_lines = []
for line in lines:
    # Remove leading spaces
    fixed_lines.append(line.lstrip())

text = '\n'.join(fixed_lines)

# Fix: period followed by space and capital (sentence spacing)
text = re.sub(r'\.([A-Z])', r'. \1', text)

# Fix: multiple spaces
text = re.sub(r'  +', ' ', text)

# Fix: space before commas/periods
text = re.sub(r' ,', ',', text)
text = re.sub(r' \.', '.', text)
text = re.sub(r' !', '!', text)
text = re.sub(r' \?', '?', text)

# Fix: double newlines between paragraphs
text = re.sub(r'\n\n+', '\n\n', text)

# Save
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(text)

print(f"Saved final version: {len(text)} chars")

# Upload to Google Docs
print("\n=== Uploading final version ===")
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

with open(output_file, 'rb') as f:
    file_content = f.read()

media = MediaIoBaseUpload(io.BytesIO(file_content), mimetype='text/plain', resumable=True)

file_metadata = {
    'name': 'Unforgotten Whisper (Draft 2) - EDITED',
    'mimeType': 'application/vnd.google-apps.document'
}

created = drive_service.files().create(
    body=file_metadata,
    media_body=media,
    fields='id, webViewLink'
).execute()

print(f"✅ Final version: {created.get('webViewLink')}")
print(f"Document ID: {created.get('id')}")
