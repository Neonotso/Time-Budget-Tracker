# Ableton Bridge — Next Tasks

## High priority (clip key workflow)
- [ ] Add `select_clip(trackIndex, clipIndex)` (no fire)
- [ ] Add `select_all_clips_session()` (best-effort)
- [ ] Add `set_selected_clips_scale(root, scale, inKeyEnabled)`
- [ ] Add `set_clip_scale(trackIndex, clipIndex, root, scale)`
- [ ] Add `get_selected_clips()` diagnostics

## Scale/key bridge hardening
- [ ] Ensure scale polling autostarts reliably on device load (`loadbang -> start_poll`)
- [ ] Add robust root write path (remove coercion ambiguity)
- [ ] Add bridge-side command timeout + retry for scale command queue

## Telemetry hardening
- [ ] Improve peak/median robustness (ignore startup spikes)
- [ ] Add telemetry health endpoint (`get_telemetry_health`)

## Plugin control
- [ ] Keep `load_plugin_by_name` as preferred path
- [ ] Add better error hints for AU/VST load failures
