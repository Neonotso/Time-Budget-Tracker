// ScaleBridge.js
// Node for Max helper: bridge Ableton global scale/key state to Ableton Bridge HTTP.

const Max = require('max-api');

const BRIDGE_BASE = process.env.ABLETON_BRIDGE_HTTP_BASE || 'http://127.0.0.1:8767';
const PUSH_URL = `${BRIDGE_BASE}/scale-state`;
const COMMAND_URL = `${BRIDGE_BASE}/scale-command`;
const ACK_URL = `${BRIDGE_BASE}/scale-command-ack`;
const CLIP_COMMAND_URL = `${BRIDGE_BASE}/clip-scale-command`;
const CLIP_ACK_URL = `${BRIDGE_BASE}/clip-scale-command-ack`;
const CLIP_STATE_URL = `${BRIDGE_BASE}/clip-scale-state`;
let pollTimer = null;
let lastGlobalCommandId = null;
let lastClipCommandId = null;

async function postScaleState(payload) {
  try {
    const res = await fetch(PUSH_URL, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const txt = await res.text();
    Max.post(`ScaleBridge POST ${res.status}: ${txt}`);
    Max.outlet(['ok', res.status]);
  } catch (e) {
    Max.post(`ScaleBridge error: ${e.message}`);
    Max.outlet(['error', String(e.message)]);
  }
}

// Accept pre-resolved scale state from Max patch (LiveAPI side).
// Example:
// state C Minor 1
Max.addHandler('state', async (root, scale, inKeyEnabled = 1) => {
  await postScaleState({
    topic: 'global_scale_state',
    ts: Date.now(),
    root: String(root),
    scale: String(scale),
    inKeyEnabled: !!Number(inKeyEnabled),
  });
});

// passthrough json
Max.addHandler('json', async (...args) => {
  const raw = args.join(' ');
  try {
    const payload = JSON.parse(raw);
    payload.topic = payload.topic || 'global_scale_state';
    payload.ts = payload.ts || Date.now();
    await postScaleState(payload);
  } catch (e) {
    Max.post(`ScaleBridge json parse error: ${e.message}`);
  }
});

async function pollCommands() {
  try {
    const res = await fetch(COMMAND_URL);
    const data = await res.json();
    const cmd = data && data.command;
    if (!cmd || !cmd.id) return;
    if (lastGlobalCommandId === cmd.id) return;

    lastGlobalCommandId = cmd.id;
    // Emit command back into Max patch for LiveAPI wiring.
    // Expected in patch: route cmd_set_global_scale -> apply root/scale/inKey.
    Max.outlet(['cmd_set_global_scale', String(cmd.root), String(cmd.scale), cmd.inKeyEnabled ? 1 : 0, cmd.id]);

    await fetch(ACK_URL, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ id: cmd.id })
    });

    // Also check clip-scale command queue
    const clipRes = await fetch(CLIP_COMMAND_URL);
    const clipData = await clipRes.json();
    const clipCmd = clipData && clipData.command;
    if (clipCmd && clipCmd.id && lastClipCommandId !== clipCmd.id) {
      lastClipCommandId = clipCmd.id;
      if (clipCmd.type === 'set_clip_scale') {
        Max.outlet([
          'cmd_set_clip_scale',
          Number(clipCmd.trackIndex),
          Number(clipCmd.clipIndex),
          String(clipCmd.root),
          String(clipCmd.scale),
          clipCmd.enabled ? 1 : 0,
          clipCmd.id,
        ]);
      } else if (clipCmd.type === 'set_all_clip_scales_from_pad') {
        Max.outlet([
          'cmd_set_all_clip_scales_from_pad',
          Number(clipCmd.padTrackIndex),
          Number(clipCmd.padClipIndex),
          clipCmd.includeAudio ? 1 : 0,
          clipCmd.includeMidi ? 1 : 0,
          clipCmd.includeEmpty ? 1 : 0,
          clipCmd.id,
        ]);
      }
      await fetch(CLIP_ACK_URL, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ id: clipCmd.id })
      });
    }
  } catch (e) {
    // keep quiet; polling should be resilient
  }
}

Max.addHandler('start_poll', (ms = 500) => {
  const interval = Math.max(200, Number(ms) || 500);
  if (pollTimer) clearInterval(pollTimer);
  pollTimer = setInterval(pollCommands, interval);
  Max.post(`ScaleBridge polling every ${interval}ms`);
});

Max.addHandler('stop_poll', () => {
  if (pollTimer) clearInterval(pollTimer);
  pollTimer = null;
  Max.post('ScaleBridge polling stopped');
});


// clip_state <trackIndex> <clipIndex> <root> <scale> <enabled>
Max.addHandler('clip_state', async (trackIndex, clipIndex, root, scale, enabled = 1) => {
  try {
    const payload = {
      topic: 'clip_scale_state',
      ts: Date.now(),
      trackIndex: Number(trackIndex),
      clipIndex: Number(clipIndex),
      root: String(root),
      scale: String(scale),
      enabled: !!Number(enabled),
    };
    const res = await fetch(CLIP_STATE_URL, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(payload),
    });
    Max.outlet(['clip_state_ok', res.status, Number(trackIndex), Number(clipIndex)]);
  } catch (e) {
    Max.outlet(['clip_state_error', String(e.message)]);
  }
});

