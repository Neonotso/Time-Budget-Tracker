#!/usr/bin/env python3
"""
Deterministic after-lesson routine entrypoint for cron.

This script is the canonical callable for post-lesson automation.
It centralizes trigger detection and the handoff points for:
- reMarkable export by exact student name
- Drive upload/grouping
- recipient send (email/iMessage automation)
- cleanup to Trash

Current status:
- Trigger detection + preflight implemented.
- Export/upload/send steps require the downstream runner implementation.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

WORKSPACE = Path('/Users/ryantaylorvegh/.openclaw/workspace')
SECRETS_ENV = WORKSPACE / '.secrets' / 'google_sheets & drive.env'
PREFLIGHT_SCRIPT = WORKSPACE / 'scripts' / 'ensure_remarkable_front.applescript'
EXCLUDED_STUDENTS_FILE = Path.home() / '.openclaw' / 'excluded_students.txt'
DOWNSTREAM_RUNNER = WORKSPACE / 'scripts' / 'remarkable_lesson_pipeline.py'  # to be implemented

PRIVATE_CAL = '6qpnjqcot3plkotpupcbi5l17g@group.calendar.google.com'
KMS_CAL = 'c5f832065582c736e9e3f2c4ea0b3ff9c81243e1aa10acdbdd9f191ce52317ef@group.calendar.google.com'

TZ = ZoneInfo('America/Detroit')


def _target_date() -> date:
    raw = (os.environ.get('LESSON_TARGET_DATE') or '').strip()
    if raw:
        return date.fromisoformat(raw)
    return datetime.now(TZ).date()


def _target_now() -> datetime:
    d = _target_date()
    current = datetime.now(TZ)
    return datetime.combine(d, current.timetz(), TZ)


@dataclass
class Lesson:
    calendar_name: str
    summary: str
    start: datetime
    end: datetime
    kind: str  # voice|drum|other


def _load_env(path: Path) -> dict[str, str]:
    vals: dict[str, str] = {}
    for raw in path.read_text().splitlines():
        s = raw.strip()
        if not s or s.startswith('#') or '=' not in s:
            continue
        k, v = s.split('=', 1)
        vals[k.strip()] = v.strip().strip('"').strip("'")
    return vals


def _calendar_service():
    vals = _load_env(SECRETS_ENV)
    creds = Credentials(
        token=vals.get('GOOGLE_CALENDAR_ACCESS_TOKEN') or None,
        refresh_token=vals.get('GOOGLE_CALENDAR_REFRESH_TOKEN'),
        token_uri='https://oauth2.googleapis.com/token',
        client_id=vals.get('GOOGLE_CALENDAR_CLIENT_ID') or vals.get('GOOGLE_SHEETS_CLIENT_ID'),
        client_secret=vals.get('GOOGLE_CALENDAR_CLIENT_SECRET') or vals.get('GOOGLE_SHEETS_CLIENT_SECRET'),
    )
    if not creds.valid:
        creds.refresh(Request())
    return build('calendar', 'v3', credentials=creds)


def _target_day_lessons() -> list[Lesson]:
    svc = _calendar_service()
    target = _target_date()
    start = datetime.combine(target, datetime.min.time(), TZ)
    end = start + timedelta(days=1)

    out: list[Lesson] = []
    for cal_name, cal_id in [('Private Lessons', PRIVATE_CAL), ('Kingdom Music School', KMS_CAL)]:
        events = (
            svc.events()
            .list(
                calendarId=cal_id,
                timeMin=start.isoformat(),
                timeMax=end.isoformat(),
                singleEvents=True,
                orderBy='startTime',
            )
            .execute()
            .get('items', [])
        )
        for e in events:
            st = e.get('start', {}).get('dateTime')
            en = e.get('end', {}).get('dateTime')
            if not st or not en:
                continue
            st_dt = datetime.fromisoformat(st.replace('Z', '+00:00')).astimezone(TZ)
            en_dt = datetime.fromisoformat(en.replace('Z', '+00:00')).astimezone(TZ)
            summary = e.get('summary', '')
            low = summary.lower()
            kind = 'voice' if 'voice' in low else ('drum' if 'drum' in low else 'other')
            out.append(Lesson(cal_name, summary, st_dt, en_dt, kind))
    return out


def _voice_audio_exists(student_hint: str, target_dt: datetime) -> bool:
    d = Path.home() / 'Downloads'
    if not d.exists():
        return False
    raw = student_hint.lower().strip()
    # Accept all tokens (e.g., "caleb" from "Mandy F's son, Caleb")
    tokens = [re.sub(r'[^a-z0-9]', '', t) for t in re.split(r"\s+", raw) if t]
    candidates = set()
    if tokens:
        candidates.add(tokens[0])  # e.g., "eric"
    if len(tokens) >= 2:
        candidates.add(" ".join(tokens[:2]))  # e.g., "eric v"
    if raw:
        candidates.add(re.sub(r'[^a-z0-9]', '', raw))  # full name without punctuation
    # Add ALL individual tokens (critical for names like "Caleb" that aren't first)
    candidates.update(tokens)

    date_str = target_dt.strftime('%m-%d-%y').replace('-0', '-')
    today_markers = [
        date_str,
        target_dt.strftime('%Y-%m-%d'),
        target_dt.strftime('%-m-%-d-%y'),
        target_dt.strftime('%m_%d_%y'),
        target_dt.strftime('%m%d%y'),
    ]
    for p in d.iterdir():
        if not p.is_file():
            continue
        n = p.name.lower()
        if not any(m in n for m in today_markers):
            continue
        if any(c and c in n for c in candidates):
            return True
    return False


def _preflight_focus():
    if PREFLIGHT_SCRIPT.exists():
        subprocess.run(['osascript', str(PREFLIGHT_SCRIPT)], check=False)


def _student_hint(summary: str) -> str:
    s = summary.strip()

    # Most common direct forms - handle various lesson title formats
    # "Voice with X", "Voice/Guitar with X", "Drums with X", "Drum with X"
    import re
    
    # FIRST: Handle "'s kid/son/daughter, NAME" patterns (Mandy's son, Caleb / Henry's kid, David)
    # These must be checked BEFORE the generic "with" pattern
    m = re.search(r"'s\s+(kid|son|daughter),\s*([A-Za-z][A-Za-z\-']+)", s, flags=re.IGNORECASE)
    if m:
        return m.group(2).strip()  # Return just the name: "David", "Jonathan", "Caleb"
    
    # SECOND: Match anything after "with " (case insensitive) - "Voice with Evan Stein", "Drums with Mike L"
    m = re.search(r'with\s+(.+)$', s, re.IGNORECASE)
    if m:
        return m.group(1).strip()

    # Fallback: if there's a trailing comma segment, prefer that as the student token
    if ',' in s:
        tail = s.rsplit(',', 1)[1].strip()
        if tail:
            return tail

    return s


def _get_excluded_students() -> set[str]:
    """Load excluded students from file. Returns lowercase set of excluded names."""
    if not EXCLUDED_STUDENTS_FILE.exists():
        return set()
    with open(EXCLUDED_STUDENTS_FILE) as f:
        return {line.strip().lower() for line in f if line.strip()}


def main() -> int:
    now = _target_now()
    lessons = _target_day_lessons()

    # Load excluded students
    excluded = _get_excluded_students()
    if excluded:
        print(f'STEP 1 exclusion: skipping {excluded}')

    eligible: list[dict] = []
    for ls in lessons:
        if ls.end > now or ls.kind == 'other':
            continue
        hint = _student_hint(ls.summary)
        
        # Check if student is excluded (case-insensitive match)
        hint_lower = hint.lower()
        if any(exc in hint_lower for exc in excluded):
            print(f'STEP 1: skipping excluded student: {hint}')
            continue

        if ls.kind == 'voice':
            if _voice_audio_exists(hint, now):
                eligible.append({'kind': 'voice', 'studentHint': hint, 'summary': ls.summary})
        elif ls.kind == 'drum':
            if now >= (ls.end + timedelta(hours=2)):
                eligible.append({'kind': 'drum', 'studentHint': hint, 'summary': ls.summary})

    if not eligible:
        print('NO_ACTION')
        return 0

    print('STEP 1 trigger detection:', json.dumps({'eligibleCount': len(eligible), 'eligible': eligible}, ensure_ascii=False))
    _preflight_focus()
    print('STEP 2 preflight focus: reMarkable window prep attempted')

    if not DOWNSTREAM_RUNNER.exists():
        print('BLOCKED STEP 3: downstream runner missing:', str(DOWNSTREAM_RUNNER))
        print('ACTION: implement deterministic export/upload/send in this runner path and re-run')
        return 2

    payload = {'eligible': eligible, 'ts': now.isoformat(), 'targetDate': _target_date().isoformat()}
    proc = subprocess.run(
        [sys.executable, str(DOWNSTREAM_RUNNER)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        print('BLOCKED STEP 3+: downstream runner failed')
        if proc.stderr:
            print(proc.stderr.strip())
        if proc.stdout:
            print(proc.stdout.strip())
        return proc.returncode

    if proc.stdout:
        print(proc.stdout.strip())
    print('DONE')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
