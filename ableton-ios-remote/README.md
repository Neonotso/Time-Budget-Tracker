# Ableton iOS Remote (V1 Scaffold)

A local-network web app (PWA-ready) to control Ableton Live transport from iPhone.

## V1 scope

- Play / Stop / Record
- Tap tempo
- Metronome toggle
- Tempo up/down + direct set
- Undo
- Connection status badge

## Architecture

1. **iPhone Web UI** (`public/`)
2. **Local Node server** (`server.js`) exposes REST + Socket.IO
3. **Mac bridge layer** (`bridge/`) sends commands to Ableton
   - For now: mock bridge + TODO hooks
   - Next: MIDI/OSC or Max for Live device

## Run

```bash
cd ableton-ios-remote
npm install
npm run dev
```

Then open on iPhone (same Wi-Fi):

`http://<YOUR-MAC-IP>:3030`

## Next implementation steps (exact plan)

### Phase 1: working transport (fast)
- [ ] Implement bridge command handlers in `bridge/abletonBridge.js`
- [ ] Connect handlers to Ableton via one of:
  - MIDI mapping (quickest)
  - OSC (if already configured)
  - Max for Live device (best long-term)
- [ ] Verify end-to-end latency (<100ms local)

### Phase 2: feedback loop
- [ ] Push live state over Socket.IO (isPlaying, isRecording, tempo)
- [ ] Reflect state in UI button colors/labels

### Phase 3: iPhone polish
- [ ] Add Add-to-Home-Screen manifest + icons
- [ ] Full-screen layout for stage use
- [ ] Haptic/visual confirmations

### Optional screen view from iPhone
- [ ] Lightweight option: embed a local VNC/WebRTC stream view panel
- [ ] Better option: add Live state panel (scene/clip/track info) before full video

## Security

- Local network only (bind to LAN intentionally)
- Add simple shared key for command endpoints before public/demo use
- No cloud exposure by default
