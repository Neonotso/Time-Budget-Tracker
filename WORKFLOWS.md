# WORKFLOWS.md

## Command: `set up Sunday worship set`

When Ryan says **“set up Sunday worship set”**, run this exact sequence.

### Inputs needed
- Plan date (e.g. `2026-03-22`)
- Planning Center service type + plan id
- Song list (from plan items)

### Steps
0. **Execution mode (required): phased + save-after-each-step**
   - Run one phase at a time.
   - After each phase: **save, verify, then continue**.
   - Phases: (1) scenes, (2) pads, (3) tempos, (4) final save/reopen verify.

1. **Open clean template**
   - If Live is running, use in-app Open or close current set first.
   - Open: `Sunday Template for OpenClaw.als`.
   - Clear blocking dialogs first (Yes/OK).

2. **Get songs + keys from Planning Center**
   - Use PAT via Basic Auth (`curl -u "id:token" ...`).
   - Read plan items and extract `title` + `key_name`.

3. **Set scene names in correct slots (OSC)**
   - Song scenes are slots **3..7** in this template.
   - Name format: `* Full Song Name "Three Word Max"`.
   - Keep quoted short name to max 3 words.

4. **Set Pad clips to match keys (Pad track 10)**
   - Use OSC view select + Cmd+C/Cmd+V copy workflow.
   - Verify clip names with `/live/clip/get/name 10 <slot>`.
   - Expected key sequence for song scenes should match plan keys.

5. **Fetch tempos from MultiTracks (browser relay)**
   - Open each song’s `/multitracks/` page.
   - Parse `Key: <x> BPM: <n>`.
   - Write BPM to tempo clips on track 11 (`12 Tempo`), slots 3..7 via `/live/clip/set/name`.

6. **Save set properly**
   - If untitled: Cmd+Shift+S → filename date (e.g. `2026-03-22`) → Cmd+Shift+G → `/Users/ryantaylorvegh/Music/Church/Backing Track Sets` → Enter, Enter.
   - Normalize folder name to `YYYY-MM-DD` (not `YYYY-MM-DD Project`) when needed.

7. **Verify before done**
   - Scene names correct slots?
   - Pad clips keys correct?
   - Tempo clip names (BPM) correct?
   - File exists at:
     - `/Users/ryantaylorvegh/Music/Church/Backing Track Sets/YYYY-MM-DD/YYYY-MM-DD.als`

8. **Cleanup**
   - Remove `~/Desktop/peekaboo_*.png`.

## Notes
- Do not use terminal `open` while Live already has an active set unless intentionally restarting flow.
- Dialogs block all automation; always clear them first.
