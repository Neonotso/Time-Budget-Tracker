import express from 'express';
import http from 'http';
import fs from 'node:fs';
import path from 'node:path';
import { Server as SocketServer } from 'socket.io';
import { getState, runCommand, getArrangementPreview, getTrackArmPreview, getTrackArmStatus, getProjectLocators } from './bridge/abletonBridge.js';

const app = express();
app.use(express.json());
app.use(express.static('public', {
  setHeaders: (res) => {
    res.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate');
  }
}));

let pushedMetronome = null;
let pushedMetronomeAt = 0;
let pushedIsPlaying = null;
let pushedIsPlayingAt = 0;
let pushedTrackArms = [];
let pushedTrackArmsAt = 0;

app.get('/api/state', (_req, res) => {
  res.json(getMergedState());
});

function getMergedState() {
  const state = getState();
  const freshMetro = pushedMetronome !== null && Date.now() - pushedMetronomeAt < 5 * 60 * 1000;
  if (freshMetro) state.metronome = !!pushedMetronome;

  const freshPlaying = pushedIsPlaying !== null && Date.now() - pushedIsPlayingAt < 10 * 1000;
  if (freshPlaying) state.isPlaying = !!pushedIsPlaying;

  return state;
}

let commandQueue = Promise.resolve();

function withTimeout(promise, ms, label) {
  return Promise.race([
    promise,
    new Promise((_, reject) => setTimeout(() => reject(new Error(`${label} timed out`)), ms))
  ]);
}

function enqueueCommand(name, payload, timeoutMs = 12000) {
  commandQueue = commandQueue
    .catch(() => null)
    .then(() => withTimeout(runCommand(name, payload), timeoutMs, name));
  return commandQueue;
}

app.post('/api/command/:name', async (req, res) => {
  try {
    const result = await enqueueCommand(req.params.name, req.body || {});
    const merged = getMergedState();
    io.emit('state', merged);
    res.status(result.success ? 200 : 400).json({ ...result, state: merged });
  } catch (err) {
    res.status(500).json({ success: false, error: String(err?.message || err), state: getState() });
  }
});

app.get('/api/arrangement-preview', async (_req, res) => {
  try {
    const preview = await getArrangementPreview();
    res.json({ success: true, preview });
  } catch (err) {
    res.status(500).json({ success: false, error: String(err?.message || err) });
  }
});

app.get('/api/tracks', async (req, res) => {
  try {
    const forceLive = String(req.query?.live || '') === '1';

    // Keep pushed metadata (group/color/nesting) as the canonical shape for UI.
    const hasPushed = pushedTrackArms.length > 0;
    if (hasPushed && !forceLive) {
      return res.json({
        success: true,
        preview: {
          trackCount: pushedTrackArms.length,
          showing: pushedTrackArms.length,
          hiddenNonArmable: 0,
          tracks: pushedTrackArms
        },
        source: 'pushed'
      });
    }

    const preview = await getTrackArmPreview();

    // When forceLive is requested and pushed metadata exists, merge live arm states into
    // pushed rows so we don't lose colors/group flags and cause UI flicker/regression.
    if (hasPushed && forceLive && Array.isArray(preview?.tracks)) {
      const byIndex = new Map(preview.tracks.map((t) => [Number(t.index), !!t.arm]));
      const merged = pushedTrackArms.map((t) => ({
        ...t,
        arm: byIndex.has(Number(t.index)) ? byIndex.get(Number(t.index)) : t.arm
      }));

      return res.json({
        success: true,
        preview: {
          trackCount: merged.length,
          showing: merged.length,
          hiddenNonArmable: 0,
          tracks: merged
        },
        source: 'merged'
      });
    }

    res.json({ success: true, preview, source: 'mcp' });
  } catch (err) {
    res.status(500).json({ success: false, error: String(err?.message || err) });
  }
});

app.get('/api/track-arm/:index', async (req, res) => {
  try {
    const track = await getTrackArmStatus(Number(req.params.index));
    res.json({ success: true, track });
  } catch (err) {
    res.status(500).json({ success: false, error: String(err?.message || err) });
  }
});

let pushedLocators = [];
let pushedLocatorsAt = 0;

const CACHE_DIR = path.resolve('.cache');
const CACHE_FILE = path.join(CACHE_DIR, 'pushed-state.json');

function loadPushedCache() {
  try {
    if (!fs.existsSync(CACHE_FILE)) return;
    const raw = fs.readFileSync(CACHE_FILE, 'utf8');
    const j = JSON.parse(raw);
    if (Array.isArray(j.locators)) pushedLocators = j.locators;
    if (Array.isArray(j.trackArms)) pushedTrackArms = j.trackArms;
    if (typeof j.metronome === 'boolean') pushedMetronome = j.metronome;
    if (typeof j.isPlaying === 'boolean') pushedIsPlaying = j.isPlaying;
    const now = Date.now();
    pushedLocatorsAt = now;
    pushedTrackArmsAt = now;
    pushedMetronomeAt = now;
    pushedIsPlayingAt = now;
  } catch {
    // ignore cache read failures
  }
}

function savePushedCache() {
  try {
    fs.mkdirSync(CACHE_DIR, { recursive: true });
    fs.writeFileSync(CACHE_FILE, JSON.stringify({
      locators: pushedLocators,
      trackArms: pushedTrackArms,
      metronome: pushedMetronome,
      isPlaying: pushedIsPlaying,
      savedAt: Date.now()
    }));
  } catch {
    // ignore cache write failures
  }
}

loadPushedCache();

app.post('/api/locators/push', (req, res) => {
  const locators = Array.isArray(req.body?.locators) ? req.body.locators : [];
  pushedLocators = locators
    .map((l) => ({ name: String(l?.name || ''), beats: Number(l?.beats) }))
    .filter((l) => l.name && Number.isFinite(l.beats))
    .sort((a, b) => a.beats - b.beats);
  pushedLocatorsAt = Date.now();

  const rawMetronome = req.body?.metronome;
  if (rawMetronome !== undefined && rawMetronome !== null) {
    if (typeof rawMetronome === 'boolean') {
      pushedMetronome = rawMetronome;
      pushedMetronomeAt = Date.now();
    } else if (typeof rawMetronome === 'number') {
      pushedMetronome = rawMetronome === 1;
      pushedMetronomeAt = Date.now();
    } else if (typeof rawMetronome === 'string') {
      const v = rawMetronome.trim().toLowerCase();
      if (v === '1' || v === 'true' || v === 'on') {
        pushedMetronome = true;
        pushedMetronomeAt = Date.now();
      } else if (v === '0' || v === 'false' || v === 'off') {
        pushedMetronome = false;
        pushedMetronomeAt = Date.now();
      }
    }
  }

  const rawIsPlaying = req.body?.isPlaying;
  if (rawIsPlaying !== undefined && rawIsPlaying !== null) {
    if (typeof rawIsPlaying === 'boolean') {
      pushedIsPlaying = rawIsPlaying;
      pushedIsPlayingAt = Date.now();
    } else if (typeof rawIsPlaying === 'number') {
      pushedIsPlaying = rawIsPlaying === 1;
      pushedIsPlayingAt = Date.now();
    } else if (typeof rawIsPlaying === 'string') {
      const v = rawIsPlaying.trim().toLowerCase();
      if (v === '1' || v === 'true' || v === 'on') {
        pushedIsPlaying = true;
        pushedIsPlayingAt = Date.now();
      } else if (v === '0' || v === 'false' || v === 'off') {
        pushedIsPlaying = false;
        pushedIsPlayingAt = Date.now();
      }
    }
  }

  const arms = Array.isArray(req.body?.trackArms) ? req.body.trackArms : [];
  if (arms.length) {
    pushedTrackArms = arms
      .map((t) => ({
        index: Number(t?.index),
        name: String(t?.name || ''),
        arm: !!t?.arm,
        mute: !!t?.mute,
        solo: !!t?.solo,
        color: Number(t?.color || 0),
        isGroup: !!t?.isGroup,
        isGrouped: !!t?.isGrouped,
        armable: !t?.isGroup,
        nonArmable: !!t?.isGroup
      }))
      .filter((t) => Number.isFinite(t.index) && t.name.length > 0)
      .sort((a, b) => a.index - b.index);
    pushedTrackArmsAt = Date.now();
  }

  savePushedCache();
  io.emit('state', getMergedState());
  res.json({ success: true, count: pushedLocators.length, armCount: pushedTrackArms.length });
});

app.get('/api/locators', async (_req, res) => {
  try {
    // Prefer pushed locators whenever available (stable UI, no flicker).
    if (pushedLocators.length) {
      return res.json({ success: true, locators: pushedLocators, source: 'pushed' });
    }

    const locators = await getProjectLocators();
    res.json({ success: true, locators, source: 'osc' });
  } catch (err) {
    res.status(500).json({ success: false, error: String(err?.message || err) });
  }
});

const server = http.createServer(app);
const io = new SocketServer(server, { cors: { origin: '*' } });

io.on('connection', (socket) => {
  socket.emit('state', getMergedState());
});

// Push periodic authoritative state updates (tempo/playback + metronome readback best-effort)
let refreshInFlight = false;
setInterval(async () => {
  if (refreshInFlight) return;
  refreshInFlight = true;
  try {
    await enqueueCommand('refresh', {}, 5000);
    io.emit('state', getMergedState());
  } catch {
    // Ignore transient refresh errors; command handlers still return explicit failures.
  } finally {
    refreshInFlight = false;
  }
}, 8000);

const PORT = process.env.PORT || 3030;
server.listen(PORT, '0.0.0.0', () => {
  console.log(`Ableton iOS Remote listening on http://0.0.0.0:${PORT}`);
});
