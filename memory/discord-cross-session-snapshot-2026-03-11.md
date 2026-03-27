# Discord Cross-Session Snapshot (2026-03-11)

Compiled from the channels Ryan shared in Discord.

## PIER Song Database (`#pier-song-database`)
- Built Planning Center API ingestion + reporting pipeline.
- Generated first-pass keep/review/retire CSV outputs, then improved to full-history scan.
- Full-history stats cited in channel:
  - 565 plans
  - 2,797 song events
  - 507 songs
- Published data to Google Sheet and formatted tabs (`all_songs`, `keep_core`, `review`, `retire_candidates`).
- Added full-history tabs (`full_summary`, `full_events`) and sorting/formatting.
- Important lesson: 3-recent-use heuristic is not enough for strategic decisions; full-history recency/frequency needed.

## PIER Map App (`#pier-map-app`)
- Ongoing repo + deploy work in `PIER-People` (Firebase live deploy workflow).
- Multiple fixes shipped around navigation UX + behavior:
  - nav banner step indicators
  - reroute/end controls
  - coupling navigation stop with live tracking stop behavior
  - close info window when navigating
  - hide legend during navigation and restore after
  - dark/light mode behavior tied to device on load
- Repo hygiene:
  - two local clones existed (`workspace/PIER-People` and `~/PIER-People`)
  - user-folder clone was behind, later fast-forward synced
- Reinforced process: push + deploy after edit sessions.

## Mission Control (`#mission-control`)
- Built a local Mission Control prototype (Next.js), launched on localhost.
- Core sections implemented: Task Board, Calendar, Projects, Memory, Docs, Team, Office.
- Later updated UI content from placeholder data toward real project context.
- Session architecture note captured: this Discord channel used one main channel session.

## Ableton / music-related lanes (cross-channel context)
- Strong ongoing initiatives Ryan expects tracked under Ableton systems:
  - weekly worship set build workflow
  - iOS Ableton remote app
  - Ableton Bridge (in progress)
  - control via MCP / OSC / OSC-MCP + UI fallbacks
- Additional lane referenced by Ryan: backing track generation for Ableton.

## PIER Church support lanes explicitly called out by Ryan
- Chord chart/ChordPro pipeline still unresolved (goal: avoid manual file downloads).
- Slide image generation uses local Fooocus installation.
- PIER song database trimming is active ongoing work.

## Finance / monthly budget
- Monthly budget work remains active and should stay as a dedicated lane.
- Venmo/budget reconciliation and sheet maintenance expected to continue.

## Process/ops notes to preserve
- Keep main-session continuity by periodically reconciling Discord-channel work into main memory.
- Avoid assuming transcript fragment timestamps are sentence-safe for clip editing; use post-render transcript verification.
- For external outreach: do not proactively offer Sally services to others unless Ryan explicitly asks.
- For thread replies on email: default reply-all so Ryan stays in the loop.
