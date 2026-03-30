# MEMORY.md

## iPhone Shortcut Listener (Hey Sally)
- **Script:** `scripts/hey_sally_listener.py`
- **Token:** Stored in `.secrets/hey_sally_listener_token.env`
- **Port:** 18790
- **Protocol:** POST to `http://100.105.118.34:18790/sally`
  - Header: `X-Auth-Token` with the token value
  - Body (JSON): `{"text": "Your message here"}`
- **Current Session ID:** `26379dad-7feb-4721-8c9a-f31df3040970` (updated March 17, 2026)
- **Launchd:** Running as `com.openclaw.hey-sally-listener` (user agent)
- **Plist:** `~/Library/LaunchAgents/com.openclaw.hey-sally-listener.plist`
- **How it works:** Receives iPhone Shortcut messages via Tailscale, forwards to main OpenClaw session via `openclaw agent --message "..."`
- **Bug fix (Mar 14):** Fixed duplicate subprocess call that was causing double messages. Updated plist with env var for token.

## Email Integration (AgentMail)
- **Primary Provider:** AgentMail
- **Tooling:** Use `agentmail` skill for inbox management, sending, and programmatic access.
- **Workflow:** For regular email checks, use AgentMail's programmatic access.
- **Hard rule:** Never use Gmail. Never use the Mail app. For inbox access/checks, use AgentMail only.
- **Note:** Avoid Gmail OAuth workflows; AgentMail is the designated platform.
- **Critical:** The Python library (`agentmail` package) has bugs with send functionality — use direct `requests` calls instead:
  ```python
  import requests
  API_KEY = "am_us_..."
  INBOX_ID = "sallysquirrel@agentmail.to"
  resp = requests.post(
      f"https://api.agentmail.to/v0/inboxes/{INBOX_ID}/messages/send",
      headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
      json={"to": ["recipient@email.com"], "subject": "...", "text": "..."}
  )
  ```
- **Key fix (Mar 19):** The `/messages/send` endpoint works; the library was routing incorrectly.

## Google Workspace API Access
- **Credentials:** Stored in `.secrets/google_sheets & drive.env` (contains `GOOGLE_SHEETS_CLIENT_ID`, `GOOGLE_SHEETS_CLIENT_SECRET`, `GOOGLE_SHEETS_REFRESH_TOKEN`, etc.).
- **Access:** Can use these credentials for Google Drive and Google Docs API operations (OAuth2 flow with refresh token).
- **Usage:** Always use the credentials from the secret file when programmatically accessing Google Drive or Docs for editing documents or managing files.

## Script Execution Best Practices

- **Python Environment:** Always use `./venv/bin/python` to ensure all dependencies (e.g., `aiohttp`, `agentmail`) are available. Never use the system `python3`.
- **Credentials:** When running scripts that require sensitive tokens (e.g., Venmo, Email), inject the environment variable explicitly from the `.secrets/` files. 
  - Example: `env VENMO_ACCESS_TOKEN=$(grep access_token .secrets/venmo_creds.env | cut -d= -f2) ./venv/bin/python scripts/venmo_transactions.py transactions --limit 5`
- **Verify Tools:** If a tool like `gcal` or a Python module fails, check if the project-specific environment is being utilized first.

## Home Assistant
- **Deployment:** Running via Docker (`ghcr.io/home-assistant/home-assistant:stable`).
- **Configuration Path:** `/Users/ryantaylorvegh/.homeassistant` (mapped to `/config` in container).
- **HACS:** Installed in `/config/custom_components`.
- **Integrations:** Wyze integration installed (uses `wyzeapy`).
- **Devices:** `light.color_bulb_1`, `light.color_bulb_2`.
- **Active Automation:** "Master Bedroom Warm Setup" (`master_bedroom_warm_setup_12345` in `automations.yaml`).
  - *Current Status:* Manual trigger works; automatic state trigger (off->on) failing. Needs further debugging of entity state change detection.
- **iOS App URL:** `http://Ryans-M1---Fresh-Start.local:8123` (use if on same WiFi as Home Assistant container)
- **Docker Port:** 0.0.0.0:8123->8123/tcp

## Technical Debt / Next Steps
- **Calendar Tools:** `gcal` CLI tool missing; required for lesson automation check.
- **Automation Troubleshooting:** Trigger detection for Home Assistant bulbs not firing (state changes from "off" to "on" not registered).
- The PIER map project is in the `PIER-People` repository.
- Workflow rule for PIER map app edits: after each edit session, push changes to GitHub and deploy to Firebase.

## Ableton Integration Tools
- **AbletonMCP** — Installed, for controlling Ableton via MCP protocol
- **AbletonOSC** — Installed, OSC-based control
- **AbletonOSC-MCP** — Installed, OSC wrapped as MCP
- **Max for Live Ableton Bridge** — In progress. Adding features to allow more control than OSC and MCP tools alone allow.
- **Ableton iOS Remote app** — In development. Controlling Ableton Live from iOS device.

## Planning Center API
- **Token location:** Hardcoded in `~/.openclaw/workspace/scripts/pier_ableton_songs.py`
- **Auth method:** Use basic auth with `-u "id:token"` flag, NOT Bearer token header
- **Keys for songs:** Available in Planning Center API under song attributes

## MultiTracks
- **Tempo lookup:** Use browser relay to fetch from MultiTracks.com (no login required)

## Church Ableton Automation (Sunday Songs)
**Weekly workflow:**
1. Get song list + keys from Planning Center Online API
2. Get tempos from MultiTracks.com (via Browser Relay, no login required — search song, find tempo)
3. **Create proper Ableton Project Folder** (not just .als file) - copy from previous week
4. Update 5-6 song scenes:
   - Rename scene names (Main) with song names formatted like `* SONG NAME "3-WORD-SONG-NAME"`
   - Copy pad clips from the template's pads track (clips named by key, e.g., "C#m") into each scene's pad slot
   - Set tempo clips in each scene to match MultiTracks tempo
5. Save with Cmd+S (file already named so no dialog needed)

**Root cause fixes needed:**
- **Project folder structure**: Ableton requires .als files to live inside a "Project" folder with `Ableton Project Info/` subfolder and `Icon` file. Solution: copy previous week's project folder, rename it, delete old .als, copy in fresh template.
- **OSC timing**: The python-osc commands sometimes don't get responses in time. Solution: increase delays between OSC commands, verify each edit worked before proceeding.
- **Save workflow**: Open the destination file (already named), make edits, then Cmd+S saves in place without dialog.

**Template location:** Ableton Sunday Songs Template for OpenClaw — has multiple clips in the pads track with clip names matching key names.

## GitHub Repos
- PIER-People: `Neonotso/PIER-People`

## Monthly PIER Reports
- **Automation**: Monthly cron job runs `scripts/monthly_pier_report.py` on the 1st of each month.
- **Functionality**: Queries `backup_2026-03-13_v4.db` (decompressed GZIP SQLite) for "The PIER" project, calculates totals, creates formatted Excel (`PIER_Report_Month_Year.xlsx`), and emails to Dave Holtrop (CC Ryan).

## Excel Reporting Pipeline
- Scripts: `scripts/create_excel.py`, `scripts/send_excel_email.py`.
- Formats: Applies Arial/11pt, wraps text, bold headers/totals, auto-fits columns (max width 50), and formats times as AM/PM.

## Image Generation (ComfyUI)
- **Location:** ~/.openclaw/workspace/ComfyUI
- **Port:** 8188 (API mode)
- **Model:** juggernautXL_v8Rundiffusion.safetensors (linked from Fooocus models)
- **Workflow nodes:** CheckpointLoaderSimple → CLIPTextEncode (positive) → CLIPTextEncode (negative) → EmptyLatentImage → KSampler → VAEDecode → SaveImage
- **How to generate:** POST JSON to http://localhost:8188/prompt
- **Output:** ~/.openclaw/workspace/ComfyUI/output/
- **Save location:** /Users/ryantaylorvegh/Library/CloudStorage/Dropbox/Slides Images/
- **Note:** Fooocus is Gradio-only (no API), ComfyUI is better for automation

## Lesson Automation Pipeline (March 2026)

### Scripts
- `scripts/after_lesson_full_routine.py` - Trigger detection + calls downstream
- `scripts/remarkable_lesson_pipeline.py` - Export, upload, email

### Student Name Extraction (CRITICAL)
The pipeline extracts student names from calendar event titles:
- "Voice with Mandy F's son, Caleb" → Caleb (last token after comma)
- "Voice/Guitar with Evan Stein" → Evan Stein (full name after "with")
- "Drums with Mike L" → Mike L (full name after "with")

**Bug fix (Mar 17):** Date markers and name extraction were hardcoded. Now dynamically extracts name using regex.

### reMarkable Export
- Export timeout increased to 90 seconds
- May need manual export if automation fails

### Email Mode
- Set `DRAFT_ONLY=1` to draft emails instead of sending automatically

## Home Assistant
- **Preference**: Docker installation (pending).

**Spreadsheet:** "Monthly Budget" - https://docs.google.com/spreadsheets/d/1Eg5hKm2xSDf6-mEYYG9pR1X7kFtiO6C5jeRO4zDzw90

**Credentials:** Stored in `.secrets/google_sheets & drive.env` (OAuth refresh token)

**Workflow (saved in memory/monthly-budget-workflow.md):**
- At month-end: Duplicate Summary → YYYY_MM, Transactions → YYYY_MMtrans
- Freeze snapshots (convert formulas to values, preserve sparklines)
- Update Summary cell M3 to reference previous month
- Reset Transactions sheet (keep recurring, clear rest)
- Add transactions using Google Sheets API

**How to add transactions:**
1. Use Google Sheets API with credentials from secrets
2. Build credentials with `token=None` + refresh token/client id/client secret, then call `creds.refresh(Request())`
3. Do not force scopes during refresh for this token flow (prevents `invalid_scope` errors)
4. Store amounts as numbers (not "$" strings)
5. Use `valueInputOption='USER_ENTERED'` so Google interprets dates/amounts
6. Expenses go in columns B-E, Income in G-J
7. **Always copy formatting** from an existing row before adding new transactions (use `copyPaste` with `pasteType: 'PASTE_FORMAT'`), then update values
8. **Refunds** always go in Income section as "Reimbursement" category, not in Expenses
9. **For Amazon purchases:** Always check the order confirmation email to get the actual item description - never use "Amazon.com *" or leave the description blank. Categorize properly (Entertainment for movies/media, Household Items for physical products).
10. **Valid categories:** Always use exact dropdown values:
    - Expenses: Gas for Car, Household Items, Entertainment, Dining Out, Other, Gas Bill, My Music Career, Misc Helpfulness, Fixed Expenses
    - Income: Lessons, PIER Church, Reimbursement, Other
11. **Gas purchases:** Include station name, loyalty program, price per gallon, and total gallons in description

## Screenshot Management
- **Rule:** Automatically trash `peekaboo` screenshots (`peekaboo-*.png`, `peekaboo_see_*.png`) and generic `screenshot-*.png` files from common locations (Desktop, Downloads, Documents) after they are used or no longer needed for the current task. Prioritize `trash` over `rm` for recoverability.


## Lesson Export Rule (added March 17, 2026)
- When uploading reMarkable lesson notes to Google Drive, ONLY upload the PNG with the highest page number
- Not all pages - just the one with the highest number




## Voice Lesson Pre-Email Check (added March 17, 2026)
- For voice lessons, check Drive folder for BOTH PNG + audio before drafting email
- If either is missing, skip email (don't send incomplete updates)


