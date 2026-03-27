# Operating Playbook v1

Purpose: fast delegation + continuity across sessions/channels.
Owner: Sally (master orchestrator)

## 1) Agent lanes (who owns what)

### Sally (Master Orchestrator)
- Front-door intake for all requests
- Break work into tasks, assign worker lane
- Track status, blockers, and completion
- Keep Ryan looped in and prioritize correctly

### Ableton Systems Lane
- Weekly worship set setup
- Ableton Bridge work (in progress)
- iOS Ableton Remote work (in progress)
- Ableton control methods: MCP / OSC / OSC-MCP / UI fallback

### PIER Church Lane
- PIER Map App (`PIER-People`) feature/fix/deploy
- PIER Song Database analysis + cleanup workflows
- Chord charts / ChordPro pipeline R&D
- Church slide image generation pipeline (Fooocus)

### Finance Lane
- Monthly budget sheet workflows
- Month-end rollover/snapshot process
- Venmo-to-budget reconciliation

### Comms Lane
- Email/SMS/WhatsApp outbound communication
- Apply communication rules and approval rules

### Ops/Platform Lane
- Cron setup/maintenance
- Reliability fixes and script hardening
- Mission Control app status/revival

### Media Lane
- Video clipping/composites
- Transcript/OCR pipelines
- Post-render QA for sentence/flow integrity

---

## 2) Non-negotiable rules

1. **Reply-all default in thread replies** so Ryan remains in the loop unless explicitly overridden.
2. **Do not offer Sally services to other people** unless Ryan explicitly asks.
3. **PIER map edits:** push + deploy after edit sessions.
4. **Clip editing QA:** no contextless openers, no dangling sentence endings, no repeated thesis beats in adjacent stitched segments.
5. **External actions:** follow Ryan’s approval rules from USER.md.

---

## 3) Known active systems

### Bible Readers reminder automation
- Source: Google Sheet (`8:1 Bible Readers`) `Sheet1` A:D
- Dispatcher script: `scripts/bible_reader_sms_reminders.py`
- Sending path: local Messages bridge script (`send_message_via_messages.sh`)
- Schedule: cron every 15 minutes
- Timing logic:
  - reading < 12:00 PM → primary reminder day-before 6:00 PM
  - reading >= 12:00 PM → primary reminder same-day 9:00 AM
  - final reminder 1 hour before

### Messaging bridge (interim SMS/iMessage)
- Script: `scripts/send_message_via_messages.sh`
- For phone numbers, prefer SMS service first (to avoid iMessage-only failures)
- Dependency: Mac Messages + iPhone relay availability

### OCR pipeline status
- Tesseract/EasyOCR were poor on quote images
- Better local fallback: macOS Vision OCR (`ocrmac`)
- Google Photos API access attempted; still blocked by scope behavior in current OAuth/project setup

---

## 4) PIER Church priorities (current)

1. PIER Map App reliability + UX fixes + disciplined deploy flow
2. PIER Song Database trim (full-history informed)
3. ChordPro ingestion path without manual repeated downloads (still unresolved)
4. Fooocus slide image generation process hardening

---

## 5) Ableton priorities (current)

1. Weekly Sunday worship set automation stability
2. Better control layer hierarchy:
   - MCP where possible
   - OSC / OSC-MCP where effective
   - UI fallback where needed
3. Continue Ableton Bridge capabilities
4. Continue iOS remote development path

---

## 6) Operating cadence

- Keep Sally responsive in main chat.
- Offload long tasks to worker sessions/subagents.
- Return concise status updates with:
  - assigned lane
  - ETA
  - deliverable
  - blocker (if any)

Suggested status format:
- Lane: <name>
- State: queued/running/blocked/done
- Output: <artifact/path/link>
- Next: <next action>

---

## 7) Continuity maintenance

- After major Discord-channel work, reconcile into main memory snapshot.
- Update this playbook when lanes/rules change.
- Keep long-term memory distilled; keep tactical details in dated files.
