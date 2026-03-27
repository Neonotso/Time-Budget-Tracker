#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta, time
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

TZ = ZoneInfo("America/Detroit")
WORKDIR = Path('/Users/ryantaylorvegh/.openclaw/workspace')
ENV_PATH = WORKDIR / '.secrets/google_sheets & drive.env'
STATE_PATH = WORKDIR / 'memory/bible_reader_reminder_state.json'
SHEET_ID = '16f75U8IZjGkrgNeUyk7haDU-_isrBlmd6glnW0ah5BA'
SHEET_NAME = 'Sheet1'
SEND_SCRIPT = WORKDIR / 'scripts/send_message_via_messages.sh'

CHURCH_FOOTER = "Bauer Community Fellowship\n4852 Bauer Rd, Hudsonville, MI 49426"


@dataclass
class Slot:
    row: int
    section: str
    label: str
    first: str
    last: str
    phone: str


def load_env(path: Path) -> dict:
    d = {}
    for raw in path.read_text().splitlines():
        s = raw.strip()
        if not s or s.startswith('#') or '=' not in s:
            continue
        k, v = s.split('=', 1)
        d[k.strip()] = v.strip().strip('"').strip("'")
    return d


def sheets_service():
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
    return build('sheets', 'v4', credentials=creds)


def parse_date_from_section(section: str, now: datetime) -> Optional[datetime]:
    # Supports:
    # - "March 17 - First Name"
    # - "Mar 17 - First Name"
    # - "Sunday - April 12"
    if not section:
        return None

    month_token = None
    day = None

    # Case 1: "Month Day - ..."
    left = section.split(' - ')[0].strip()
    m = re.match(r'^([A-Za-z]+)\s+(\d{1,2})$', left)
    if m:
        month_token = m.group(1).lower()
        day = int(m.group(2))

    # Case 2: "Weekday - Month Day"
    if month_token is None:
        parts = [p.strip() for p in section.split(' - ') if p.strip()]
        if len(parts) >= 2:
            m2 = re.match(r'^([A-Za-z]+)\s+(\d{1,2})$', parts[1])
            if m2:
                month_token = m2.group(1).lower()
                day = int(m2.group(2))

    if month_token is None or day is None:
        return None

    month_lookup = {
        'jan': 1, 'january': 1,
        'feb': 2, 'february': 2,
        'mar': 3, 'march': 3,
        'apr': 4, 'april': 4,
        'may': 5,
        'jun': 6, 'june': 6,
        'jul': 7, 'july': 7,
        'aug': 8, 'august': 8,
        'sep': 9, 'sept': 9, 'september': 9,
        'oct': 10, 'october': 10,
        'nov': 11, 'november': 11,
        'dec': 12, 'december': 12,
    }
    month = month_lookup.get(month_token)
    if not month:
        return None

    year = now.year
    try:
        dt = datetime(year, month, day, tzinfo=TZ)
    except ValueError:
        return None

    # if date already passed by > 45 days, likely next year rollover
    if dt < now - timedelta(days=45):
        try:
            dt = datetime(year + 1, month, day, tzinfo=TZ)
        except ValueError:
            return None

    return dt


def parse_time_label(label: str) -> Optional[time]:
    s = label.strip().upper()
    if s == 'NOON':
        return time(12, 0)
    m = re.match(r'^(\d{1,2}):(\d{2})\s*(AM|PM)$', s)
    if not m:
        return None
    hh, mm, ap = int(m.group(1)), int(m.group(2)), m.group(3)
    if hh == 12:
        hh = 0
    if ap == 'PM':
        hh += 12
    return time(hh, mm)


def normalize_phone(phone: str) -> str:
    digits = re.sub(r'\D+', '', phone)
    if len(digits) == 10:
        return '+1' + digits
    if len(digits) == 11 and digits.startswith('1'):
        return '+' + digits
    if phone.startswith('+'):
        return phone
    return '+' + digits if digits else phone


def load_state() -> dict:
    if not STATE_PATH.exists():
        return {'sent': {}}
    try:
        return json.loads(STATE_PATH.read_text())
    except Exception:
        return {'sent': {}}


def save_state(state: dict):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2) + '\n')


def clamp_quiet_hours(dt: datetime) -> datetime:
    start = dt.replace(hour=8, minute=0, second=0, microsecond=0)
    end = dt.replace(hour=20, minute=30, second=0, microsecond=0)
    if dt < start:
        return start
    if dt > end:
        return end
    return dt


def is_revelation_label(label: str) -> bool:
    """Check if the label is a Revelation chapter (e.g., 'Revelation 12')."""
    return 'revelation' in label.lower()


def parse_revelation_chapter(label: str) -> Optional[int]:
    """Extract chapter number from label like 'Revelation 12'."""
    match = re.search(r'revelation\s*(\d+)', label.lower())
    if match:
        return int(match.group(1))
    return None


def build_composite_message(first: str, start_dt: datetime, end_dt: datetime, 
                           is_revelation: bool = False, chapters: list = None):
    """Build a composite message for consecutive reading slots.
    
    For time-based slots: "You're scheduled to read from X AM to Y AM"
    For Revelation chapters: "You're scheduled to read Revelation 12-14"
    """
    if is_revelation and chapters:
        # Build Revelation range message
        if len(chapters) == 1:
            chapter_text = f"Revelation {chapters[0]}"
        else:
            chapter_text = f"Revelation {min(chapters)}-{max(chapters)}"
        
        message = (
            f"Hi {first}! You're scheduled to read {chapter_text}. "
            f"Thank you for serving 🙏\n{CHURCH_FOOTER}"
        )
    else:
        # Time-based message
        start_time = start_dt.strftime('%-I:%M %p')
        end_time = end_dt.strftime('%-I:%M %p')
        
        message = (
            f"Hi {first}! You're scheduled to read Scripture from {start_time} to {end_time}. "
            f"Thank you for serving 🙏\n{CHURCH_FOOTER}"
        )
    return message


def group_consecutive_slots(slots):
    """
    Group slots by person, then group consecutive timeslots.
    Consecutive means: same person in consecutive rows (next row has different name = gap).
    Returns list of (person_key, [(slot, reading_dt), ...]) groups.
    Also returns a set of Revelation row numbers.
    """
    from collections import defaultdict
    
    # First, calculate reading_dt for each slot
    now = datetime.now(TZ)
    slots_with_times = []
    revelation_rows = set()  # Track which rows are Revelation chapters
    
    for s in slots:
        section_date = parse_date_from_section(s.section, now)
        slot_time = parse_time_label(s.label)
        
        # Check if this is a Revelation entry (no time, but has chapter in label)
        is_revelation = is_revelation_label(s.label)
        
        if is_revelation:
            # Revelation chapters: assign default time of 9:30 AM (church service)
            slot_time = time(9, 30)
            revelation_rows.add(s.row)
        
        if not section_date or not slot_time:
            continue
        reading_dt = section_date.replace(hour=slot_time.hour, minute=slot_time.minute)
        slots_with_times.append((s, reading_dt))
    
    # Sort by row (preserve order from sheet = chronological)
    slots_with_times.sort(key=lambda x: x[0].row)
    
    # Build a lookup for next slot's time by row number
    row_to_next_time = {}
    for i in range(len(slots_with_times) - 1):
        current_slot, current_dt = slots_with_times[i]
        next_slot, next_dt = slots_with_times[i + 1]
        row_to_next_time[current_slot.row] = next_dt
    
    # Group by person (first + last + phone)
    person_slots = defaultdict(list)
    for s, reading_dt in slots_with_times:
        key = (s.first.lower(), s.last.lower(), s.phone)
        person_slots[key].append((s, reading_dt))
    
    # Now group consecutive slots for each person
    # Consecutive = same person in consecutive rows (check if next row has different person)
    composite_groups = []
    for person_key, person_slots_list in person_slots.items():
        # Sort by reading_dt
        person_slots_list.sort(key=lambda x: x[1])
        
        # Group consecutive slots
        current_group = [person_slots_list[0]]
        for i in range(1, len(person_slots_list)):
            prev_slot, prev_dt = current_group[-1]
            curr_slot, curr_dt = person_slots_list[i]
            
            # Check if current slot is immediately after previous (consecutive rows)
            if curr_slot.row == prev_slot.row + 1:
                # Same person in next row - consecutive
                current_group.append((curr_slot, curr_dt))
            else:
                # Gap - save current group and start new one
                composite_groups.append(current_group)
                current_group = [(curr_slot, curr_dt)]
        
        # Don't forget the last group
        if current_group:
            composite_groups.append(current_group)
    
    return composite_groups, row_to_next_time, revelation_rows


def send_sms(phone: str, message: str):
    subprocess.run([str(SEND_SCRIPT), phone, message], check=True)


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    now = datetime.now(TZ)
    svc = sheets_service()
    vals = svc.spreadsheets().values().get(
        spreadsheetId=SHEET_ID,
        range=f'{SHEET_NAME}!A1:D2000'
    ).execute().get('values', [])

    slots = []
    section = ''
    for i, row in enumerate(vals, start=1):
        a = (row[0] if len(row) > 0 else '').strip()
        b = (row[1] if len(row) > 1 else '').strip()
        c = (row[2] if len(row) > 2 else '').strip()
        d = (row[3] if len(row) > 3 else '').strip()
        if not a:
            continue
        is_section = (' - ' in a) and ('First Name' in b)
        if is_section:
            section = a
            continue
        if (b or c or d):
            slots.append(Slot(i, section, a, b, c, d))

    state = load_state()
    sent = state.setdefault('sent', {})

    # Group consecutive slots by person, also get next-slot lookup
    composite_groups, row_to_next_time, revelation_rows = group_consecutive_slots(slots)
    
    # Debug: print groups
    for group in composite_groups:
        first_slot, first_dt = group[0]
        last_slot, last_dt = group[-1]
        print(f"Group: {first_slot.first} {first_slot.last} - {len(group)} slots, from {first_dt}")

    sends = []
    for group in composite_groups:
        first_slot, first_dt = group[0]
        last_slot, last_dt = group[-1]
        
        # Check if this is a Revelation reading (using the pre-computed set)
        is_revelation = first_slot.row in revelation_rows
        chapters = [parse_revelation_chapter(s.label) for s, _ in group]
        chapters = [c for c in chapters if c is not None]
        
        # Calculate actual END time:
        # If there's a next row on the SAME DATE, use that time as end
        # Otherwise, estimate based on 30 min per slot
        use_estimated = True
        if last_slot.row in row_to_next_time:
            next_dt = row_to_next_time[last_slot.row]
            # Only use next row's time if it's on the same date
            if next_dt.date() == last_dt.date():
                actual_end_dt = next_dt
                use_estimated = False
        
        if use_estimated:
            # Estimate based on 30 min per slot
            actual_end_dt = last_dt + timedelta(minutes=30 * len(group))
        
        # Skip if all slots are in the past
        if actual_end_dt < now - timedelta(hours=3):
            continue
        
        # Calculate reminder times
        if is_revelation:
            # Revelation: night before at 6 PM, day of at 8:30 AM (1 hour before 9:30 AM service)
            primary_dt = (first_dt - timedelta(days=1)).replace(hour=18, minute=0, second=0, microsecond=0)
            final_dt = first_dt.replace(hour=8, minute=30, second=0, microsecond=0)
        else:
            # Regular slots: night before at 6 PM (afternoon slots) or 9 AM (morning slots), 1 hour before
            primary_dt = (
                (first_dt - timedelta(days=1)).replace(hour=18, minute=0, second=0, microsecond=0)
                if first_dt.hour < 12
                else first_dt.replace(hour=9, minute=0, second=0, microsecond=0)
            )
            final_dt = first_dt - timedelta(hours=1)

        primary_dt = clamp_quiet_hours(primary_dt)
        final_dt = clamp_quiet_hours(final_dt)

        # Build composite message: "from X AM to Y AM" or "Revelation 12-14"
        composite_msg = build_composite_message(
            first_slot.first, first_dt, actual_end_dt, 
            is_revelation=is_revelation, chapters=chapters
        )

        # Use first slot's row as identifier for this group
        group_key = f"{first_slot.row}-{last_slot.row}"
        
        for kind, when_dt, text in (
            ('primary', primary_dt, composite_msg),
            ('final_1h', final_dt, composite_msg),
        ):
            key = f"{group_key}|{first_dt.isoformat()}|{kind}"
            if key in sent:
                continue
            if now >= when_dt and now <= when_dt + timedelta(minutes=20):
                sends.append((key, normalize_phone(first_slot.phone), text))

    for key, phone, text in sends:
        try:
            if args.dry_run:
                print(f'DRY_RUN {phone} {key} :: {text[:120]}')
            else:
                send_sms(phone, text)
                sent[key] = now.isoformat()
                print(f'SENT {phone} {key}')
        except Exception as e:
            print(f'ERROR {phone} {key} {e}')

    save_state(state)
    print(f'DONE sent_count={len(sends)}')


if __name__ == '__main__':
    main()
