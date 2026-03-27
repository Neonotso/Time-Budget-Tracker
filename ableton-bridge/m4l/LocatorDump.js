// Max js (not Node): lightweight observer-driven push for transport + metronome + locators.
// Designed to avoid Live UI slowdown.
// Usage:
// [loadbang] -> [js LocatorDump.js] -> [prepend post] -> [node.script locator_post.js]
// Optional: [qmetro 3000] -> [js LocatorDump.js] for periodic locator refresh.

autowatch = 1;
inlets = 1;
outlets = 1;

var observedSongApi = [];
var cache = {
  locators: [],
  metronome: false,
  isPlaying: false,
  trackArms: []
};
var lastSentJson = '';
var lastLocatorRefreshMs = 0;
var lastTrackRefreshMs = 0;

function loadbang() {
  init();
}

function bang() {
  // Manual / slow periodic refresh path.
  refreshAll(true);
  emitIfChanged();
}

function init() {
  try {
    clearObservers();

    observeSongProperty('is_playing');
    observeSongProperty('metronome');

    refreshAll(true);
    emitIfChanged(true);

    post('LocatorDump: lightweight mode initialized\n');
  } catch (e) {
    post('LocatorDump init error: ' + e + '\n');
  }
}

function refresh() {
  bang();
}

function observeSongProperty(prop) {
  var api = new LiveAPI(songObserverCallback, 'live_set');
  api.property = prop;
  observedSongApi.push(api);
}

function songObserverCallback() {
  refreshSongFlags();
  emitIfChanged();
}

function refreshAll(forceLocators) {
  refreshSongFlags();
  refreshLocatorsMaybe(!!forceLocators);
  refreshTrackArmsMaybe(!!forceLocators);
}

function refreshSongFlags() {
  try {
    var song = new LiveAPI('live_set');

    var metronome = song.get('metronome');
    if (metronome && metronome.length !== undefined) metronome = metronome[0];

    var isPlaying = song.get('is_playing');
    if (isPlaying && isPlaying.length !== undefined) isPlaying = isPlaying[0];

    cache.metronome = Number(metronome || 0) === 1;
    cache.isPlaying = Number(isPlaying || 0) === 1;
  } catch (e) {
    post('LocatorDump refreshSongFlags error: ' + e + '\n');
  }
}

function refreshLocatorsMaybe(force) {
  var now = Date.now();
  if (!force && now - lastLocatorRefreshMs < 10000) return;

  try {
    var song = new LiveAPI('live_set');
    var count = song.getcount('cue_points');
    var locators = [];

    for (var i = 0; i < count; i++) {
      var cue = new LiveAPI('live_set cue_points ' + i);
      var name = cue.get('name');
      var time = cue.get('time');

      if (name && name.length !== undefined) name = name[0];
      if (time && time.length !== undefined) time = time[0];

      locators.push({
        name: String(name || ('Locator ' + (i + 1))),
        beats: Number(time || 0)
      });
    }

    cache.locators = locators;
    lastLocatorRefreshMs = now;
  } catch (e) {
    post('LocatorDump refreshLocators error: ' + e + '\n');
  }
}

function emitIfChanged(force) {
  var payload = {
    locators: cache.locators,
    metronome: cache.metronome,
    isPlaying: cache.isPlaying,
    trackArms: cache.trackArms
  };

  var json = JSON.stringify(payload);
  if (!force && json === lastSentJson) return;

  lastSentJson = json;
  outlet(0, json);
}

function refreshTrackArmsMaybe(force) {
  var now = Date.now();
  // Keep arm payload low-frequency to avoid Live UI slowdown.
  if (!force && now - lastTrackRefreshMs < 5000) return;

  try {
    var song = new LiveAPI('live_set');
    var trackCount = song.getcount('tracks');
    var trackArms = [];

    for (var t = 0; t < trackCount; t++) {
      try {
        var tr = new LiveAPI('live_set tracks ' + t);
        var tName = tr.get('name');
        var tMute = tr.get('mute');
        var tSolo = tr.get('solo');
        var tColor = tr.get('color');
        var tFoldable = tr.get('is_foldable');
        var tGrouped = tr.get('is_grouped');

        // Critical: guard arm reads to avoid console spam on return/master/group tracks.
        var canBeArmed = tr.get('can_be_armed');
        if (canBeArmed && canBeArmed.length !== undefined) canBeArmed = canBeArmed[0];
        var tArm = 0;
        if (Number(canBeArmed || 0) === 1) {
          var armVal = tr.get('arm');
          if (armVal && armVal.length !== undefined) armVal = armVal[0];
          tArm = Number(armVal || 0);
        }

        if (tName && tName.length !== undefined) tName = tName[0];
        if (tMute && tMute.length !== undefined) tMute = tMute[0];
        if (tSolo && tSolo.length !== undefined) tSolo = tSolo[0];
        if (tColor && tColor.length !== undefined) tColor = tColor[0];
        if (tFoldable && tFoldable.length !== undefined) tFoldable = tFoldable[0];
        if (tGrouped && tGrouped.length !== undefined) tGrouped = tGrouped[0];

        trackArms.push({
          index: t,
          name: String(tName || ('Track ' + (t + 1))),
          arm: Number(tArm || 0) === 1,
          mute: Number(tMute || 0) === 1,
          solo: Number(tSolo || 0) === 1,
          color: Number(tColor || 0),
          isGroup: Number(tFoldable || 0) === 1,
          isGrouped: Number(tGrouped || 0) === 1,
          canBeArmed: Number(canBeArmed || 0) === 1
        });
      } catch (_ignored) {
        // Skip odd tracks if LiveAPI still rejects a property read.
      }
    }

    cache.trackArms = trackArms;
    lastTrackRefreshMs = now;
  } catch (e) {
    post('LocatorDump refreshTrackArms error: ' + e + '\n');
  }
}

function clearObservers() {
  try {
    for (var i = 0; i < observedSongApi.length; i++) {
      try { observedSongApi[i].property = ''; } catch (_e) {}
    }
  } catch (_e2) {}
  observedSongApi = [];
}

function reset() {
  init();
}
