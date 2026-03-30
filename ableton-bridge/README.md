# Ableton Bridge (MVP)

Local JSON-RPC bridge for deterministic Ableton control.

## Goals
- Replace fragile UI automation with explicit APIs.
- Expose discovery + control primitives for tracks/devices/params.
- Enable OpenClaw to call reliable commands.

## Transport
- WebSocket on `ws://127.0.0.1:8765`
- JSON-RPC 2.0 messages

## Core methods (MVP)
- `health()`
- `list_tracks()`
- `list_devices({trackId})`
- `find_device({trackId,name})`
- `get_param({deviceId,param})`
- `set_param({deviceId,param,value})`
- `get_levels({trackId})`
- `route_sidechain({compressorDeviceId,sourceTrackId,mode})`

## Nice-to-have
- `ensure_rack_macro_mapping(...)`
- `set_macro(...)`
- `batch([{method,params}, ...])`

## Scale/Key control (scaffold)
- `get_global_scale()`
- `set_global_scale({root,scale,inKeyEnabled})`

Current state:
- Methods are scaffolded in bridge and return pending status.
- Next step is M4L LiveAPI exposure of Ableton global key/scale, then bridge wiring.

## Telemetry path (new)
- `push_duck_telemetry(payload)`
- `get_duck_telemetry({trackId,kickTrackId,windowMs})`

Current state:
- Bridge can store external telemetry pushes per track.
- `get_duck_telemetry` returns latest stored packet if available.

Next step:
- Max for Live telemetry device publishes `duck_telemetry` payload to bridge via `push_duck_telemetry`.

## IDs
- Track IDs: stable UUID-like strings produced by bridge.
- Device IDs: `trackId:deviceIndex:className` (v1), with lookup refresh.

## Safety
- Optional allowlist for mutating methods.
- `dryRun` support for planning.

## Next steps
1. Build Node adapter client (`client.js`) in this folder.
2. Define full JSON schema in `protocol.json`.
3. Implement Max for Live device to back these methods.
