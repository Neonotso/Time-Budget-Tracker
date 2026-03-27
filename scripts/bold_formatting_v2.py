#!/usr/bin/env python3
"""
Apply bold formatting to character names - improved version
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

# Use existing doc
doc_id = '1dWVV_eLCKHITmjZGpLtx6N8zuZAj4cc65HwExlhoHjw'

# Get document
doc = docs_service.documents().get(documentId=doc_id).execute()
content = doc.get('body').get('content')

# Build full text with positions
full_text = ""
position_map = []  # maps from text position to doc position

for elem in content:
    if 'paragraph' in elem:
        para = elem['paragraph']
        para_start = elem.get('startIndex', 0)
        for el in para.get('elements', []):
            if 'textRun' in el:
                text = el['textRun'].get('content', '')
                el_start = el.get('startIndex', para_start)
                for i, char in enumerate(text):
                    position_map.append(el_start + i)
                full_text += text

print(f"Full text length: {len(full_text)}")

# Character names to bold
character_names = [
    'Zara', 'Flora', 'Nathan', 'Alfred', 'Letzier', 'Zeb', 'Daisy', 
    'Colten', 'Reanna', 'Rheanna', 'Azreal', 'Stone', 'Dan', 'Blade',
    'Andrew', 'Nalie', 'Nova', 'Amika', 'Sileth', 'Julie', 'Elora',
    'Lunna', 'Ava', 'Joy', 'Mike', 'Eric', 'Greg', 'Tiffany',
    'Jax', 'V78', 'Anthony', 'Mr.', 'Mrs.'
]

# Find all occurrences
requests = []
found_count = 0

for name in character_names:
    # Find all occurrences of the name as a whole word
    pattern = r'\b' + re.escape(name) + r'\b'
    for match in re.finditer(pattern, full_text):
        start_pos = match.start()
        end_pos = match.end()
        
        # Map to document position
        if start_pos < len(position_map) and end_pos <= len(position_map):
            doc_start = position_map[start_pos]
            doc_end = position_map[end_pos - 1] + 1
            
            requests.append({
                'updateTextStyle': {
                    'range': {
                        'startIndex': doc_start,
                        'endIndex': doc_end
                    },
                    'textStyle': {
                        'bold': True
                    },
                    'fields': 'bold'
                }
            })
            found_count += 1
            if found_count <= 20:
                print(f"Bolding '{name}' at position {doc_start}")

print(f"\nFound {found_count} occurrences to bold")

# Apply in batches
if requests:
    print(f"Applying {len(requests)} bold updates...")
    for i in range(0, len(requests), 50):
        batch = requests[i:i+50]
        try:
            docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': batch}).execute()
            print(f"Applied batch {i//50 + 1} ({len(batch)} updates)")
        except Exception as e:
            print(f"Error in batch {i//50 + 1}: {e}")

print(f"\n✅ Complete: https://docs.google.com/document/d/{doc_id}/edit")
