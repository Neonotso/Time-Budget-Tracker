// BridgeTelemetry.js
// Max js script for duck telemetry payload shaping.
// v2: dynamic baseline + uncapped raw metric to avoid saturation.

inlets = 2;   // 0: pad level linear, 1: kick hit flag (0/1)
outlets = 1;  // JSON lines

var trackId = "track-6";
var kickTrackId = "track-4";
var windowMs = 120;

var recent = [];
var maxRecent = 48;
var peakHold = 0;

// Baseline follower: slow attack/decay so it tracks overall loudness but not instant duck dips.
var baseline = 0;
var alphaUp = 0.04;   // baseline rises slowly
var alphaDown = 0.01; // baseline falls very slowly

function set_track_id(v) { trackId = String(v); }
function set_kick_track_id(v) { kickTrackId = String(v); }
function set_window_ms(v) { windowMs = parseInt(v, 10) || 120; }

function _median(arr) {
  if (!arr.length) return 0;
  var s = arr.slice().sort(function(a,b){return a-b;});
  var m = Math.floor(s.length/2);
  return s.length % 2 ? s[m] : (s[m-1]+s[m])/2;
}

function _clamp(v, lo, hi) {
  return Math.max(lo, Math.min(hi, v));
}

function msg_float(v) {
  if (inlet !== 0) return;

  var x = Number(v);
  if (!isFinite(x)) return;
  x = _clamp(x, 0.000001, 1.0);

  if (baseline <= 0) baseline = x;

  // follow signal slowly to estimate "pre-duck" loudness context
  if (x > baseline) baseline = baseline + alphaUp * (x - baseline);
  else baseline = baseline + alphaDown * (x - baseline);

  var eps = 1e-6;
  var rawDuckDb = 20.0 * Math.log((baseline + eps) / (x + eps)) / Math.LN10;
  if (!isFinite(rawDuckDb) || rawDuckDb < 0) rawDuckDb = 0;

  // clamp extreme startup/transient spikes to a practical range
  var duckDb = _clamp(rawDuckDb, 0, 24);

  // normalized helper metric (same scale for now)
  var normDuckDb = duckDb;

  recent.push(duckDb);
  if (recent.length > maxRecent) recent.shift();

  var peak = 0;
  for (var i = 0; i < recent.length; i++) if (recent[i] > peak) peak = recent[i];
  // smooth peak hold with gentle decay for readability
  peakHold = Math.max(peak, peakHold * 0.985);
  var med = _median(recent);

  var hit = 0;
  if (typeof global_kick_hit !== 'undefined') hit = global_kick_hit;

  var payload = {
    topic: "duck_telemetry",
    version: 2,
    ts: new Date().getTime(),
    trackId: trackId,
    kickTrackId: kickTrackId,
    windowMs: windowMs,
    instDuckDb: duckDb,
    peakDuckDb: peakHold,
    medianDuckDb: med,
    instDuckDbNorm: normDuckDb,
    baselineLevel: baseline,
    levelNow: x,
    hit: !!hit
  };

  outlet(0, JSON.stringify(payload));
}

var global_kick_hit = 0;
function msg_int(v) {
  if (inlet !== 1) return;
  global_kick_hit = v ? 1 : 0;
}
