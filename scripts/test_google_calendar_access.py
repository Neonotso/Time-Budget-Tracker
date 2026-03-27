#!/usr/bin/env python3
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

ENV_PATH = Path('/Users/ryantaylorvegh/.openclaw/workspace/.secrets/google_sheets & drive.env')


def load_env(path: Path):
    data = {}
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, v = line.split('=', 1)
        data[k.strip()] = v.strip().strip('"').strip("'")
    return data


def main():
    env = load_env(ENV_PATH)
    creds = Credentials(
        token=env.get('GOOGLE_SHEETS_ACCESS_TOKEN') or None,
        refresh_token=env.get('GOOGLE_SHEETS_REFRESH_TOKEN'),
        token_uri='https://oauth2.googleapis.com/token',
        client_id=env.get('GOOGLE_SHEETS_CLIENT_ID'),
        client_secret=env.get('GOOGLE_SHEETS_CLIENT_SECRET'),
    )
    if not creds.valid:
        creds.refresh(Request())

    svc = build('calendar', 'v3', credentials=creds)
    resp = svc.calendarList().list(maxResults=20).execute()
    items = resp.get('items', [])

    print(f'✅ Calendar API access works. Calendars visible: {len(items)}')
    for c in items:
        print(f"- {c.get('summary')} ({c.get('id')})")


if __name__ == '__main__':
    main()
