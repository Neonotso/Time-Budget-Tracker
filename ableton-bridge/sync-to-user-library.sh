#!/usr/bin/env bash
set -euo pipefail
SRC_DIR="/Users/ryantaylorvegh/.openclaw/workspace/ableton-bridge/m4l"
DST_DIR="/Users/ryantaylorvegh/Music/ABLETON/User Library/Presets/Audio Effects/Max Audio Effect"
mkdir -p "$DST_DIR"
cp -f "$SRC_DIR/BridgeTelemetry.js" "$DST_DIR/BridgeTelemetry.js"
cp -f "$SRC_DIR/ScaleBridge.js" "$DST_DIR/ScaleBridge.js"
cp -f "$SRC_DIR/telemetry_post.js" "$DST_DIR/telemetry_post.js"
cp -f "$SRC_DIR/AbletonBridgeTelemetry.maxpat" "$DST_DIR/AbletonBridgeTelemetry.maxpat"
echo "Synced BridgeTelemetry.js + ScaleBridge.js + telemetry_post.js + AbletonBridgeTelemetry.maxpat to User Library Max Audio Effect folder."