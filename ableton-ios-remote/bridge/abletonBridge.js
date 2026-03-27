import { execFile } from 'node:child_process';
import { promisify } from 'node:util';

const execFileAsync = promisify(execFile);

const state = {
  connected: false,
  isPlaying: false,
  isRecording: false,
  metronome: false,
  tempo: 120,
  mode: 'ableton-mcp'
};

const MCP_CWD = '/Users/ryantaylorvegh/.openclaw/workspace/ableton-mcp';
const OSC_MCP_BIN = '/opt/homebrew/bin/ableton-osc-mcp';
const MCP_BASE_ARGS = [
  'call',
  '--stdio', 'uv',
  '--stdio-arg', 'run',
  '--stdio-arg', 'python',
  '--stdio-arg', 'MCP_Server/server.py',
  '--server', 'abletonlocal',
  '--output', 'text',
  '--timeout', '30000'
];

export function getState() {
  return { ...state };
}

export async function getArrangementPreview() {
  const info = await mcpTool('get_session_info', {});
  const trackCount = Number(info?.track_count || 0);
  const limit = Math.min(trackCount, 8);
  const tracks = [];

  for (let i = 0; i < limit; i++) {
    try {
      const t = await mcpTool('get_track_info', { track_index: i });
      const clipSlots = Array.isArray(t?.clip_slots) ? t.clip_slots : [];
      const clipCount = clipSlots.filter((s) => s?.has_clip).length;
      tracks.push({
        index: t?.index ?? i,
        name: t?.name || `Track ${i + 1}`,
        arm: !!t?.arm,
        mute: !!t?.mute,
        solo: !!t?.solo,
        isAudio: !!t?.is_audio_track,
        isMidi: !!t?.is_midi_track,
        clipCount,
        deviceCount: Array.isArray(t?.devices) ? t.devices.length : 0
      });
    } catch {
      tracks.push({
        index: i,
        name: `Track ${i + 1}`,
        error: true
      });
    }
  }

  return {
    generatedAt: new Date().toISOString(),
    trackCount,
    showing: limit,
    signatureNumerator: Number(info?.signature_numerator || 4),
    signatureDenominator: Number(info?.signature_denominator || 4),
    tracks
  };
}

export async function getTrackArmPreview() {
  const info = await mcpTool('get_session_info', {});
  const trackCount = Number(info?.track_count || 0);
  const limit = Math.min(trackCount, 64);

  const raw = await Promise.all(
    Array.from({ length: limit }, async (_, i) => {
      try {
        const t = await mcpTool('get_track_info', { track_index: i });

        // mcpTool can return plain-text errors as { ok, text }.
        if (!Number.isInteger(t?.index)) {
          const txt = String(t?.text || '');
          const nonArmable = txt.includes("have no 'Arm' state");
          return {
            index: i,
            name: `Track ${i + 1}`,
            arm: false,
            mute: false,
            solo: false,
            armable: !nonArmable,
            nonArmable,
            error: !nonArmable
          };
        }

        return {
          index: t.index,
          name: t?.name || `Track ${i + 1}`,
          arm: !!t?.arm,
          mute: !!t?.mute,
          solo: !!t?.solo,
          armable: true,
          nonArmable: false
        };
      } catch {
        return { index: i, name: `Track ${i + 1}`, error: true, armable: false, nonArmable: false };
      }
    })
  );

  const tracks = raw.filter((t) => t.armable);
  const hiddenNonArmable = raw.filter((t) => t.nonArmable).length;

  return { trackCount, showing: tracks.length, hiddenNonArmable, tracks };
}

export async function getTrackArmStatus(trackIndex) {
  const idx = Number(trackIndex);
  if (!Number.isInteger(idx) || idx < 0) throw new Error('Invalid track index');

  const t = await mcpTool('get_track_info', { track_index: idx });
  if (!Number.isInteger(t?.index)) throw new Error('Track info unavailable');

  return {
    index: t.index,
    name: t?.name || `Track ${idx + 1}`,
    arm: !!t?.arm,
    mute: !!t?.mute,
    solo: !!t?.solo
  };
}

export async function getProjectLocators() {
  const candidates = [
    '/live/song/get/locators',
    '/live/song/get/cue_points',
    '/live/song/get/arrangement_locators'
  ];

  for (const address of candidates) {
    try {
      const res = await oscSend(address, []);
      const locators = extractLocators(String(res?.text || ''));
      if (locators.length) return locators;
    } catch {
      // try next endpoint
    }
  }

  return [];
}

export async function runCommand(command, payload = {}) {
  try {
    switch (command) {
      case 'play':
        try {
          await oscSend('/live/song/continue_playing', []);
        } catch {
          await mcpTool('start_playback', {});
        }
        state.isPlaying = true;
        await refreshState();
        return ok();

      case 'stop':
        try {
          await oscSend('/live/song/stop_playing', []);
        } catch {
          await mcpTool('stop_playback', {});
        }
        state.isPlaying = false;
        state.isRecording = false;
        await refreshState();
        return ok();

      case 'setTempo': {
        const tempo = Number(payload.tempo);
        if (!Number.isFinite(tempo) || tempo < 20 || tempo > 999) {
          return fail('Invalid tempo value');
        }
        await mcpTool('set_tempo', { tempo });
        state.tempo = tempo;
        await refreshState();
        return ok();
      }

      case 'nudgeTempo': {
        const delta = Number(payload.delta || 0);
        if (!Number.isFinite(delta)) return fail('Invalid tempo delta');
        await refreshState();
        const nextTempo = Math.max(20, Math.min(999, Number(state.tempo || 120) + delta));
        await mcpTool('set_tempo', { tempo: nextTempo });
        state.tempo = nextTempo;
        await refreshState();
        return ok();
      }

      case 'record': {
        const next = state.isRecording ? 0 : 1;

        // Prefer Arrangement Record (record_mode). If unavailable, fall back to session_record.
        try {
          await oscSend('/live/song/set/record_mode', [next]);
        } catch {
          await oscOrKeystroke('/live/song/set/session_record', [next], async () => sendFunctionKey(9));
        }

        // Keep UI responsive even if readback is unavailable in this environment.
        state.isRecording = next === 1;
        if (state.isRecording) state.isPlaying = true;

        await refreshRecordState();
        return ok();
      }

      case 'playFromPosition': {
        const beats = Number(payload.beats);
        if (!Number.isFinite(beats) || beats < 0) return fail('Invalid marker position');

        // Behavior split:
        // - If already playing: just jump to locator (no stop/start churn).
        // - If stopped: set position first, then start playback.
        await refreshState();

        if (state.isPlaying) {
          await oscSend('/live/song/set/current_song_time', [beats]);
        } else {
          // In stopped state, start transport first, then jump.
          // This avoids certain Live sessions snapping to Song Start Marker.
          try {
            await oscSend('/live/song/start_playing', []);
          } catch {
            await mcpTool('start_playback', {});
          }
          await sleep(60);
          await oscSend('/live/song/set/current_song_time', [beats]);
        }

        state.isPlaying = true;
        await refreshState();
        return ok();
      }

      case 'recordFromPosition': {
        const beats = Number(payload.beats);
        if (!Number.isFinite(beats) || beats < 0) return fail('Invalid marker position');
        await oscSend('/live/song/set/current_song_time', [beats]);
        await sleep(80);
        try {
          await oscSend('/live/song/set/record_mode', [1]);
          state.isRecording = true;
        } catch {
          // keep going even if readback/control is partial in this environment
        }
        try {
          await oscSend('/live/song/continue_playing', []);
        } catch {
          await mcpTool('start_playback', {});
        }
        state.isPlaying = true;
        await refreshState();
        await refreshRecordState();
        return ok();
      }

      case 'setTrackArm': {
        const trackIndex = Number(payload.trackIndex);
        const trackName = String(payload.trackName || '');
        const arm = !!payload.arm;
        if (!Number.isInteger(trackIndex) || trackIndex < 0) return fail('Invalid track index');

        await setTrackArmAutoIndex(trackIndex, trackName, arm);
        return ok();
      }

      case 'seekAndStop': {
        const beats = Number(payload.beats);
        if (!Number.isFinite(beats) || beats < 0) return fail('Invalid marker position');
        await oscSend('/live/song/set/current_song_time', [beats]);
        await sleep(50);
        try {
          await oscSend('/live/song/stop_playing', []);
        } catch {
          await mcpTool('stop_playback', {});
        }
        state.isPlaying = false;
        await refreshState();
        return ok();
      }

      case 'tapTempo':
        await oscSend('/live/song/tap_tempo', []);
        await refreshState();
        return ok();

      case 'toggleMetronome': {
        const next = state.metronome ? 0 : 1;

        // Try explicit OSC set first.
        await oscOrKeystroke('/live/song/set/metronome', [next], async () => sendChord('m', ['command down', 'shift down']));

        // If OSC readback isn't available in this environment, use keyboard fallback once
        // to ensure there's still a practical control path.
        const hadReadback = await refreshMetronomeState();
        if (!hadReadback) {
          try {
            await sendChord('m', ['command down', 'shift down']);
          } catch {
            // If Live isn't frontable from this host context, keep optimistic state.
          }
          state.metronome = !state.metronome;
        }

        return ok();
      }

      case 'undo':
        await oscOrKeystroke('/live/song/undo', [], async () => sendChord('z', ['command down']));
        return ok();

      case 'refresh':
        await refreshState();
        await refreshMetronomeState();
        await refreshRecordState();
        return ok();

      default:
        return fail(`Unknown command: ${command}`);
    }
  } catch (err) {
    state.connected = false;
    return fail(`Ableton command failed: ${err.message || err}`);
  }
}

async function refreshState() {
  const info = await mcpTool('get_session_info', {});
  state.connected = true;

  // MCP is_playing can be stale in some sessions; prefer OSC readback when available.
  const oscPlaying = await readTransportPlayingFromOsc();
  if (typeof oscPlaying === 'boolean') {
    state.isPlaying = oscPlaying;
  } else if (typeof info.is_playing === 'boolean') {
    state.isPlaying = info.is_playing;
  }

  state.tempo = Number(info.tempo || state.tempo || 120);
  return state;
}

async function mcpTool(tool, args = {}) {
  const cmdArgs = [
    ...MCP_BASE_ARGS,
    '--tool', tool,
    '--args', JSON.stringify(args)
  ];

  const { stdout, stderr } = await execFileAsync('mcporter', cmdArgs, {
    cwd: MCP_CWD,
    timeout: 35000,
    maxBuffer: 1024 * 1024
  });

  const parsed = extractJsonObject(stdout || '');
  if (parsed) return parsed;

  // Some tools return plain text success lines (e.g., start/stop playback)
  const text = String(stdout || '').trim();
  if (text.length > 0) return { ok: true, text };

  throw new Error(`MCP parse failed for ${tool}${stderr ? ` (${stderr.trim()})` : ''}`);
}

async function oscSend(address, args = []) {
  // ableton-osc-mcp currently expects OSC args as strings in its schema.
  const normalizedArgs = Array.isArray(args) ? args.map((v) => String(v)) : [];

  const cmdArgs = [
    'call',
    '--stdio', OSC_MCP_BIN,
    '--server', 'abletonosc',
    '--tool', 'ableton_osc_send',
    '--args', JSON.stringify({ address, args: normalizedArgs }),
    '--output', 'text',
    '--timeout', '15000'
  ];

  const { stdout, stderr } = await execFileAsync('mcporter', cmdArgs, {
    timeout: 20000,
    maxBuffer: 1024 * 1024
  });

  const text = String(stdout || '').trim();
  if (!text) {
    throw new Error(`OSC send failed for ${address}${stderr ? ` (${stderr.trim()})` : ''}`);
  }
  return { ok: true, text };
}

async function refreshMetronomeState() {
  const addresses = [
    '/live/song/get/metronome',
    '/live/song/get/metro',
    '/live/song/get/click'
  ];

  for (const address of addresses) {
    try {
      const res = await oscSend(address, []);
      const parsed = extractMetronomeValue(String(res?.text || ''));
      if (parsed !== null) {
        state.metronome = parsed;
        return true;
      }
    } catch {
      // try next address
    }
  }

  // Keep existing state if readback fails.
  return false;
}

function extractMetronomeValue(text) {
  if (!text) return null;

  if (/\b(true|on)\b/i.test(text)) return true;
  if (/\b(false|off)\b/i.test(text)) return false;

  // Common patterns seen across wrappers/versions.
  const patterns = [
    /metronome[^0-9]*([01])/i,
    /metro[^0-9]*([01])/i,
    /click[^0-9]*([01])/i,
    /value[^0-9-]*([01])/i,
    /args?[^0-9-]*\[?\s*([01])\s*\]?/i,
    /([01])\s*$/
  ];

  for (const re of patterns) {
    const m = text.match(re);
    if (m?.[1] === '0' || m?.[1] === '1') return m[1] === '1';
  }

  return null;
}

async function refreshRecordState() {
  // Prefer Arrangement Record (record_mode), then fall back to session_record.
  try {
    const res = await oscSend('/live/song/get/record_mode', []);
    const parsed = extractBinaryFlag(String(res?.text || ''), 'record_mode');
    if (parsed !== null) {
      state.isRecording = parsed;
      return true;
    }
  } catch {
    // continue to fallback
  }

  try {
    const res = await oscSend('/live/song/get/session_record', []);
    const parsed = extractBinaryFlag(String(res?.text || ''), 'session_record');
    if (parsed !== null) {
      state.isRecording = parsed;
      return true;
    }
    return false;
  } catch {
    return false;
  }
}

function extractBinaryFlag(text, key) {
  if (!text) return null;
  const patterns = [
    new RegExp(`${key}[^0-9]*([01])`, 'i'),
    /value[^0-9-]*([01])/i,
    /args?[^0-9-]*\[?\s*([01])\s*\]?/i,
    /([01])\s*$/
  ];
  for (const re of patterns) {
    const m = text.match(re);
    if (m?.[1] === '0' || m?.[1] === '1') return m[1] === '1';
  }
  return null;
}

async function readTransportPlayingFromOsc() {
  const addresses = [
    '/live/song/get/is_playing',
    '/live/song/get/playing_status'
  ];

  for (const address of addresses) {
    try {
      const res = await oscSend(address, []);
      const txt = String(res?.text || '');
      const parsed = extractBinaryFlag(txt, 'is_playing') ?? extractBinaryFlag(txt, 'playing_status');
      if (parsed !== null) return parsed;
    } catch {
      // try next
    }
  }

  return null;
}

function extractLocators(text) {
  if (!text) return [];
  const out = [];

  // Try JSON array payload if present.
  const arrMatch = text.match(/\[[\s\S]*\]/);
  if (arrMatch) {
    try {
      const arr = JSON.parse(arrMatch[0]);
      if (Array.isArray(arr)) {
        for (const item of arr) {
          if (item && (item.name || item.label) && Number.isFinite(Number(item.time ?? item.beats))) {
            out.push({ name: String(item.name || item.label), beats: Number(item.time ?? item.beats) });
          }
        }
      }
    } catch {
      // ignore parse failure
    }
  }

  // Fallback: parse "name:..., beats:..." chunks.
  const re = /name[:=]\s*([^,\]]+).*?(?:beats|time)[:=]\s*([0-9.]+)/gi;
  let m;
  while ((m = re.exec(text)) !== null) {
    out.push({ name: m[1].trim(), beats: Number(m[2]) });
  }

  return out.slice(0, 32);
}

async function oscOrKeystroke(address, args, keystrokeFallback) {
  try {
    await oscSend(address, args);
  } catch {
    await keystrokeFallback();
  }
}

async function setTrackArmAutoIndex(trackIndex, trackName, arm) {
  // Different AbletonOSC setups may behave as 0-based or 1-based.
  const candidates = [trackIndex, trackIndex + 1, Math.max(0, trackIndex - 1)];

  for (const idx of candidates) {
    await oscSend('/live/track/set/arm', [idx, arm ? 1 : 0]);
    await sleep(80);

    try {
      const t = await mcpTool('get_track_info', { track_index: trackIndex });
      const confirmed = typeof t?.arm === 'boolean' ? t.arm : null;
      if (confirmed === arm) return;
    } catch {
      // If verification fails, try next candidate.
    }
  }
}
async function sendKeystroke(key) {
  await runAppleScript(`
    tell application "System Events"
      set liveProc to first process whose name starts with "Ableton Live"
      set frontmost of liveProc to true
    end tell
    delay 0.08
    tell application "System Events"
      keystroke "${key}"
    end tell
  `);
}

async function sendChord(key, modifiers = []) {
  const modList = `{${modifiers.join(', ')}}`;
  await runAppleScript(`
    tell application "System Events"
      set liveProc to first process whose name starts with "Ableton Live"
      set frontmost of liveProc to true
    end tell
    delay 0.08
    tell application "System Events"
      keystroke "${key}" using ${modList}
    end tell
  `);
}

async function sendFunctionKey(n) {
  const keyCodes = {
    1: 122,
    2: 120,
    3: 99,
    4: 118,
    5: 96,
    6: 97,
    7: 98,
    8: 100,
    9: 101,
    10: 109,
    11: 103,
    12: 111
  };
  const code = keyCodes[n];
  if (!code) throw new Error(`Unsupported function key: F${n}`);

  await runAppleScript(`
    tell application "System Events"
      set liveProc to first process whose name starts with "Ableton Live"
      set frontmost of liveProc to true
    end tell
    delay 0.08
    tell application "System Events"
      key code ${code}
    end tell
  `);
}

async function runAppleScript(script) {
  await execFileAsync('osascript', ['-e', script]);
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
        try {
          return JSON.parse(candidate);
        } catch {
          return null;
        }
      }
    }
  }

  return null;
}

function ok() {
  return { success: true, state: getState() };
}

function fail(error) {
  return { success: false, error, state: getState() };
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
