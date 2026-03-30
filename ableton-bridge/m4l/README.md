# Ableton Bridge M4L Telemetry Device (Step 1)

This folder contains scaffolding for a Max for Live device that emits ducking telemetry.

## Files
- `BridgeTelemetry.js` — JS logic intended for a Max `js` object.
- `AbletonBridgeTelemetry.maxpat` — starter patch skeleton to host the JS.

## Intended signal path (audio effect device on PAD track)
1. Input audio from pad track enters device.
2. Device measures fast envelope (`snapshot~` style in patch).
3. JS receives sampled level stream + optional kick-hit trigger.
4. JS computes:
   - `instDuckDb`
   - rolling `peakDuckDb`
   - rolling `medianDuckDb`
5. JS emits JSON lines to Max outlet for transport to bridge.

## Current status
- Scaffolding only (not fully wired to live audio objects yet).
- Next iteration: add concrete Max MSP objects and route sample values into JS inlet.

## Telemetry JSON format
Matches `../telemetry-spec.json` (`duck_telemetry` topic).
