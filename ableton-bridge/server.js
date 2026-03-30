#!/usr/bin/env node
import { WebSocketServer } from 'ws';
import { spawnSync } from 'node:child_process';
import dgram from 'node:dgram';
import http from 'node:http';

const port = Number(process.env.ABLETON_BRIDGE_PORT || 8765);
const wss = new WebSocketServer({ host: '127.0.0.1', port });
const latestTelemetryByTrack = new Map();
let latestGlobalScaleState = null;
let pendingGlobalScaleCommand = null;
const latestClipScaleStateByClip = new Map();
let pendingClipScaleCommand = null;
const udpPort = Number(process.env.ABLETON_BRIDGE_UDP_PORT || 8766);
const httpPort = Number(process.env.ABLETON_BRIDGE_HTTP_PORT || 8767);
const calibrationFactor = Number(process.env.ABLETON_BRIDGE_CALIBRATION || 0.73);

function ok(id, result) {
  return JSON.stringify({ jsonrpc: '2.0', id, result });
}
function err(id, code, message) {
  return JSON.stringify({ jsonrpc: '2.0', id, error: { code, message } });
}

function extractJsonObject(text) {
  const start = text.indexOf('{');
  if (start === -1) return null;

  let depth = 0;
  let inString = false;
  let escape = false;

  for (let i = start; i < text.length; i++) {
    const ch = text[i];

    if (inString) {
      if (escape) {
        escape = false;
      } else if (ch === '\\') {
        escape = true;
      } else if (ch === '"') {
        inString = false;
      }
      continue;
    }

    if (ch === '"') {
      inString = true;
      continue;
    }

    if (ch === '{') depth++;
    if (ch === '}') {
      depth--;
      if (depth === 0) {
        const candidate = text.slice(start, i + 1);
        try { return JSON.parse(candidate); } catch { return null; }
      }
    }
  }

  return null;
}

function mcpSpawn(tool, args = {}, output = 'text') {
  const cmdArgs = [
    'call',
    '--stdio', 'uv',
    '--stdio-arg', 'run',
    '--stdio-arg', 'python',
    '--stdio-arg', 'MCP_Server/server.py',
    '--server', 'abletonlocal',
    '--tool', tool,
    '--args', JSON.stringify(args),
    '--output', output,
    '--timeout', '30000',
  ];

  return spawnSync('mcporter', cmdArgs, {
    cwd: '/Users/ryantaylorvegh/.openclaw/workspace/ableton-mcp',
    encoding: 'utf8',
    timeout: 35000,
  });
}

function mcpTool(tool, args = {}) {
  const r = mcpSpawn(tool, args, 'text');
  const parsed = extractJsonObject(r.stdout || '');
  if (!parsed) {
    throw new Error(`MCP parse failed for ${tool}`);
  }
  return parsed;
}

function mcpToolText(tool, args = {}) {
  const r = mcpSpawn(tool, args, 'text');
  return {
    ok: (r.status === 0),
    stdout: r.stdout || '',
    stderr: r.stderr || '',
    status: r.status,
  };
}

wss.on('connection', (ws) => {
  ws.on('message', async (buf) => {
    let req;
    try {
      req = JSON.parse(buf.toString());
    } catch {
      ws.send(err(null, -32700, 'Parse error'));
      return;
    }

    const { id = null, method, params = {} } = req || {};

    try {
      if (method === 'health') {
        const session = mcpTool('get_session_info', {});
        ws.send(ok(id, { status: 'ok', bridge: 'ableton-bridge-mvp', ts: Date.now(), tempo: session.tempo }));
        return;
      }

      if (method === 'list_tracks') {
        const session = mcpTool('get_session_info', {});
        const count = Number(session.track_count || 0);
        const tracks = [];
        for (let i = 0; i < count; i++) {
          const t = mcpTool('get_track_info', { track_index: i });
          tracks.push({ index: i, name: t.name, deviceCount: (t.devices || []).length });
        }
        ws.send(ok(id, { tracks }));
        return;
      }

      if (method === 'list_devices') {
        const { trackIndex } = params;
        if (trackIndex === undefined) {
          ws.send(err(id, -32602, 'Missing params: trackIndex'));
          return;
        }
        const t = mcpTool('get_track_info', { track_index: Number(trackIndex) });
        ws.send(ok(id, { trackIndex: Number(trackIndex), trackName: t.name, devices: t.devices || [] }));
        return;
      }

      if (method === 'find_device') {
        const { trackIndex, name } = params;
        if (trackIndex === undefined || !name) {
          ws.send(err(id, -32602, 'Missing params: trackIndex, name'));
          return;
        }
        const result = mcpTool('find_device', { track_index: Number(trackIndex), query: String(name) });
        ws.send(ok(id, result));
        return;
      }

      if (method === 'list_params') {
        const { trackIndex, deviceIndex } = params;
        if ([trackIndex, deviceIndex].some(v => v === undefined)) {
          ws.send(err(id, -32602, 'Missing params: trackIndex, deviceIndex'));
          return;
        }
        const full = mcpTool('get_device_parameters', {
          track_index: Number(trackIndex),
          device_index: Number(deviceIndex),
        });
        ws.send(ok(id, {
          trackIndex: Number(trackIndex),
          deviceIndex: Number(deviceIndex),
          deviceName: full.device_name,
          className: full.class_name,
          parameters: full.parameters || [],
        }));
        return;
      }

      if (method === 'get_param') {
        const { trackIndex, deviceIndex, paramName } = params;
        if ([trackIndex, deviceIndex, paramName].some(v => v === undefined)) {
          ws.send(err(id, -32602, 'Missing params: trackIndex, deviceIndex, paramName'));
          return;
        }
        const full = mcpTool('get_device_parameters', {
          track_index: Number(trackIndex),
          device_index: Number(deviceIndex),
        });
        const target = (full.parameters || []).find((p) => {
          const n = String(p.name || '').toLowerCase();
          const q = String(paramName).toLowerCase();
          return n === q || n.includes(q);
        });
        if (!target) {
          ws.send(err(id, -32004, `Parameter not found: ${paramName}`));
          return;
        }
        ws.send(ok(id, target));
        return;
      }

      if (method === 'load_plugin_by_name') {
        const { trackIndex, vendor = 'iZotope', name } = params;
        if ([trackIndex, name].some(v => v === undefined)) {
          ws.send(err(id, -32602, 'Missing params: trackIndex, name'));
          return;
        }

        const vendorPath = `Plugins/AUv2/${vendor}`;
        const listing = mcpTool('get_browser_items_at_path', { path: vendorPath });
        const items = listing.items || [];
        const q = String(name).toLowerCase();
        const match = items.find((it) => String(it.name || '').toLowerCase() === q)
          || items.find((it) => String(it.name || '').toLowerCase().includes(q));

        if (!match || !match.uri) {
          ws.send(err(id, -32004, `Plugin not found under ${vendorPath}: ${name}`));
          return;
        }

        const load = mcpToolText('load_instrument_or_effect', {
          track_index: Number(trackIndex),
          uri: String(match.uri),
        });

        const loaded = load.ok && /Loaded instrument/i.test(load.stdout || '');
        ws.send(ok(id, {
          matchedName: match.name,
          uri: match.uri,
          loaded,
          output: (load.stdout || '').trim(),
          error: loaded ? null : ((load.stderr || '').trim() || 'Load failed'),
        }));
        return;
      }

      if (method === 'set_param') {
        const { trackIndex, deviceIndex, paramName, value } = params;
        if ([trackIndex, deviceIndex, paramName, value].some(v => v === undefined)) {
          ws.send(err(id, -32602, 'Missing params: trackIndex, deviceIndex, paramName, value'));
          return;
        }
        const result = mcpTool('set_device_parameter', {
          track_index: Number(trackIndex),
          device_index: Number(deviceIndex),
          parameter: String(paramName),
          value: Number(value),
        });
        ws.send(ok(id, result));
        return;
      }

      if (method === 'route_sidechain') {
        const { trackIndex, deviceIndex, sourceTrackName, sourceTrackIndex, mode = 'Post FX' } = params;
        if ([trackIndex, deviceIndex].some(v => v === undefined) || (sourceTrackName === undefined && sourceTrackIndex === undefined)) {
          ws.send(err(id, -32602, 'Missing params: trackIndex, deviceIndex, sourceTrackName|sourceTrackIndex'));
          return;
        }

        let inputType = sourceTrackName;
        if (inputType === undefined) {
          const t = mcpTool('get_track_info', { track_index: Number(sourceTrackIndex) });
          inputType = t.name;
        }

        const routing = mcpTool('set_device_input_routing', {
          track_index: Number(trackIndex),
          device_index: Number(deviceIndex),
          input_type: String(inputType),
          input_channel: String(mode),
        });

        const sc = mcpTool('set_device_parameter', {
          track_index: Number(trackIndex),
          device_index: Number(deviceIndex),
          parameter: 'S/C On',
          value: 1,
        });

        ws.send(ok(id, { routing, sidechain: sc }));
        return;
      }

      if (method === 'setup_sidechain') {
        const {
          trackIndex,
          sourceTrackName,
          sourceTrackIndex,
          deviceName = 'Compressor',
          threshold = 0.32,
          ratio = 0.9,
          attack = 0.08,
          release = 0.42,
          mode = 'Post FX',
        } = params;

        if (trackIndex === undefined || (sourceTrackName === undefined && sourceTrackIndex === undefined)) {
          ws.send(err(id, -32602, 'Missing params: trackIndex, sourceTrackName|sourceTrackIndex'));
          return;
        }

        const found = mcpTool('find_device', {
          track_index: Number(trackIndex),
          query: String(deviceName),
        });
        const deviceIndex = Number(found.device_index);

        let inputType = sourceTrackName;
        if (inputType === undefined) {
          const t = mcpTool('get_track_info', { track_index: Number(sourceTrackIndex) });
          inputType = t.name;
        }

        const routing = mcpTool('set_device_input_routing', {
          track_index: Number(trackIndex),
          device_index: deviceIndex,
          input_type: String(inputType),
          input_channel: String(mode),
        });

        const updates = [
          mcpTool('set_device_parameter', { track_index: Number(trackIndex), device_index: deviceIndex, parameter: 'Device On', value: 1 }),
          mcpTool('set_device_parameter', { track_index: Number(trackIndex), device_index: deviceIndex, parameter: 'S/C On', value: 1 }),
          mcpTool('set_device_parameter', { track_index: Number(trackIndex), device_index: deviceIndex, parameter: 'Threshold', value: Number(threshold) }),
          mcpTool('set_device_parameter', { track_index: Number(trackIndex), device_index: deviceIndex, parameter: 'Ratio', value: Number(ratio) }),
          mcpTool('set_device_parameter', { track_index: Number(trackIndex), device_index: deviceIndex, parameter: 'Attack', value: Number(attack) }),
          mcpTool('set_device_parameter', { track_index: Number(trackIndex), device_index: deviceIndex, parameter: 'Release', value: Number(release) }),
        ];

        ws.send(ok(id, { trackIndex: Number(trackIndex), deviceIndex, routing, updates }));
        return;
      }

      if (method === 'measure_sidechain_effect') {
        const { trackIndex, deviceIndex, bursts = 4, kickTrackIndex = 4, padClipIndex = 0, kickClipIndex = 0 } = params;
        if ([trackIndex, deviceIndex].some(v => v === undefined)) {
          ws.send(err(id, -32602, 'Missing params: trackIndex, deviceIndex'));
          return;
        }

        // Ensure audio context is active before sampling
        try { mcpTool('fire_clip', { track_index: Number(kickTrackIndex), clip_index: Number(kickClipIndex) }); } catch {}
        try { mcpTool('fire_clip', { track_index: Number(trackIndex), clip_index: Number(padClipIndex) }); } catch {}
        try { mcpTool('start_playback', {}); } catch {}

        const values = [];
        const n = Math.max(1, Math.min(12, Number(bursts)));
        for (let i = 0; i < n; i++) {
          const r = mcpTool('estimate_sidechain_gr', {
            track_index: Number(trackIndex),
            device_index: Number(deviceIndex),
          });
          if (typeof r.estimated_gr_db === 'number') values.push(r.estimated_gr_db);
        }

        const stats = values.length
          ? {
              samples: values.length,
              minDb: Math.min(...values),
              maxDb: Math.max(...values),
              avgDb: values.reduce((a, b) => a + b, 0) / values.length,
              values,
              source: 'proxy_estimate_sidechain_gr'
            }
          : { samples: 0, values: [], source: 'proxy_estimate_sidechain_gr' };

        ws.send(ok(id, stats));
        return;
      }

      if (method === 'get_global_scale') {
        if (latestGlobalScaleState) {
          ws.send(ok(id, { status: 'ok', ...latestGlobalScaleState }));
          return;
        }
        ws.send(ok(id, {
          status: 'awaiting_m4l_source',
          source: 'm4l_scale_bridge_pending',
          hint: 'Expose Live global scale/key via Max for Live LiveAPI bridge and push via /scale-state.'
        }));
        return;
      }

      if (method === 'set_global_scale') {
        const { root, scale, inKeyEnabled } = params;
        pendingGlobalScaleCommand = {
          id: Date.now(),
          root,
          scale,
          inKeyEnabled: (inKeyEnabled === undefined ? true : !!inKeyEnabled),
          createdTs: Date.now()
        };
        ws.send(ok(id, {
          status: 'queued_for_m4l_bridge',
          requested: pendingGlobalScaleCommand,
          source: 'm4l_scale_bridge_pending',
          hint: 'Command queued. M4L ScaleBridge should poll /scale-command and apply via LiveAPI.'
        }));
        return;
      }


      if (method === 'get_clip_scale') {
        const { trackIndex, clipIndex } = params;
        const key = `${Number(trackIndex)}:${Number(clipIndex)}`;
        const latest = latestClipScaleStateByClip.get(key);
        if (latest) {
          ws.send(ok(id, { status: 'ok', ...latest }));
          return;
        }
        ws.send(ok(id, {
          status: 'awaiting_m4l_source',
          source: 'm4l_clip_scale_bridge_pending',
          key,
          hint: 'Expose clip scale/key via Max for Live bridge and push via /clip-scale-state.'
        }));
        return;
      }

      if (method === 'set_clip_scale') {
        const { trackIndex, clipIndex, root, scale, enabled } = params;
        pendingClipScaleCommand = {
          id: Date.now(),
          type: 'set_clip_scale',
          trackIndex: Number(trackIndex),
          clipIndex: Number(clipIndex),
          root,
          scale,
          enabled: (enabled === undefined ? true : !!enabled),
          createdTs: Date.now()
        };
        ws.send(ok(id, {
          status: 'queued_for_m4l_bridge',
          requested: pendingClipScaleCommand,
          source: 'm4l_clip_scale_bridge_pending'
        }));
        return;
      }

      if (method === 'set_all_clip_scales_from_pad') {
        const { padTrackIndex, padClipIndex, includeAudio = true, includeMidi = true, includeEmpty = false } = params;
        pendingClipScaleCommand = {
          id: Date.now(),
          type: 'set_all_clip_scales_from_pad',
          padTrackIndex: Number(padTrackIndex),
          padClipIndex: Number(padClipIndex),
          includeAudio: !!includeAudio,
          includeMidi: !!includeMidi,
          includeEmpty: !!includeEmpty,
          createdTs: Date.now()
        };
        ws.send(ok(id, {
          status: 'queued_for_m4l_bridge',
          requested: pendingClipScaleCommand,
          source: 'm4l_clip_scale_bridge_pending'
        }));
        return;
      }

      if (method === 'push_duck_telemetry') {
        const payload = params || {};
        const trackId = String(payload.trackId || 'track-unknown');
        latestTelemetryByTrack.set(trackId, {
          ...payload,
          receivedTs: Date.now(),
          source: payload.source || 'external_push'
        });
        ws.send(ok(id, { status: 'ok', stored: true, trackId }));
        return;
      }

      if (method === 'get_duck_telemetry') {
        const { trackId = 'track-6', kickTrackId = 'track-4', windowMs = 120 } = params;
        const latest = latestTelemetryByTrack.get(String(trackId));
        if (latest) {
          const inst = Number(latest.instDuckDb || 0);
          const peak = Number(latest.peakDuckDb || 0);
          const med = Number(latest.medianDuckDb || 0);
          ws.send(ok(id, {
            status: 'ok',
            ...latest,
            calibrationFactor,
            instDuckDbCalibrated: inst * calibrationFactor,
            peakDuckDbCalibrated: peak * calibrationFactor,
            medianDuckDbCalibrated: med * calibrationFactor,
          }));
          return;
        }
        ws.send(ok(id, {
          status: 'awaiting_m4l_source',
          source: 'm4l_bridge_pending',
          trackId,
          kickTrackId,
          windowMs: Number(windowMs),
          calibrationFactor,
          hint: 'Install Ableton Bridge M4L telemetry device and push duck telemetry via push_duck_telemetry.'
        }));
        return;
      }

      ws.send(err(id, -32601, `Method not found: ${method}`));
    } catch (e) {
      ws.send(err(id, -32000, String(e.message || e)));
    }
  });
});

const udp = dgram.createSocket('udp4');
udp.on('message', (msg) => {
  const raw = msg.toString().trim();
  if (!raw) return;
  const lines = raw.split(/\n+/);
  for (const line of lines) {
    try {
      const payload = JSON.parse(line);
      const trackId = String(payload.trackId || 'track-unknown');
      latestTelemetryByTrack.set(trackId, {
        ...payload,
        receivedTs: Date.now(),
        source: payload.source || 'udp_push'
      });
    } catch {
      // ignore malformed datagrams
    }
  }
});
udp.bind(udpPort, '127.0.0.1');

const httpServer = http.createServer((req, res) => {
  if (req.method === 'GET' && req.url === '/scale-command') {
    res.writeHead(200, { 'content-type': 'application/json' });
    res.end(JSON.stringify({ ok: true, command: pendingGlobalScaleCommand }));
    return;
  }

  if (req.method === 'GET' && req.url === '/clip-scale-command') {
    res.writeHead(200, { 'content-type': 'application/json' });
    res.end(JSON.stringify({ ok: true, command: pendingClipScaleCommand }));
    return;
  }

  if (req.method === 'POST' && req.url === '/clip-scale-command-ack') {
    let body = '';
    req.on('data', (chunk) => { body += chunk.toString(); });
    req.on('end', () => {
      try {
        const payload = JSON.parse(body || '{}');
        if (!pendingClipScaleCommand || payload.id === pendingClipScaleCommand.id) {
          pendingClipScaleCommand = null;
        }
        res.writeHead(200, { 'content-type': 'application/json' });
        res.end(JSON.stringify({ ok: true }));
      } catch (e) {
        res.writeHead(400, { 'content-type': 'application/json' });
        res.end(JSON.stringify({ ok: false, error: String(e.message || e) }));
      }
    });
    return;
  }

  if (req.method === 'POST' && req.url === '/scale-command-ack') {
    let body = '';
    req.on('data', (chunk) => { body += chunk.toString(); });
    req.on('end', () => {
      try {
        const payload = JSON.parse(body || '{}');
        if (!pendingGlobalScaleCommand || payload.id === pendingGlobalScaleCommand.id) {
          pendingGlobalScaleCommand = null;
        }
        res.writeHead(200, { 'content-type': 'application/json' });
        res.end(JSON.stringify({ ok: true }));
      } catch (e) {
        res.writeHead(400, { 'content-type': 'application/json' });
        res.end(JSON.stringify({ ok: false, error: String(e.message || e) }));
      }
    });
    return;
  }

  if (req.method === 'POST' && (req.url === '/duck-telemetry' || req.url === '/scale-state' || req.url === '/clip-scale-state')) {
    let body = '';
    req.on('data', (chunk) => {
      body += chunk.toString();
      if (body.length > 1_000_000) req.destroy();
    });
    req.on('end', () => {
      try {
        const payload = JSON.parse(body || '{}');
        if (req.url === '/duck-telemetry') {
          const trackId = String(payload.trackId || 'track-unknown');
          latestTelemetryByTrack.set(trackId, {
            ...payload,
            receivedTs: Date.now(),
            source: payload.source || 'http_post'
          });
          res.writeHead(200, { 'content-type': 'application/json' });
          res.end(JSON.stringify({ ok: true, trackId }));
          return;
        }

        if (req.url === '/clip-scale-state') {
          const trackIndex = Number(payload.trackIndex);
          const clipIndex = Number(payload.clipIndex);
          const key = `${trackIndex}:${clipIndex}`;
          const state = {
            ...payload,
            trackIndex,
            clipIndex,
            key,
            receivedTs: Date.now(),
            source: payload.source || 'http_post'
          };
          latestClipScaleStateByClip.set(key, state);
          res.writeHead(200, { 'content-type': 'application/json' });
          res.end(JSON.stringify({ ok: true, topic: 'clip_scale_state', key }));
          return;
        }

        // /scale-state
        latestGlobalScaleState = {
          ...payload,
          receivedTs: Date.now(),
          source: payload.source || 'http_post'
        };
        res.writeHead(200, { 'content-type': 'application/json' });
        res.end(JSON.stringify({ ok: true, topic: 'global_scale_state' }));
      } catch (e) {
        res.writeHead(400, { 'content-type': 'application/json' });
        res.end(JSON.stringify({ ok: false, error: String(e.message || e) }));
      }
    });
    return;
  }

  res.writeHead(404, { 'content-type': 'application/json' });
  res.end(JSON.stringify({ ok: false, error: 'not_found' }));
});
httpServer.listen(httpPort, '127.0.0.1');

console.log(`Ableton Bridge listening on ws://127.0.0.1:${port} (udp:${udpPort}, http:${httpPort})`);
