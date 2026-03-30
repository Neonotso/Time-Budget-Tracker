import os
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# Load credentials from environment (mock-loading logic)
client_id = os.environ.get("GOOGLE_SHEETS_CLIENT_ID")
client_secret = os.environ.get("GOOGLE_SHEETS_CLIENT_SECRET")
refresh_token = os.environ.get("GOOGLE_SHEETS_REFRESH_TOKEN")

creds = Credentials(
    None,
    refresh_token=refresh_token,
    token_uri="https://oauth2.googleapis.com/token",
    client_id=client_id,
    client_secret=client_secret
)

# Refresh credentials if expired or missing
if not creds or not creds.valid:
    creds.refresh(Request())

service = build('drive', 'v3', credentials=creds)

query = "name = 'Unforgotten Whisper (Draft 2) - Edited'"
results = service.files().list(q=query, fields="files(id, name)").execute()
files = results.get('files', [])

if files:
    print(f"Found file: {files[0]['name']} with ID: {files[0]['id']}")
else:
    print("File not found.")
