// Node for Max: locator_post.js
// Receives locator payload JSON from Max and POSTs to iOS remote.
// Includes lightweight watchdog + throttle + dedupe to reduce long-run drift.

const Max = require('max-api');

const ENDPOINT = process.env.ABLETON_IOS_REMOTE_LOCATORS || 'http://127.0.0.1:3030/api/locators/push';

const state = {
  lastSentAt: 0,
  lastPayloadHash: '',
  lastPayloadAt: 0,
  minIntervalMs: Number(process.env.LOCATOR_POST_MIN_INTERVAL_MS || 120),
  dedupeWindowMs: Number(process.env.LOCATOR_POST_DEDUPE_MS || 1200),
  sent: 0,
  skippedRate: 0,
  skippedDup: 0,
  errors: 0,
  watchdogTimer: null,
  watchdogEveryMs: Number(process.env.LOCATOR_WATCHDOG_MS || 30000),
  warnHeapMb: Number(process.env.LOCATOR_WATCHDOG_WARN_MB || 180),
};

function payloadHash(text) {
  // Lightweight stable-ish hash (good enough for dedupe)
  let h = 2166136261;
  for (let i = 0; i < text.length; i++) {
    h ^= text.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return String(h >>> 0);
}

function shouldSkip(text) {
  const now = Date.now();

  if (now - state.lastSentAt < state.minIntervalMs) {
    state.skippedRate++;
    return 'rate';
  }

  const hash = payloadHash(text);
  if (hash === state.lastPayloadHash && (now - state.lastPayloadAt) < state.dedupeWindowMs) {
    state.skippedDup++;
    return 'dup';
  }

  state.lastPayloadHash = hash;
  state.lastPayloadAt = now;
  return null;
}

async function postPayload(raw) {
  try {
    const text = Array.isArray(raw) ? raw.join(' ') : String(raw);
    const payload = JSON.parse(text);

    const skip = shouldSkip(text);
    if (skip) {
      Max.outlet(['skip', skip]);
      return;
    }

    const res = await fetch(ENDPOINT, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(payload),
    });

    const body = await res.text();
    state.sent++;
    state.lastSentAt = Date.now();
    Max.post(`locator_post: ${res.status} ${body}`);
    Max.outlet(['ok', res.status]);
  } catch (e) {
    state.errors++;
    Max.post(`locator_post error: ${e.message}`);
    Max.outlet(['error', String(e.message)]);
  }
}

function reportStats() {
  const mem = process.memoryUsage();
  const rssMb = Math.round(mem.rss / 1024 / 1024);
  const heapMb = Math.round(mem.heapUsed / 1024 / 1024);

  Max.post(`locator_post stats: sent=${state.sent} err=${state.errors} skipRate=${state.skippedRate} skipDup=${state.skippedDup} rss=${rssMb}MB heap=${heapMb}MB minInterval=${state.minIntervalMs}ms`);
  Max.outlet(['stats', JSON.stringify({
    sent: state.sent,
    errors: state.errors,
    skippedRate: state.skippedRate,
    skippedDup: state.skippedDup,
    rssMb,
    heapMb,
    minIntervalMs: state.minIntervalMs,
  })]);

  if (heapMb >= state.warnHeapMb) {
    // Auto-throttle a bit when memory climbs; suggest restart.
    state.minIntervalMs = Math.max(state.minIntervalMs, 400);
    Max.post(`locator_post watchdog: high heap (${heapMb}MB). Throttling minInterval to ${state.minIntervalMs}ms.`);
    Max.outlet(['restart_recommended', String(heapMb)]);
  }
}

function startWatchdog() {
  if (state.watchdogTimer) return;
  state.watchdogTimer = setInterval(reportStats, state.watchdogEveryMs);
  Max.post(`locator_post watchdog started (${state.watchdogEveryMs}ms)`);
}

function stopWatchdog() {
  if (!state.watchdogTimer) return;
  clearInterval(state.watchdogTimer);
  state.watchdogTimer = null;
  Max.post('locator_post watchdog stopped');
}

Max.addHandler('anything', (...args) => postPayload(args));
Max.addHandler('list', (...args) => postPayload(args));
Max.addHandler('post', (...args) => postPayload(args));

Max.addHandler('stats', () => reportStats());
Max.addHandler('watchdog_on', (...args) => {
  const ms = Number(args?.[0]);
  if (Number.isFinite(ms) && ms >= 5000) state.watchdogEveryMs = ms;
  startWatchdog();
});
Max.addHandler('watchdog_off', () => stopWatchdog());
Max.addHandler('set_min_interval', (...args) => {
  const ms = Number(args?.[0]);
  if (Number.isFinite(ms) && ms >= 0) state.minIntervalMs = ms;
  Max.post(`locator_post minInterval set to ${state.minIntervalMs}ms`);
});

startWatchdog();
