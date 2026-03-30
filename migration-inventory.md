# Migration Inventory (Current Mac Baseline)

Purpose: concrete source-of-truth for machine-specific dependencies that must exist on the new Mac.

Last updated: 2026-03-11
Current host: Ryan's M1 - Fresh Start

## 1) DAW / Audio stack

### Ableton Live
- Version: _TBD (not captured yet)_
- Install source/license location: _TBD_
- User Library path: _TBD_
- Packs required:
  - [ ] _TBD_
  - [ ] _TBD_

### Plugins / Instruments (VST/AU)
- [ ] Plugin inventory export pending
- [ ] License location mapping pending
- [ ] Must verify any iLok/Native Access dependencies

### Max for Live / bridges
- [x] ableton-bridge repo present (`./ableton-bridge`)
- [x] ableton-mcp repo present (`./ableton-mcp`)
- [ ] AbletonMCP installed + reachable (runtime check pending)
- [ ] AbletonOSC installed + reachable (runtime check pending)
- [ ] AbletonOSC-MCP installed + reachable (runtime check pending)

## 2) OpenClaw + automation dependencies

### CLIs
- [x] openclaw — `OpenClaw 2026.3.8 (3caab92)`
- [x] gh — `gh version 2.87.3`
- [x] ffmpeg — `ffmpeg version 8.0.1`
- [x] jq — `jq-1.7.1-apple`
- [x] python3 — `Python 3.14.3`
- [x] node / npm — `node v25.6.1`, `npm 11.9.0`

### Python deps (critical scripts)
- [ ] google-api-python-client (missing in current global py env)
- [ ] google-auth (missing in current global py env)
- [ ] google-auth-oauthlib (missing in current global py env)
- [ ] aiohttp (missing in current global py env)
- [ ] Confirm these are installed in project venv and record exact versions

### Node deps / repos
- [x] mission-control present — `mission-control@0.1.0`
- [x] ableton-ios-remote present — `ableton-ios-remote@0.1.0`
- [ ] Confirm fresh `npm install` succeeds on new Mac for both

## 3) macOS permissions and UX dependencies
- [ ] Terminal has Accessibility (manual verify)
- [ ] Terminal has Screen Recording (manual verify)
- [ ] reMarkable app has required permissions (manual verify)
- [ ] Peekaboo has required permissions (manual verify)
- [x] Peekaboo installed via Homebrew — `peekaboo 3.0.0-beta3`
- [x] KeyCastr installed (cask present)

## 4) Launch items / background services
- [x] launch agent plists present in workspace root:
  - `com.openclaw.gateway-start.plist`
  - `com.openclaw.gateway-stop.plist`
- [ ] Autostart behavior tested after reboot

## 5) Identity / messaging
From `openclaw status` snapshot:
- [x] Telegram configured
- [x] WhatsApp linked and active
- [x] Discord configured
- [ ] AgentMail sending tested on this host

## 6) Verification sign-off
- Migration date: _TBD_
- Old Mac hostname: `Ryan's M1 - Fresh Start`
- New Mac hostname: _TBD_
- Final status: IN PROGRESS
- Blocking issues:
  - [ ] Ableton/plugin inventory incomplete
  - [ ] Python dependency source-of-truth (venv vs global) not finalized
  - [ ] Permission/runtime validations pending
