# Cron Audit — 2026-03-20

## Goal
Figure out why some Sally-originated behavior/messages are showing up through Gus's Telegram thread, then stabilize routing before rebuilding the cron setup cleanly.

## Findings

### 1) The live cron store is here
- `~/.openclaw/cron/jobs.json`

This is the canonical live job store currently used by Gateway.

### 2) The problem is mainly migrated cron ownership + delivery, not simple inbound Telegram duplication
Several jobs were originally created under Sally/main and later reassigned to Gus by changing:
- `agentId` → `gus`
- `sessionKey` → `agent:gus:main`

But they were not fully re-authored as Gus-native jobs.

That left a mixed state where:
- the job owner is now Gus
- the payload/instructions were written in Sally-era context
- the job is isolated (`sessionTarget: "isolated"`)
- isolated jobs default to or keep `delivery.mode: "announce"` unless explicitly changed
- announce delivery can route externally without going through Sally's main chat turn

### 3) Current live jobs by owner

#### Sally / main-facing jobs
These are correctly still on `main` and should remain Sally-facing:
- `Regular email check` (`1cc650ef-8022-4e45-8849-6fa86e6e91c0`) — `sessionTarget: main`
- `Morning money board` (`b5afb83e-a86c-45b5-a993-a49b86ffea8d`) — `sessionTarget: main`

#### Gus-owned background jobs
These had been migrated to Gus:
- `Bible readers SMS reminder dispatcher` (`3ac6a4e1-e96c-4247-aacd-3dcf67a0538e`)
- `Email receipts to budget (Amazon)` (`9e46aae7-126c-475d-8f2b-218d798a34d2`)
- `Nightly Venmo to bank transfer` (`3956d85f-f139-49af-9451-36466cf11a84`)
- `Monthly PIER Report Report` (`01102deb-3743-4426-81d2-e6fa8624edf1`)
- `After-lesson automation sweep` (`bd393969-eaef-48a2-b7e5-39ce5c8d46bd`) [currently disabled]

### 4) Evidence of prior bad delivery state
From logs / prior job state, migrated jobs had delivery-related failures such as:
- `Channel is required when multiple channels are configured: telegram, whatsapp`
- `Delivering to Telegram requires target <chatId>`
- `Delivering to WhatsApp requires target <E.164|group JID>`

This strongly indicates the migration changed ownership/session but left delivery assumptions in a partially broken state.

### 5) Separate config issue found
`~/.openclaw/openclaw.json` had a syntax error in Gus's agent block (missing comma before `"model"`).
This was fixed on 2026-03-20.

## Immediate mitigation applied
To stop cross-thread / surprise external announcements while auditing, these Gus-owned isolated jobs were changed to:
- `delivery.mode: "none"`

Applied to:
- `3ac6a4e1-e96c-4247-aacd-3dcf67a0538e`
- `9e46aae7-126c-475d-8f2b-218d798a34d2`
- `3956d85f-f139-49af-9451-36466cf11a84`
- `01102deb-3743-4426-81d2-e6fa8624edf1`
- `bd393969-eaef-48a2-b7e5-39ce5c8d46bd`

### What this mitigation does
- Stops those jobs from posting external summaries to Telegram/WhatsApp/etc.
- Stops them from announcing into the main session as cron summaries.
- Lets the jobs still run internally.

### Tradeoff
- Ryan will no longer automatically see success/failure summaries from those Gus jobs until a cleaner reporting path is rebuilt.

## Recommended rebuild plan

### Phase 1 — containment ✅
- Fix config syntax error
- Disable external announce delivery for migrated Gus jobs

### Phase 2 — clean separation
Rebuild Gus-owned jobs so they are explicitly one of these:

#### Pattern A: internal-only chores
Use for jobs that should run silently unless manually inspected.
- `sessionTarget: isolated`
- `delivery.mode: none`

Likely candidates:
- Email receipts to budget (if no user-facing summary needed)
- Bible readers SMS dispatcher (if only operational)

#### Pattern B: explicit notification jobs
Use only when Ryan truly wants an automatic heads-up.
- `sessionTarget: isolated`
- `delivery.mode: announce`
- explicit `delivery.channel`
- explicit `delivery.to`
- explicit `delivery.account` if needed

Likely candidates:
- Nightly Venmo transfer
- After-lesson automation sweep (only when meaningful output exists)

### Phase 3 — re-author, don't keep patching
Best practice: recreate transferred jobs cleanly instead of preserving inherited state forever.

For each Gus-owned job:
1. Export current payload/instructions
2. Remove old job
3. Create fresh job with:
   - correct `agentId`
   - correct `sessionTarget`
   - intentional delivery mode
   - explicit destination if announcing
4. Test with `openclaw cron run <id>`
5. Verify no message lands in the wrong Telegram thread

## Open questions to decide with Ryan
1. Which Gus jobs should be completely silent?
2. Which Gus jobs should notify Ryan automatically?
3. If Gus should notify Ryan, should that happen in:
   - Gus's Telegram thread
   - Sally's Telegram thread
   - webchat only
   - Discord/webhook instead?

## Notes
OpenClaw docs confirm:
- isolated jobs default to announce when delivery is omitted
- `delivery.mode: none` makes them internal-only
- manual edits to `jobs.json` are discouraged while Gateway is running; prefer `openclaw cron edit`

## Status at end of this audit pass
- Root cause direction identified
- Config syntax bug fixed
- Immediate containment applied
- Next step: rebuild job-by-job with explicit delivery intent
