#!/usr/bin/env python3
"""
Continue book editing - called from heartbeat
"""
import re
import os

workspace_dir = '/Users/ryantaylorvegh/.openclaw/workspace'
input_file = os.path.join(workspace_dir, 'edited_book_v2.txt')
output_file = os.path.join(workspace_dir, 'edited_book_final.txt')

# Read current state
with open(input_file, 'r', encoding='utf-8') as f:
    text = f.read()

print(f"Loaded {len(text)} characters")

# More comprehensive corrections - round 2
corrections = [
    # More apostrophe fixes
    (r"\bcouldent\b", "couldn't"),
    (r"\bwouldent\b", "wouldn't"),
    (r"\bshouldent\b", "shouldn't"),
    (r"\bwasent\b", "wasn't"),
    (r"\bwerent\b", "weren't"),
    (r"\bhasent\b", "hasn't"),
    (r"\bhadent\b", "hadn't"),
    (r"\bisent\b", "isn't"),
    (r"\bdoent\b", "doesn't"),
    
    # Lowercase i fixes (the tricky ones)
    (r"\bi don't", "I don't"),
    (r"\bi can't", "I can't"),
    (r"\bi won't", "I won't"),
    (r"\bi'm\b", "I'm"),
    (r"\bi've\b", "I've"),
    (r"\bi'll\b", "I'll"),
    (r"\bi'd\b", "I'd"),
    
    # Quotes in the middle of sentences
    (r'\bi\s+would', "I would"),
    (r'\bi\s+could', "I could"),
    (r'\bi\s+should', "I should"),
    (r'\bi\s+have', "I have"),
    (r'\bi\s+was', "I was"),
    (r'\bi\s+am', "I am"),
    (r'\bi\s+will', "I will"),
    
    # Specific errors found
    (r"we'll then", "Well then"),
    (r"We'll then", "Well then"), 
    (r"didint", "didn't"),
    (r"couldint", "couldn't"),
    (r"couldent", "couldn't"),
    (r"wouldint", "wouldn't"),
    (r"shouldint", "shouldn't"),
    (r"wasint", "wasn't"),
    (r"hasint", "hasn't"),
    (r"hadint", "hadn't"),
    (r"isint", "isn't"),
    (r"doent", "doesn't"),
    
    # its/it's (the tricky contextual ones - be conservative)
    (r"it's name is", "its name is"),
    (r"it's shape", "its shape"),
    (r"it's form", "its form"),
    (r"it's surface", "its surface"),
    (r"it's color", "its color"),
    (r"it's light", "its light"),
    (r"it's glow", "its glow"),
    (r"it's pulse", "its pulse"),
    (r"it's feel", "its feel"),
    (r"it's sound", "its sound"),
    
    # Punctuation
    (r"\s+([.,!?])", r"\1"),
    (r"  +", " "),
    
    # Double words
    (r"\b(a\.m\.) \1", r"\1"),
]

# Apply corrections
for pattern, replacement in corrections:
    text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

# Fix multiple spaces/newlines
text = re.sub(r"  +", " ", text)
text = re.sub(r"\n\n\n+", "\n\n", text)

# Save
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(text)

print(f"Saved to {output_file}")
print(f"New length: {len(text)} chars")

# Check if there are still lowercase i issues
lowercase_i = re.findall(r"\bi\s+[a-z]", text)
if lowercase_i:
    print(f"WARNING: Still found {len(lowercase_i)} lowercase 'i' issues")
    print("Sample:", lowercase_i[:5])

# Final upload to Google Docs
if len(text) > 1000:
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
    
    # Read the file
    with open(output_file, 'rb') as f:
        file_content = f.read()
    
    # Delete old version and upload new
    old_doc_id = '1Xd7fXa-FsEeosof86_kfa_bo6CRiB1IcRtIAhfEtV3s'
    try:
        drive_service.files().delete(fileId=old_doc_id).execute()
        print(f"Deleted old doc {old_doc_id}")
    except:
        pass
    
    media = MediaIoBaseUpload(io.BytesIO(file_content), mimetype='text/plain', resumable=True)
    
    file_metadata = {
        'name': 'Unforgotten Whisper (Draft 2) - Fully Edited v2',
        'mimeType': 'application/vnd.google-apps.document'
    }
    
    created = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, webViewLink'
    ).execute()
    
    print(f"✅ Uploaded: {created.get('webViewLink')}")
    print(f"Document ID: {created.get('id')}")
    
    # Save the new doc ID
    with open(os.path.join(workspace_dir, 'memory', 'book_doc_id.txt'), 'w') as f:
        f.write(created.get('id'))

print("\n✅ Book edit cycle complete!")
