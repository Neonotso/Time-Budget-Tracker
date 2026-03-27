#!/usr/bin/env python3
"""
Refresh Google OAuth credentials with FULL Drive scope.
Use this to get new tokens with full Drive access instead of limited drive.file scope.

Usage:
    python refresh_oauth_full_drive.py
"""

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import os
import sys

# Read existing client ID/secret
creds_dict = {}
with open('.secrets/google_sheets & drive.env') as f:
    for line in f:
        if '=' in line:
            key, val = line.strip().split('=', 1)
            creds_dict[key] = val

client_id = creds_dict.get('GOOGLE_SHEETS_CLIENT_ID')
client_secret = creds_dict.get('GOOGLE_SHEETS_CLIENT_SECRET')

# Create a client config for installed application
client_config = {
    'installed': {
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': 'http://localhost',
        'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
        'token_uri': 'https://oauth2.googleapis.com/token',
    }
}

# Scopes needed for Sheets and FULL Drive access
scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',  # FULL Drive access instead of drive.file
]

print("Starting OAuth flow with FULL Drive scope...")
print("A browser window should open. Please sign in and authorize the app.")
print("This will grant access to:")
print("  - Google Sheets")
print("  - FULL Google Drive access (read/write all files)")
print()

# Run the OAuth flow
flow = InstalledAppFlow.from_client_config(client_config, scopes)
credentials = flow.run_local_server(port=8080, prompt='consent')

print("OAuth successful!")
print()
print("New credentials:")
print(f"  Access Token: {credentials.token[:50]}...")
print(f"  Refresh Token: {credentials.refresh_token}")
print()

# Save to secrets file
secrets_file = '.secrets/google_sheets & drive.env'

# Read existing file
with open(secrets_file, 'r') as f:
    lines = f.readlines()

# Update the lines
new_lines = []
for line in lines:
    if line.startswith('GOOGLE_SHEETS_ACCESS_TOKEN='):
        new_lines.append(f'GOOGLE_SHEETS_ACCESS_TOKEN={credentials.token}\n')
    elif line.startswith('GOOGLE_SHEETS_REFRESH_TOKEN='):
        new_lines.append(f'GOOGLE_SHEETS_REFRESH_TOKEN={credentials.refresh_token}\n')
    else:
        new_lines.append(line)

# Write back
with open(secrets_file, 'w') as f:
    f.writelines(new_lines)

print(f"Updated {secrets_file}")
print("Done! You now have FULL Google Drive access.")
print("Note: This grants broader access than before - use responsibly.")