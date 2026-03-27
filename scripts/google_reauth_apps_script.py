#!/usr/bin/env python3
"""
One-time OAuth re-auth to get scopes needed for Google Apps Script automation.
Writes refreshed creds to .secrets/google_sheets & drive.env
"""
from pathlib import Path
import os

from google_auth_oauthlib.flow import InstalledAppFlow

ENV_PATH = Path('/Users/ryantaylorvegh/.openclaw/workspace/.secrets/google_sheets & drive.env')

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/script.projects',
    'https://www.googleapis.com/auth/script.deployments',
    'https://www.googleapis.com/auth/script.webapp.deploy',
]


def load_env(path: Path):
    data = {}
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, v = line.split('=', 1)
        data[k.strip()] = v.strip().strip('"').strip("'")
    return data


def save_env(path: Path, updates: dict):
    lines = path.read_text().splitlines()
    out = []
    seen = set()
    for raw in lines:
        if '=' not in raw or raw.strip().startswith('#'):
            out.append(raw)
            continue
        k, _ = raw.split('=', 1)
        key = k.strip()
        if key in updates:
            out.append(f"{key}={updates[key]}")
            seen.add(key)
        else:
            out.append(raw)
    for k, v in updates.items():
        if k not in seen:
            out.append(f"{k}={v}")
    path.write_text('\n'.join(out) + '\n')


def main():
    env = load_env(ENV_PATH)
    client_id = env.get('GOOGLE_SHEETS_CLIENT_ID')
    client_secret = env.get('GOOGLE_SHEETS_CLIENT_SECRET')
    redirect_uri = env.get('GOOGLE_SHEETS_REDIRECT_URI') or 'http://localhost'

    if not client_id or not client_secret:
        raise SystemExit('Missing GOOGLE_SHEETS_CLIENT_ID / GOOGLE_SHEETS_CLIENT_SECRET')

    flow = InstalledAppFlow.from_client_config(
        {
            'installed': {
                'client_id': client_id,
                'client_secret': client_secret,
                'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                'token_uri': 'https://oauth2.googleapis.com/token',
                'redirect_uris': [redirect_uri, 'http://localhost'],
            }
        },
        SCOPES,
    )

    creds = flow.run_local_server(port=0, open_browser=True)

    updates = {
        'GOOGLE_SHEETS_ACCESS_TOKEN': creds.token or '',
        'GOOGLE_SHEETS_REFRESH_TOKEN': creds.refresh_token or env.get('GOOGLE_SHEETS_REFRESH_TOKEN', ''),
    }
    save_env(ENV_PATH, updates)

    print('✅ Re-auth complete. Updated .secrets/google_sheets & drive.env with refreshed token(s).')
    print('Scopes granted for Apps Script deployment automation.')


if __name__ == '__main__':
    main()
