#!/usr/bin/env python3
"""
Apply bold formatting to character names via Google Docs API
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

docs_service = build('docs', 'v1', credentials=creds)

# Read the formatted text
input_file = os.path.join(workspace_dir, 'formatted_book_bold.txt')
with open(input_file, 'r', encoding='utf-8') as f:
    text = f.read()

print(f"Loaded {len(text)} characters")

# Create new document
body = {'title': 'Unforgotten Whisper (Draft 2) - FULLY FORMATTED'}
new_doc = docs_service.documents().create(body=body).execute()
doc_id = new_doc['documentId']
print(f"Created doc: {doc_id}")

# Insert text
requests = [{
    'insertText': {
        'location': {'index': 1},
        'text': text
    }
}]
docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
print("Text inserted")

# Now find character names and apply bold
# Known character names to bold
character_names = [
    'Zara', 'Flora', 'Nathan', 'Alfred', 'Letzier', 'Zeb', 'Daisy', 
    'Colten', 'Reanna', 'Rheanna', 'Azreal', 'Stone', 'Dan', 'Blade',
    'Andrew', 'Nalie', 'Nova', 'Amika', 'Sileth', 'Julie', 'Elora',
    'Lunna', 'Ava', 'Joy', 'Mike', 'Eric', 'Greg', 'Tiffany',
    'Jax', 'V78', 'Anthony'
]

# Get document to find positions
doc = docs_service.documents().get(documentId=doc_id).execute()
content = doc.get('body').get('content')

# Build a map of text to find positions
# This is complex - let's simplify: find each character name and bold it
# We'll search through paragraphs and find matching text

print("Applying bold formatting...")

# Get all text with indices
def get_all_text_with_indices(content):
    """Extract all text with their start/end indices"""
    result = []
    for elem in content:
        if 'paragraph' in elem:
            para = elem['paragraph']
            start = elem.get('startIndex', 0)
            for el in para.get('elements', []):
                if 'textRun' in el:
                    text = el['textRun'].get('content', '')
                    el_start = el.get('startIndex', start)
                    result.append({
                        'text': text,
                        'startIndex': el_start,
                        'endIndex': el_start + len(text)
                    })
    return result

text_elements = get_all_text_with_indices(content)
print(f"Found {len(text_elements)} text elements")

# Find and bold character names
requests = []
for name in character_names:
    for i, elem in enumerate(text_elements):
        if elem['text'].strip() == name:
            # Found a character name - apply bold
            requests.append({
                'updateTextStyle': {
                    'range': {
                        'startIndex': elem['startIndex'],
                        'endIndex': elem['endIndex']
                    },
                    'textStyle': {
                        'bold': True
                    },
                    'fields': 'bold'
                }
            })
            print(f"Bolded: {name} at {elem['startIndex']}")

# Apply in batches of 50
if requests:
    print(f"Applying {len(requests)} bold updates...")
    for i in range(0, len(requests), 50):
        batch = requests[i:i+50]
        try:
            docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': batch}).execute()
            print(f"Applied batch {i//50 + 1}")
        except Exception as e:
            print(f"Error in batch {i//50 + 1}: {e}")

print(f"\n✅ Complete: https://docs.google.com/document/d/{doc_id}/edit")
