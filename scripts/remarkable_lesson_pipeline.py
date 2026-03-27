#!/usr/bin/env python3
"""
Deterministic reMarkable lesson pipeline.

Input: JSON on stdin from after_lesson_full_routine.py
Output: progress/status text for cron announcements.

Codified rules:
- Trigger export from notebook view with Cmd+E
- Save destination must be ~/Downloads/reMarkable
- Post-export selection picks highest page-number PNG (not newest timestamp)
- Upload selected artifacts to Drive Lessons/<Student>/<YYYY MM Month DD>/
- Send update when supported (email via AgentMail). iMessage route is surfaced as pending
  when no local sender implementation is configured.
"""

from __future__ import annotations

import json
import mimetypes
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

try:
    from Quartz.CoreGraphics import (
        CGEventCreateMouseEvent,
        CGEventPost,
        kCGEventLeftMouseDown,
        kCGEventLeftMouseUp,
        kCGEventMouseMoved,
        kCGHIDEventTap,
    )
    HAS_QUARTZ = True
except Exception:
    HAS_QUARTZ = False

EXPORT_ROOT = Path.home() / "Downloads" / "reMarkable"
WORKSPACE = Path("/Users/ryantaylorvegh/.openclaw/workspace")
GOOGLE_ENV = WORKSPACE / ".secrets" / "google_sheets & drive.env"
AGENTMAIL_ENV = WORKSPACE / ".secrets" / "agentmail.env"
LESSONS_ROOT_FOLDER_ID = "1VtnKoXBgM2m3Y9RIzW4hHPflDu5dP5-J"
APPROVAL_TELEGRAM_TARGET = os.environ.get("LESSON_APPROVAL_TELEGRAM_TARGET", "8557709372").strip()
APPROVAL_TELEGRAM_ACCOUNT = os.environ.get("LESSON_APPROVAL_TELEGRAM_ACCOUNT", "").strip()

TZ = ZoneInfo("America/Detroit")


def _target_date(payload: dict | None = None) -> date:
    payload = payload or {}
    raw = (payload.get("targetDate") or os.environ.get("LESSON_TARGET_DATE") or "").strip()
    if raw:
        return date.fromisoformat(raw)
    return datetime.now(TZ).date()


def _target_datetime(payload: dict | None = None) -> datetime:
    target = _target_date(payload)
    current = datetime.now(TZ)
    return datetime.combine(target, current.timetz(), TZ)


@dataclass
class Contact:
    email: Optional[str] = None
    text_phone: Optional[str] = None
    text_via: Optional[str] = None  # "imessage-appscript"


CONTACTS: dict[str, Contact] = {
    "evan stein": Contact(email="steinevan1123@gmail.com"),
    "eric v": Contact(email="er841ra@gmail.com"),
    "eric": Contact(email="er841ra@gmail.com"),  # Fallback for first-name-only match
    "mike laukaitis": Contact(email="Mikelaukaitis55@gmail.com", text_phone="+16166342992", text_via="imessage-appscript"),
    "mike l": Contact(email="Mikelaukaitis55@gmail.com", text_phone="+16166342992", text_via="imessage-appscript"),
    "greg": Contact(text_phone="+16164859599", text_via="imessage-appscript"),
    "joy vegh": Contact(email="888lvegh@gmail.com"),
    "caleb": Contact(email="foxmail49316@aol.com"),
    "mandy": Contact(email="foxmail49316@aol.com"),
    "david": Contact(email="saitehmuntlang@gmail.com"),
    "jonathan": Contact(email="saitehmuntlang@gmail.com"),
    "henry": Contact(email="saitehmuntlang@gmail.com"),
}


def _load_env(path: Path) -> dict[str, str]:
    vals: dict[str, str] = {}
    if not path.exists():
        return vals
    for raw in path.read_text().splitlines():
        s = raw.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        vals[k.strip()] = v.strip().strip('"').strip("'")
    return vals


def run_osascript(script: str) -> None:
    subprocess.run(["osascript", "-e", script], check=False)


def move_path_to_trash(path: Path) -> None:
    # Move item to macOS Trash (recoverable), do not permanently delete.
    p = str(path).replace('"', '\\"')
    script = f'''
    tell application "Finder"
        delete POSIX file "{p}"
    end tell
    '''
    out = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, check=False)
    if out.returncode != 0:
        raise RuntimeError((out.stderr or out.stdout or "failed to move to Trash").strip())


def _extract_page(name: str) -> int:
    page = -1
    m = re.search(r"(?:page\s*|p)(\d+)", name)
    if not m:
        m = re.search(r"(?:_|-|\s)(\d+)$", name)
    if m:
        page = int(m.group(1))
    return page


def _matching_pngs(student_hint: str) -> list[Path]:
    if not EXPORT_ROOT.exists():
        return []
    token = student_hint.lower().strip()
    token_first = token.split()[0] if token else ""
    out: list[Path] = []
    for p in EXPORT_ROOT.rglob("*.png"):
        name = p.stem.lower()
        if token_first and token_first not in name:
            continue
        out.append(p)
    return out


def select_highest_page_png(student_hint: str) -> Path | None:
    candidates = _matching_pngs(student_hint)
    if not candidates:
        return None
    scored = [(_extract_page(p.stem.lower()), p) for p in candidates]
    scored = [x for x in scored if x[0] >= 0]
    if not scored:
        return None
    scored.sort(key=lambda t: t[0])
    return scored[-1][1]


def _normalize_text(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", s.lower())).strip()


def _remarkable_window_bounds() -> tuple[int, int, int, int] | None:
    script = '''
    tell application "System Events"
        tell process "reMarkable"
            if (count of windows) = 0 then return ""
            set {xPos, yPos} to position of window 1
            set {wSize, hSize} to size of window 1
            return (xPos as text) & "," & (yPos as text) & "," & (wSize as text) & "," & (hSize as text)
        end tell
    end tell
    '''
    out = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, check=False)
    raw = (out.stdout or "").strip()
    if not raw:
        return None
    try:
        x, y, w, h = [int(v.strip()) for v in raw.split(",")]
        return x, y, w, h
    except Exception:
        return None


def _ocr_hits_for_query(image_path: Path, query: str) -> list[tuple[int, int]]:
    # Returns hit centers in window-relative coordinates.
    cmd = ["tesseract", str(image_path), "stdout", "tsv"]
    out = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if out.returncode != 0 or not out.stdout:
        return []

    lines = out.stdout.splitlines()
    if len(lines) < 2:
        return []

    query_norm = _normalize_text(query)
    query_words = [w for w in query_norm.split(" ") if w]
    if not query_words:
        return []

    words: list[dict] = []
    for row in lines[1:]:
        cols = row.split("\t")
        if len(cols) < 12:
            continue
        text = cols[11].strip()
        if not text:
            continue
        try:
            left, top, width, height = map(int, cols[6:10])
        except Exception:
            continue
        norm = _normalize_text(text)
        if not norm:
            continue
        words.append({"text": text, "norm": norm, "left": left, "top": top, "width": width, "height": height})

    hits: list[tuple[int, int]] = []

    # Prefer full-name sequence matches within OCR word stream.
    norms = [w["norm"] for w in words]
    for i in range(0, max(0, len(words) - len(query_words) + 1)):
        if norms[i : i + len(query_words)] == query_words:
            seg = words[i : i + len(query_words)]
            left = min(w["left"] for w in seg)
            top = min(w["top"] for w in seg)
            right = max(w["left"] + w["width"] for w in seg)
            bottom = max(w["top"] + w["height"] for w in seg)
            hits.append(((left + right) // 2, (top + bottom) // 2))

    # Fallback: single-token (first name) matches.
    if not hits and query_words:
        first = query_words[0]
        for w in words:
            if w["norm"] == first:
                hits.append((w["left"] + w["width"] // 2, w["top"] + w["height"] // 2))

    return hits


def _click_screen_point(x: int, y: int) -> None:
    # Require Quartz for reliable visible pointer movement/click on macOS.
    if not HAS_QUARTZ:
        raise RuntimeError("Quartz not available in this Python runtime; cannot perform reliable UI click automation")

    CGEventPost(kCGHIDEventTap, CGEventCreateMouseEvent(None, kCGEventMouseMoved, (x, y), 0))
    time.sleep(0.2)
    CGEventPost(kCGHIDEventTap, CGEventCreateMouseEvent(None, kCGEventLeftMouseDown, (x, y), 0))
    CGEventPost(kCGHIDEventTap, CGEventCreateMouseEvent(None, kCGEventLeftMouseUp, (x, y), 0))


def search_student_notebook(student_hint: str) -> None:
    escaped = student_hint.replace('"', '\\"')
    # Simpler proven flow from user: search -> Down Arrow selects notebook result -> Enter opens it.
    script = f'''
    tell application "System Events"
        keystroke "f" using command down
        delay 0.15
        keystroke "a" using command down
        key code 51
        keystroke "{escaped}"
        delay 0.25
        key code 125 -- down arrow (select first notebook result)
        delay 0.15
        key code 36 -- return/open
    end tell
    '''
    run_osascript(script)
    time.sleep(0.45)


def complete_export_dialog() -> None:
    # Order per confirmed working flow:
    # 1) click PNG
    # 2) click Export
    # 3) in save dialog, choose reMarkable folder
    # 4) click "Place folder here"

    # Wait briefly for export dialog to be present.
    time.sleep(0.6)

    # 1) Prefer semantic click on PNG control; fallback to calibrated point.
    run_osascript('''
    tell application "System Events"
        tell process "reMarkable"
            repeat with w in windows
                try
                    if exists (first radio button of w whose name is "PNG") then
                        click (first radio button of w whose name is "PNG")
                        return
                    end if
                end try
                try
                    if exists (first button of w whose name is "PNG") then
                        click (first button of w whose name is "PNG")
                        return
                    end if
                end try
            end repeat
        end tell
    end tell
    ''')
    # Fallback calibrated click point (from TOOLS.md)
    _click_screen_point(851, 590)
    time.sleep(0.3)

    # 2) Click Export button in dialog (name-first, no coordinate unless fallback needed)
    export_clicked = False
    check = subprocess.run([
        "osascript",
        "-e",
        '''
        tell application "System Events"
            tell process "reMarkable"
                repeat with w in windows
                    try
                        if exists (first button of w whose name is "Export") then
                            click (first button of w whose name is "Export")
                            return "ok"
                        end if
                    end try
                end repeat
            end tell
        end tell
        return "miss"
        ''',
    ], capture_output=True, text=True, check=False)
    if (check.stdout or "").strip() == "ok":
        export_clicked = True

    if not export_clicked:
        # Fallback only: press Return to activate default button.
        run_osascript('tell application "System Events" to key code 36')

    time.sleep(0.6)

    # 3) Save dialog: choose reMarkable sidebar row (calibrated point from TOOLS.md)
    _click_screen_point(546, 581)
    time.sleep(0.2)

    # 4) Confirm destination with "Place folder here"
    run_osascript('''
    tell application "System Events"
        repeat 2 times
            keystroke return
            delay 0.15
        end repeat
        try
            tell process "reMarkable"
                repeat with w in windows
                    try
                        if exists (first button of w whose name is "Place folder here") then
                            click (first button of w whose name is "Place folder here")
                            exit repeat
                        end if
                    end try
                end repeat
            end tell
        end try
    end tell
    ''')


def wait_for_new_export(student_hint: str, before: set[str], timeout_sec: int = 45) -> Path | None:
    """
    Wait for export to complete by polling the export folder.
    Detects stabilization: waits until highest page number stays same for 2+ seconds.
    Returns the highest-page PNG, or None if timeout.
    """
    deadline = time.time() + timeout_sec
    last_highest = -1
    stable_since = None
    
    while time.time() < deadline:
        current = _matching_pngs(student_hint)
        new_files = [p for p in current if str(p) not in before]
        
        if new_files:
            scored = [(_extract_page(p.stem.lower()), p) for p in new_files]
            scored = [x for x in scored if x[0] >= 0]
            if scored:
                scored.sort(key=lambda t: t[0])
                current_highest = scored[-1][0]
                
                # Check if highest page has stabilized (same for 2+ seconds)
                if current_highest == last_highest:
                    if stable_since is None:
                        stable_since = time.time()
                    elif time.time() - stable_since >= 2.0:
                        # Stabilized for 2 seconds - export is complete
                        return scored[-1][1]
                else:
                    # New highest - reset stability tracking
                    last_highest = current_highest
                    stable_since = None
        
        time.sleep(2.0)
    return None


def get_previous_lesson_page_number(svc, student_folder_id: str) -> int | None:
    """
    Find the most recent lesson folder (not today's) and return its highest page number.
    Returns None if no previous lesson found.
    """
    from datetime import datetime
    from zoneinfo import ZoneInfo
    import re
    
    TZ = ZoneInfo('America/Detroit')
    today_str = _target_datetime().strftime('%Y %m %B %d')
    
    # Get all date folders for this student
    result = svc.files().list(
        q=f"'{student_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false",
        fields='files(id,name)',
        pageSize=50
    ).execute()
    
    folders = result.get('files', [])
    
    # Find most recent folder that's not today
    max_page = None
    for folder in folders:
        folder_name = folder['name']
        if folder_name == today_str:
            continue  # Skip today's folder
        
        # Get files in this folder
        files_result = svc.files().list(
            q=f"'{folder['id']}' in parents and trashed=false",
            fields='files(name)',
            pageSize=50
        ).execute()
        
        for f in files_result.get('files', []):
            # Look for page PNGs
            m = re.search(r'page\s*(\d+)', f['name'], re.IGNORECASE)
            if m:
                page_num = int(m.group(1))
                if max_page is None or page_num > max_page:
                    max_page = page_num
    
    return max_page


def find_same_day_audio(student_hint: str) -> Path | None:
    d = Path.home() / "Downloads"
    if not d.exists():
        return None
    
    # Extract student name from lesson title (same logic as export_targets_for_student)
    import re
    m = re.search(r'with\s+(.+)$', student_hint, re.IGNORECASE)
    if m:
        name_part = m.group(1).strip()
        if "'s" in name_part:
            student_name = name_part.split(',')[-1].strip()  # "Caleb"
        else:
            student_name = name_part  # "Evan Stein" or "Mike L"
    else:
        student_name = student_hint
    
    # Use first word for audio matching (e.g., "caleb", "evan", "mike")
    token = student_name.split()[0].lower() if student_name else ""
    
    # Dynamic date markers
    from datetime import datetime
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo('America/Detroit')
    today = _target_datetime()
    date_markers = [
        today.strftime('%m-%d-%y').replace('-0', '-'),
        today.strftime('%Y-%m-%d'),
        today.strftime('%-m-%-d-%y'),
    ]
    for p in sorted(d.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
        if not p.is_file():
            continue
        n = p.name.lower()
        if token and token not in n:
            continue
        if not any(m in n for m in date_markers):
            continue
        if p.suffix.lower() in {".m4a", ".mp3", ".wav", ".aiff"}:
            return p
    return None


def drive_service():
    vals = _load_env(GOOGLE_ENV)
    creds = Credentials(
        token=vals.get("GOOGLE_SHEETS_ACCESS_TOKEN") or None,
        refresh_token=vals.get("GOOGLE_SHEETS_REFRESH_TOKEN"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=vals.get("GOOGLE_SHEETS_CLIENT_ID"),
        client_secret=vals.get("GOOGLE_SHEETS_CLIENT_SECRET"),
    )
    if not creds.valid:
        creds.refresh(Request())
    return build("drive", "v3", credentials=creds)


def _normalize_folder_name(name: str) -> str:
    return re.sub(r"\s+", " ", (name or "").strip()).casefold()


def _drive_list_kwargs() -> dict:
    return {
        "supportsAllDrives": True,
        "includeItemsFromAllDrives": True,
    }


def find_or_create_folder(svc, name: str, parent_id: Optional[str] = None, dry: bool = False) -> Optional[str]:
    canonical_name = re.sub(r"\s+", " ", (name or "").strip())
    if not canonical_name:
        return None

    # First try an exact-name query for speed.
    safe_name = canonical_name.replace("'", "\\'")
    q = ["mimeType='application/vnd.google-apps.folder'", f"name='{safe_name}'", "trashed=false"]
    if parent_id:
        q.append(f"'{parent_id}' in parents")
    resp = svc.files().list(
        q=" and ".join(q),
        fields="files(id,name,parents)",
        pageSize=10,
        **_drive_list_kwargs(),
    ).execute()
    files = resp.get("files", [])
    if files:
        return files[0]["id"]

    # Then do a normalized sibling scan to prevent duplicates caused by whitespace,
    # case differences, Drive query weirdness, or pre-existing human-made folders.
    if parent_id:
        page_token = None
        normalized_target = _normalize_folder_name(canonical_name)
        while True:
            resp = svc.files().list(
                q=(
                    "mimeType='application/vnd.google-apps.folder' and trashed=false "
                    f"and '{parent_id}' in parents"
                ),
                fields="nextPageToken, files(id,name,parents)",
                pageSize=1000,
                pageToken=page_token,
                **_drive_list_kwargs(),
            ).execute()
            for f in resp.get("files", []):
                if _normalize_folder_name(f.get("name", "")) == normalized_target:
                    return f["id"]
            page_token = resp.get("nextPageToken")
            if not page_token:
                break

    if dry:
        return None

    body = {"name": canonical_name, "mimeType": "application/vnd.google-apps.folder"}
    if parent_id:
        body["parents"] = [parent_id]
    created = svc.files().create(body=body, fields="id", supportsAllDrives=True).execute()
    return created["id"]


def upload_file(svc, path: Path, parent_id: str) -> str:
    mime = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
    media = MediaFileUpload(str(path), mimetype=mime, resumable=False)
    body = {"name": path.name, "parents": [parent_id]}
    f = svc.files().create(body=body, media_body=media, fields="id,name").execute()
    return f["id"]


def resolve_contact(student_hint: str) -> Contact:
    low = student_hint.lower().strip()
    for k, v in CONTACTS.items():
        if k in low:
            return v
    return Contact()


def export_targets_for_student(student: str) -> list[str]:
    low = student.lower().strip()
    # Joy/Mum workflow: export both Voice + Piano notebooks each run.
    if "joy" in low or low == "mum":
        return ["Mum-V", "Mum-P"]

    # Extract student name from lesson title patterns:
    # "Mandy F's son, Caleb" -> Caleb (pattern: "X's son, LASTNAME")
    # "Voice/Guitar with Evan Stein" -> Evan Stein
    # "Drums with Mike L" -> Mike L
    
    import re
    
    # Handle "X's son/daughter/kid, NAME" pattern - take last part after comma
    if re.search(r"'s\s+son", low) or re.search(r"'s\s+daughter", low) or re.search(r"'s\s+kid", low):
        if ',' in student:
            student_name = student.split(',')[-1].strip()  # "Caleb", "David", "Jonathan"
            return [student_name]
    
    # Find text after "with " (any lesson format like "Voice with X", "Drums with X")
    m = re.search(r'with\s+(.+)$', student, re.IGNORECASE)
    if m:
        name_part = m.group(1).strip()
        return [name_part]  # "Evan Stein" or "Mike L"
    
    # Fallback: return as-is
    return [student]


def drive_folder_name_for_student(student: str) -> str:
    low = student.lower().strip()
    if low in {"david", "jonathan"}:
        return "Jonathan and David"
    if "joy" in low or low == "mum":
        return "Mum"
    # Handle parent name patterns: "Mandy F's son, Caleb" -> "Caleb"
    if "son" in low and "caleb" in low:
        return "Caleb"
    return student


def _draft_only_enabled() -> bool:
    raw = os.environ.get("DRAFT_ONLY", "1").lower()
    return raw in ("1", "true", "yes")


def send_email_agentmail(to_email: str, subject: str, body: str) -> tuple[bool, str]:
    try:
        from agentmail import AgentMail  # type: ignore
    except Exception as e:
        return False, f"agentmail import failed: {e}"

    env = _load_env(AGENTMAIL_ENV)
    api_key = env.get("AGENTMAIL_API_KEY") or env.get("API_KEY")
    inbox = env.get("AGENTMAIL_FROM_INBOX") or "sallysquirrel@agentmail.to"
    if not api_key:
        return False, "missing AGENTMAIL_API_KEY"

    try:
        client = AgentMail(api_key=api_key)
        client.inboxes.messages.send(
            inbox_id=inbox,
            to=[to_email],
            subject=subject,
            text=body,
            cc=["ryan.vegh@gmail.com"],
        )
        return True, "sent"
    except Exception as e:
        return False, str(e)


def send_telegram_approval_draft(*, draft_label: str, to_email: str, subject: str, body: str) -> tuple[bool, str]:
    if not APPROVAL_TELEGRAM_TARGET:
        return False, "missing LESSON_APPROVAL_TELEGRAM_TARGET"

    message_text = (
        f"📧 LESSON EMAIL DRAFT\n"
        f"Draft: {draft_label}\n"
        f"To: {to_email}\n"
        f"CC: ryan.vegh@gmail.com\n"
        f"Subject: {subject}\n\n"
        f"{body}\n\n"
        f"Approve/edit this draft before sending."
    )

    cmd = [
        "openclaw",
        "message",
        "send",
        "--channel",
        "telegram",
        "--target",
        APPROVAL_TELEGRAM_TARGET,
        "--message",
        message_text,
    ]
    if APPROVAL_TELEGRAM_ACCOUNT:
        cmd.extend(["--account", APPROVAL_TELEGRAM_ACCOUNT])

    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode == 0:
        return True, "telegram draft sent"

    rendered = " ".join(shlex.quote(part) for part in cmd)
    detail = (proc.stderr or proc.stdout or f"exit {proc.returncode}").strip()
    return False, f"telegram send failed via `{rendered}`: {detail}"


def main() -> int:
    payload = json.loads(sys.stdin.read() or "{}")
    eligible = payload.get("eligible", [])
    target_dt = _target_datetime(payload)
    if not eligible:
        print("NO_ACTION")
        return 0

    print("STEP 3 policy: use Cmd+E for export from notebook view")
    print("STEP 3 policy: save destination must be ~/Downloads/reMarkable")

    # Ensure reMarkable is the active window before any typing/clicking
    print("STEP 3: activating reMarkable window...")
    run_osascript('tell application "reMarkable" to activate')
    time.sleep(0.5)

    svc = drive_service()
    root_lessons_id = LESSONS_ROOT_FOLDER_ID
    date_folder_name = target_dt.strftime("%Y %m %B %d")

    STOP_FILE = Path.home() / ".openclaw" / "stop_lesson_pipeline"

    def _check_stop() -> bool:
        if STOP_FILE.exists():
            print("[STOP_REQUESTED] Stop file detected, aborting gracefully")
            try:
                STOP_FILE.unlink()
            except Exception:
                pass
            return True
        return False

    processed = []
    blocked = []
    henry_children_done: dict[str, dict] = {}

    for item in eligible:
        if _check_stop():
            print("STOPPED before completing remaining students")
            break

        student = (item.get("studentHint") or "").strip()
        kind = item.get("kind") or "other"

        # Check if already processed today (dated folder with required files already exists).
        folder_owner_name = drive_folder_name_for_student(student)
        existing_student_folder = find_or_create_folder(svc, folder_owner_name, root_lessons_id, dry=True)
        skip_reason = None
        if existing_student_folder:
            existing_dated_folder = find_or_create_folder(svc, date_folder_name, existing_student_folder, dry=True)
            if existing_dated_folder:
                existing_files = svc.files().list(
                    q=f"trashed=false and '{existing_dated_folder}' in parents",
                    fields="files(id,name,mimeType)",
                    pageSize=50
                ).execute().get("files", [])
                if existing_files:
                    # DEBUG
                    # Check what files are present
                    student_token = student.lower().strip()
                    has_audio = any(f.get('name', '').lower().endswith(('.m4a', '.mp3', '.wav', '.aiff')) for f in existing_files)
                    has_image = any(f.get('name', '').lower().endswith('.png') for f in existing_files)
                    has_student_image = any(
                        f.get('name', '').lower().endswith('.png') and student_token in f.get('name', '').lower()
                        for f in existing_files
                    )

                    if kind == 'voice':
                        # Voice lessons need BOTH audio AND this student's PNG
                        if has_audio and has_student_image:
                            skip_reason = f"already has audio + student PNG ({len(existing_files)} files)"
                        elif has_audio:
                            skip_reason = None  # Don't skip - missing student PNG
                        else:
                            skip_reason = f"no files yet"
                    else:
                        # Drum lessons only count as done if this student's PNG exists.
                        if has_student_image:
                            skip_reason = f"already has student PNG ({len(existing_files)} files)"
                        else:
                            skip_reason = None  # Don't skip - missing this student's PNG

                    if skip_reason:
                        print(f"[SKIP_ALREADY_DONE] {student}: {skip_reason}, skipping")
                        continue

        if _check_stop():
            print("STOPPED before starting export for {student}")
            break

        # Get previous lesson's page number for comparison
        folder_owner_name = drive_folder_name_for_student(student) or "Unknown Student"
        existing_student_folder = find_or_create_folder(svc, folder_owner_name, root_lessons_id, dry=True)
        previous_page = None
        if existing_student_folder:
            previous_page = get_previous_lesson_page_number(svc, existing_student_folder)
            if previous_page:
                print(f"STEP 3: Previous lesson had page {previous_page}")

        export_targets = export_targets_for_student(student)
        picked_files: list[Path] = []

        for target in export_targets:
            if target != student:
                print(f"STEP 3 export: NOTE: using '{target}' notebook for '{student}'")
            else:
                print(f"STEP 3 export: searching notebook for '{target}'")

            search_student_notebook(target)
            before_set = {str(p) for p in _matching_pngs(target)}

            # Trigger export dialog/action from notebook view, then complete dialog flow.
            run_osascript('tell application "System Events" to keystroke "e" using command down')
            time.sleep(0.35)
            complete_export_dialog()

            picked = wait_for_new_export(target, before_set, timeout_sec=120)
            if not picked:
                blocked.append(
                    f"{student}: no NEW exported PNG detected for notebook '{target}' after Cmd+E. "
                    f"Likely blocked in export dialog (PNG/Export click or save step not completed)."
                )
                picked_files = []
                break
            
            # Check if this page is newer than previous lesson
            # Only compare if there's already a folder for TODAY (skip comparison for new lessons)
            existing_dated_folder = find_or_create_folder(svc, date_folder_name, existing_student_folder, dry=True) if existing_student_folder else None
            current_page = _extract_page(picked.stem.lower())
            if existing_dated_folder and previous_page is not None and current_page <= previous_page:
                print(f"[SKIP] {student}: current page {current_page} <= previous page {previous_page}. No new lesson.")
                picked_files = []
                break
            elif not existing_dated_folder:
                print(f"STEP 3: New lesson folder for today, uploading page {current_page}")
                
            picked_files.append(picked)

        # Wait for files to fully write to disk before upload
        time.sleep(3.0)

        if not picked_files:
            continue

        # Special Drive grouping rule: David + Jonathan share one parent folder.
        folder_owner_name = drive_folder_name_for_student(student) or "Unknown Student"
        student_folder_id = find_or_create_folder(svc, folder_owner_name, root_lessons_id)
        dated_folder_id = find_or_create_folder(svc, date_folder_name, student_folder_id)

        uploaded = [p.name for p in picked_files]
        for p in picked_files:
            upload_file(svc, p, dated_folder_id)

        audio_path = None
        if kind == "voice":
            # Check if audio already exists in Drive before uploading
            existing_files = svc.files().list(
                q=f"'{dated_folder_id}' in parents and trashed=false",
                fields='files(name)'
            ).execute().get('files', [])
            existing_audio = {f.get('name', '').lower() for f in existing_files}
            
            audio_path = find_same_day_audio(student)
            if audio_path:
                # Skip upload if audio with similar name already exists
                audio_name_lower = audio_path.name.lower()
                if any(audio_name_lower[:10] in ex for ex in existing_audio):
                    print(f"[SKIP] {student}: audio already exists in Drive, skipping upload")
                else:
                    upload_file(svc, audio_path, dated_folder_id)
                    uploaded.append(audio_path.name)

        # Pre-email check for voice lessons: ensure both PNG and audio exist in Drive
        if kind == "voice":
            folder_files = svc.files().list(
                q=f"'{dated_folder_id}' in parents and trashed=false",
                fields='files(name,mimeType)'
            ).execute().get('files', [])
            
            has_png = any(f.get('name', '').lower().endswith('.png') for f in folder_files)
            has_audio = any(f.get('name', '').lower().endswith(('.m4a', '.mp3', '.wav', '.aiff')) for f in folder_files)
            
            if not has_png:
                print(f"[WARN] {student}: PNG missing in Drive folder, skipping email")
                continue
            if not has_audio:
                print(f"[WARN] {student}: audio missing in Drive folder, skipping email")
                continue
            print(f"[OK] {student}: both PNG and audio present in Drive folder")

        contact = resolve_contact(student)
        send_status = "no-recipient"
        recipient = None

        # Special gate: Henry update must include BOTH David + Jonathan links in one email.
        if student.lower() in {"david", "jonathan"}:
            drive_link = f"https://drive.google.com/drive/folders/{dated_folder_id}"
            henry_children_done[student.lower()] = {
                "student": student,
                "folderId": dated_folder_id,
                "driveLink": drive_link,
                "uploaded": uploaded,
            }
            send_status = "deferred: waiting for both David + Jonathan before Henry email"
            recipient = "saitehmuntlang@gmail.com"
        elif contact.email:
            recipient = contact.email
            subject = ("Voice Lesson" if kind == "voice" else "Drum Lessons") + " -- " + target_dt.strftime("%m-%d-%y")
            intro = (
                f"Ryan's voice lesson notes and lesson recording have been uploaded for {student}."
                if kind == "voice"
                else f"Ryan's lesson notes have been uploaded for {student}."
            )
            body = (
                f"Hi,\n\n"
                f"{intro}\n"
                f"Files uploaded: {', '.join(uploaded)}\n"
                f"Drive folder: https://drive.google.com/drive/folders/{dated_folder_id}\n\n"
                f"Best,\nSally, Ryan’s assistant"
            )
            if _draft_only_enabled():
                ok, detail = send_telegram_approval_draft(
                    draft_label=f"{student} ({kind})",
                    to_email=contact.email,
                    subject=subject,
                    body=body,
                )
                send_status = (
                    f"DRAFT_ONLY telegram:{'ok' if ok else 'failed'} ({detail})"
                )
                print(send_status)
            else:
                ok, detail = send_email_agentmail(contact.email, subject, body)
                send_status = f"email:{'ok' if ok else 'failed'} ({detail})"
        elif contact.text_phone:
            recipient = contact.text_phone
            send_status = "text-pending (iMessage Apps Script integration not yet wired in this script)"

        # Cleanup local exported artifacts after successful Drive upload.
        cleanup_notes: list[str] = []
        for picked in picked_files:
            try:
                if picked.exists():
                    move_path_to_trash(picked)
                    cleanup_notes.append(f"trashed:{picked.name}")
            except Exception as e:
                cleanup_notes.append(f"trash-failed:{picked.name}:{e}")

        # Voice workflow: move matching source audio from Downloads to Trash after successful upload.
        if kind == "voice" and audio_path is not None:
            try:
                if audio_path.exists():
                    move_path_to_trash(audio_path)
                    cleanup_notes.append(f"trashed-audio:{audio_path.name}")
            except Exception as e:
                cleanup_notes.append(f"trash-audio-failed:{audio_path.name}:{e}")

        # Move matching student folder under Downloads/reMarkable to Trash after successful upload.
        try:
            for student_export_dir in {p.parent for p in picked_files}:
                if student_export_dir.exists() and student_export_dir != EXPORT_ROOT:
                    move_path_to_trash(student_export_dir)
                    cleanup_notes.append(f"trashed-dir:{student_export_dir.name}")
        except Exception as e:
            cleanup_notes.append(f"trash-dir-failed:{e}")

        processed.append(
            {
                "student": student,
                "kind": kind,
                "pickedPng": ", ".join(str(p) for p in picked_files),
                "uploaded": uploaded,
                "recipient": recipient,
                "sendStatus": send_status,
                "cleanup": cleanup_notes,
            }
        )

    # Send combined Henry update only when BOTH kids completed.
    if "david" in henry_children_done and "jonathan" in henry_children_done:
        david = henry_children_done["david"]
        jon = henry_children_done["jonathan"]
        subject = "Drum Lessons -- " + target_dt.strftime("%m-%d-%y")
        body = (
            "Hi Henry,\n\n"
            "Here are this week’s drum lesson notes folder for David and Jonathan:\n"
            f"{david['driveLink']}\n\n"
            "Best,\nSally, Ryan’s assistant"
        )
        if _draft_only_enabled():
            ok, detail = send_telegram_approval_draft(
                draft_label="Henry (drum)",
                to_email="saitehmuntlang@gmail.com",
                subject=subject,
                body=body,
            )
            print(f"HENRY_EMAIL: drafted via telegram ({detail})" if ok else f"HENRY_EMAIL: telegram draft failed ({detail})")
        else:
            ok, detail = send_email_agentmail("saitehmuntlang@gmail.com", subject, body)
            print(f"HENRY_EMAIL: {'sent' if ok else 'failed'} ({detail})")
    elif henry_children_done:
        print("HENRY_EMAIL: deferred (waiting for both David + Jonathan exports)")

    if blocked and not processed:
        print("BLOCKED STEP 3:")
        for b in blocked:
            print(f"- {b}")
        return 2

    print("STEP 4-7 summary:")
    for row in processed:
        print(
            f"- {row['student']} ({row['kind']}): png={row['pickedPng']} | "
            f"uploaded={','.join(row['uploaded'])} | recipient={row['recipient']} | {row['sendStatus']} | "
            f"cleanup={';'.join(row.get('cleanup', []))}"
        )

    if blocked:
        print("PARTIAL BLOCKERS:")
        for b in blocked:
            print(f"- {b}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
