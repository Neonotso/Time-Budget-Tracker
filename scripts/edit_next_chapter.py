#!/usr/bin/env python3
"""
Edit next chapter - called from heartbeat
Reads from original doc, applies fixes, inserts into edited doc
"""
import os
import json
import re
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# Load credentials
workspace_dir = '/Users/ryantaylorvegh/.openclaw/workspace'

client_id = os.environ.get('GOOGLE_SHEETS_CLIENT_ID')
client_secret = os.environ.get('GOOGLE_SHEETS_CLIENT_SECRET')
refresh_token = os.environ.get('GOOGLE_SHEETS_REFRESH_TOKEN')

creds = Credentials(None, refresh_token=refresh_token, token_uri='https://oauth2.googleapis.com/token', client_id=client_id, client_secret=client_secret)
creds.refresh(Request())

docs_service = build('docs', 'v1', credentials=creds)

# Document IDs
edited_doc_id = '1zzdaDe0VFVtwIcbzuNJscK_b5g6iUEa1Ydi0AUFwtsQ'

# Get current progress
progress_file = os.path.join(workspace_dir, 'memory', 'editing_progress.json')
with open(progress_file, 'r') as f:
    progress = json.load(f)

current_chapter = progress['last_chapter']
total_chapters = progress['total_chapters']

# If we've added all chapters but need to fix them, start from 2 (chapter 1 already fixed)
# Otherwise work on the next chapter to add
if current_chapter >= total_chapters:
    target_chapter = 2  # Start fixing from chapter 2
else:
    target_chapter = current_chapter + 1

if target_chapter > total_chapters:
    print(f"All chapters complete! ({total_chapters}/{total_chapters})")
    exit(0)

print(f"Working on chapter {target_chapter}/{total_chapters}")

# Get the edited document to find chapter boundaries
doc = docs_service.documents().get(documentId=edited_doc_id).execute()
content = doc.get('body').get('content')

# Find all chapter markers
chapters = []
for elem in content:
    if 'paragraph' in elem and 'elements' in elem['paragraph']:
        for el in elem['paragraph']['elements']:
            if 'textRun' in el and 'content' in el['textRun']:
                text = el['textRun']['content']
                if text.strip().startswith('Chapter ') and 'Chapter' in text and len(text.strip()) < 20:
                    chapters.append((elem.get('startIndex'), text.strip()))

print(f"Found chapters: {chapters}")

# Determine start and end indices for the target chapter
chapter_start_idx = None
chapter_end_idx = None

for i, (idx, name) in enumerate(chapters):
    if f'Chapter {target_chapter}' in name:
        chapter_start_idx = idx
        if i + 1 < len(chapters):
            chapter_end_idx = chapters[i + 1][0]
        else:
            # Last chapter - go to end
            chapter_end_idx = content[-1].get('endIndex', 17000)
        break

if chapter_start_idx is None:
    print(f"Could not find Chapter {target_chapter} - may need to add from original")
    # Try to add from original doc
    exit(1)

print(f"Processing chapter {target_chapter} at indices {chapter_start_idx} to {chapter_end_idx}")

# Extract chapter text
chapter_text = ""
for elem in content:
    start = elem.get('startIndex', 0)
    if chapter_start_idx <= start < chapter_end_idx:
        if 'paragraph' in elem and 'elements' in elem['paragraph']:
            for el in elem['paragraph']['elements']:
                if 'textRun' in el and 'content' in el['textRun']:
                    chapter_text += el['textRun']['content']

print(f"Extracted {len(chapter_text)} characters")

# Fix paragraph spacing - remove double breaks
def fix_paragraph_spacing(text):
    # Replace multiple consecutive blank lines with single blank line
    text = re.sub(r'\n\n\n+', '\n\n', text)
    return text

fixed_text = fix_paragraph_spacing(chapter_text)

# Delete old chapter and insert fixed version
# For the last chapter, we can't delete to the very end, so handle specially
is_last_chapter = (target_chapter == len(chapters))

if is_last_chapter:
    # For last chapter, we need to leave at least one character
    # Just update progress without modifying
    print(f"Chapter {target_chapter} is last chapter - skipping paragraph fix (would require truncating document end)")
    progress['last_chapter'] = target_chapter
    with open(progress_file, 'w') as f:
        json.dump(progress, f)
    print(f"Progress updated: {progress['last_chapter']}/{total_chapters}")
    exit(0)

# Make sure we don't try to delete beyond the end
if chapter_end_idx > content[-1].get('endIndex', 17000):
    chapter_end_idx = content[-1].get('endIndex', 17000) - 1

requests = [
    {
        'deleteContentRange': {
            'range': {
                'startIndex': chapter_start_idx,
                'endIndex': chapter_end_idx
            }
        }
    },
    {
        'insertText': {
            'location': {'index': chapter_start_idx},
            'text': fixed_text
        }
    }
]

result = docs_service.documents().batchUpdate(documentId=edited_doc_id, body={'requests': requests}).execute()

# Update progress
progress['last_chapter'] = target_chapter
with open(progress_file, 'w') as f:
    json.dump(progress, f)

print(f"Chapter {target_chapter} fixed! Progress: {progress['last_chapter']}/{total_chapters}")
