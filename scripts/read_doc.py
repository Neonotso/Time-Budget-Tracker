import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# Load credentials
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

if not creds or not creds.valid:
    creds.refresh(Request())

doc_id = '1zzdaDe0VFVtwIcbzuNJscK_b5g6iUEa1Ydi0AUFwtsQ'
docs_service = build('docs', 'v1', credentials=creds)

doc = docs_service.documents().get(documentId=doc_id).execute()
print(f"Title: {doc.get('title')}")
# Print the first 500 characters to get a sense of content
print(doc.get('body').get('content')[0:200])
