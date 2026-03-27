# New Mac Migration Checklist (Operational)

Owner: Ryan + Sally  
Goal: move OpenClaw workflows to a new Mac with minimal downtime.

---

## Phase 0 — Pre-migration backup on current Mac
- [ ] Archive workspace
  - `cd ~/.openclaw && tar -czf ~/Desktop/openclaw-workspace-backup.tgz workspace`
- [ ] Export Homebrew bundle
  - `brew bundle dump --file ~/Desktop/Brewfile --force`
- [ ] Capture versions for parity
  - `node -v`
  - `python3 -V`
  - `openclaw --version`
- [ ] Backup secret files to secure storage (1Password/encrypted vault)
  - `.secrets/google_sheets & drive.env`
  - `.secrets/agentmail.env`
  - `.secrets/venmo_creds.env`
  - any Planning Center / custom envs
- [ ] Save current OpenClaw config snapshot
  - `openclaw status`

## Phase 1 — Base machine setup (new Mac)
- [ ] Update macOS fully
- [ ] Install Xcode Command Line Tools
  - `xcode-select --install`
- [ ] Install Homebrew
  - `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`
- [ ] Restore Brew packages from Brewfile (optional but recommended)
  - `brew bundle --file ~/Desktop/Brewfile`
- [ ] Confirm Git works
  - `git --version`

## Phase 2 — OpenClaw install + workspace restore
- [ ] Install Node.js (match current major/minor where possible)
- [ ] Install OpenClaw CLI globally
- [ ] Restore workspace to `~/.openclaw/workspace`
  - from tgz or git clone + copied local files
- [ ] Run health check
  - `openclaw status`

## Phase 3 — Channel reconnects
- [ ] Reconnect Telegram
- [ ] Reconnect WhatsApp
- [ ] Reconnect Discord (if still used)
- [ ] Verify all channels are healthy in `openclaw status`

## Phase 4 — Secrets + auth rehydration
- [ ] Restore `.secrets/*` files
- [ ] Restrict permissions
  - `chmod 700 ~/.openclaw/workspace/.secrets`
  - `chmod 600 ~/.openclaw/workspace/.secrets/*`
- [ ] Verify secrets are readable by workflows, not world-accessible

## Phase 5 — Google + API validation
- [ ] Sheets/Drive auth test (token refresh succeeds)
- [ ] Calendar API test
  - `python3 scripts/test_google_calendar_access.py`
- [ ] Confirm Apps Script deployment access still valid

## Phase 6 — Python environment
- [ ] Recreate venv
  - `cd ~/.openclaw/workspace && python3 -m venv venv && source venv/bin/activate`
- [ ] Install required packages (from requirements if present)
- [ ] Verify critical scripts:
  - [ ] `scripts/venmo_transactions.py`
  - [ ] calendar scripts
  - [ ] lesson workflow scripts

## Phase 7 — reMarkable + UI automation
- [ ] Install reMarkable desktop app
- [ ] Install/verify Peekaboo
- [ ] Grant Screen Recording + Accessibility permissions
- [ ] Install/verify KeyCastr (if used for calibration)
- [ ] Re-validate click calibrations in `TOOLS.md`

## Phase 8 — Data/workflow sanity checks
- [ ] Confirm Drive `Lessons` root + student folder visibility
- [ ] Confirm date folder naming (`YYYY MM Month DD`)
- [ ] Confirm email behavior rules still enforced:
  - Sally signature
  - CC Ryan default
  - third-party send requires Ryan approval

## Phase 9 — Heartbeat + automations
- [ ] Verify `HEARTBEAT.md` is present and current
- [ ] Confirm heartbeat cadence in `openclaw status`
- [ ] Run one manual dry-run heartbeat and review behavior

## Phase 10 — Budget system verification
- [ ] Confirm access to `Monthly Budget` spreadsheet
- [ ] Add one test transaction via script/API
- [ ] Validate rounding behavior:
  - expenses round up
  - large expenses round up to nearest $5
  - income/savings exact

## Phase 11 — End-to-end acceptance tests
- [ ] Voice lesson flow: calendar → trigger → reMarkable export → Drive upload → outbound message
- [ ] Drum lesson flow: notes-only path works
- [ ] Venmo reconciliation flow: detect missing tx + add to sheet
- [ ] One live-channel message send/receive test (Telegram/WhatsApp)

---

## Known items to inventory next
- [ ] DAW/Ableton dependencies and plugins
- [ ] Any custom launch agents / plist jobs
- [ ] Optional automated backup for `~/.openclaw/workspace`
