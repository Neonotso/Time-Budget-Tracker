const socket = io();
const statusEl = document.getElementById('status');
const tempoInput = document.getElementById('tempoInput');
const trackArmListEl = document.getElementById('trackArmList');
const locatorListEl = document.getElementById('locatorList');
const countInRow = document.getElementById('countInRow');
const transportPanel = document.getElementById('transportPanel');
const transportToggle = document.getElementById('transportToggle');
const countInPanel = document.getElementById('countInPanel');
const countInToggle = document.getElementById('countInToggle');
const locatorPanel = document.getElementById('locatorPanel');
const locatorToggle = document.getElementById('locatorToggle');
const trackArmPanel = document.getElementById('trackArmPanel');
const trackArmToggle = document.getElementById('trackArmToggle');

let beatsPerBar = 4;
let countInBars = 2;
const pendingArm = new Map();
const armOverride = new Map();
const collapsedGroups = new Set();
let pendingTempo = null;
let tempoSendTimer = null;
let tempoHoldTimeout = null;
let tempoHoldInterval = null;
let tempoTouchStartY = null;
let tempoTouchLastStep = 0;

socket.on('state', (state) => renderState(state));

const commandButtons = {
  play: document.querySelector('button[data-cmd="play"]'),
  stop: document.querySelector('button[data-cmd="stop"]'),
  record: document.querySelector('button[data-cmd="record"]'),
  metronome: document.querySelector('button[data-cmd="toggleMetronome"]')
};

document.querySelectorAll('button[data-cmd]').forEach((btn) => {
  btn.addEventListener('click', async (e) => {
    e.preventDefault();
    btn.classList.add('pressed');
    setTimeout(() => btn.classList.remove('pressed'), 180);

    if (btn.dataset.cmd === 'stop') {
      btn.classList.add('flash-red');
      setTimeout(() => btn.classList.remove('flash-red'), 500);
    }

    const data = await send(btn.dataset.cmd);
    if (data?.state) renderState(data.state);
    await postCommandRefresh(btn.dataset.cmd);
  });
  btn.addEventListener('contextmenu', (e) => e.preventDefault());
});

const tempoUpBtn = document.getElementById('tempoUp');
const tempoDownBtn = document.getElementById('tempoDown');

tempoUpBtn.addEventListener('click', () => adjustTempoByStep(+1));
tempoDownBtn.addEventListener('click', () => adjustTempoByStep(-1));

setupTempoHold(tempoUpBtn, +1);
setupTempoHold(tempoDownBtn, -1);

tempoInput.addEventListener('change', () => {
  const next = Number(tempoInput.value);
  if (!Number.isFinite(next)) return;
  pendingTempo = { value: next, expiresAt: Date.now() + 2500 };
  tempoInput.value = String(next);
  queueTempoSend();
});

tempoInput.addEventListener('wheel', (e) => {
  e.preventDefault();
  adjustTempoByStep(e.deltaY < 0 ? +1 : -1);
}, { passive: false });

tempoInput.addEventListener('touchstart', (e) => {
  if (!e.touches || e.touches.length !== 1) return;
  tempoTouchStartY = e.touches[0].clientY;
  tempoTouchLastStep = 0;
}, { passive: true });

tempoInput.addEventListener('touchmove', (e) => {
  if (tempoTouchStartY === null || !e.touches || e.touches.length !== 1) return;
  const dy = tempoTouchStartY - e.touches[0].clientY;
  const step = Math.trunc(dy / 6);
  const deltaSteps = step - tempoTouchLastStep;
  if (deltaSteps !== 0) {
    const dir = deltaSteps > 0 ? +1 : -1;
    for (let i = 0; i < Math.abs(deltaSteps); i++) adjustTempoByStep(dir);
    tempoTouchLastStep = step;
  }
  e.preventDefault();
}, { passive: false });

tempoInput.addEventListener('touchend', () => {
  tempoTouchStartY = null;
  tempoTouchLastStep = 0;
});

document.querySelectorAll('button[data-countin]').forEach((btn) => {
  btn.addEventListener('click', () => {
    countInBars = Number(btn.dataset.countin || 0);
    countInRow.querySelectorAll('button[data-countin]').forEach((b) => {
      b.classList.toggle('active-green', b === btn);
    });
  });
});

transportToggle?.addEventListener('click', () => {
  transportPanel.classList.toggle('collapsed');
  transportToggle.textContent = transportPanel.classList.contains('collapsed') ? 'Show' : 'Hide';
  updateStickyOffsets();
});

countInToggle?.addEventListener('click', () => {
  countInPanel.classList.toggle('collapsed');
  countInToggle.textContent = countInPanel.classList.contains('collapsed') ? 'Show' : 'Hide';
});

locatorToggle?.addEventListener('click', () => {
  locatorPanel.classList.toggle('collapsed');
  locatorToggle.textContent = locatorPanel.classList.contains('collapsed') ? 'Show' : 'Hide';
});

trackArmToggle?.addEventListener('click', () => {
  trackArmPanel.classList.toggle('collapsed');
  trackArmToggle.textContent = trackArmPanel.classList.contains('collapsed') ? 'Show' : 'Hide';
});

function updateStickyOffsets() {
  const h = transportPanel?.getBoundingClientRect?.().height || 96;
  document.documentElement.style.setProperty('--transport-offset', `${Math.round(h + 8)}px`);
}

window.addEventListener('resize', updateStickyOffsets);

updateStickyOffsets();
refreshTrackArms();
refreshLocators();
syncInitialState();
// No constant tight polling: only slow safety refreshes.
setInterval(refreshTrackArms, 120000);
setInterval(refreshLocators, 120000);

async function send(cmd, body = {}) {
  const res = await fetch(`/api/command/${cmd}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  const data = await res.json();
  if (!res.ok) {
    alert(data.error || 'Command failed');
    return null;
  }
  return data;
}

async function refreshStateNow() {
  try {
    const res = await fetch('/api/state');
    const state = await res.json();
    renderState(state);
  } catch {
    // ignore transient state read errors
  }
}

async function postCommandRefresh(cmd) {
  // For arm-only actions, avoid overriding transport state with stale snapshots.
  if (cmd === 'setTrackArm') {
    await refreshTrackArms({ live: true });
    setTimeout(() => refreshTrackArms(), 500);
    setTimeout(() => refreshTrackArms(), 1100);
    setTimeout(() => refreshTrackArms(), 1900);
    setTimeout(() => refreshTrackArms(), 2800);
    return;
  }

  await refreshStateNow();

  if (cmd === 'play' || cmd === 'stop' || cmd === 'record' || cmd === 'playFromPosition' || cmd === 'recordFromPosition') {
    setTimeout(refreshStateNow, 600);
    setTimeout(refreshStateNow, 1400);
    setTimeout(refreshStateNow, 2600);
  }
}

async function syncInitialState() {
  const data = await send('refresh');
  if (data?.state) renderState(data.state);
  await refreshTrackArms();

  // Short startup burst, then stop.
  setTimeout(refreshStateNow, 600);
  setTimeout(refreshStateNow, 1400);
  setTimeout(refreshStateNow, 2600);
  setTimeout(refreshTrackArms, 1200);
  setTimeout(refreshTrackArms, 2800);
}

function renderState(state) {
  statusEl.textContent = `Connected: ${state.connected ? 'Yes' : 'No'} | Play: ${state.isPlaying ? 'On' : 'Off'} | Rec: ${state.isRecording ? 'On' : 'Off'} | Metro: ${state.metronome ? 'On' : 'Off'}`;

  const pendingActive = pendingTempo && pendingTempo.expiresAt > Date.now();
  if (pendingActive) {
    tempoInput.value = String(pendingTempo.value);
  } else {
    pendingTempo = null;
    tempoInput.value = String(Number(state.tempo));
  }

  commandButtons.play?.classList.toggle('active-green', !!state.isPlaying);
  commandButtons.record?.classList.toggle('danger', !state.isRecording);
  commandButtons.record?.classList.toggle('active-green', !!state.isRecording);
  commandButtons.metronome?.classList.toggle('active-orange', !!state.metronome);
}


async function refreshTrackArms(options = {}) {
  try {
    const qs = options.live ? '?live=1' : '';
    const res = await fetch(`/api/tracks${qs}`);
    const data = await res.json();
    if (!res.ok || !data?.success) {
      trackArmListEl.textContent = data?.error || 'Track list unavailable';
      return;
    }
    renderTrackArms(data.preview);
  } catch {
    trackArmListEl.textContent = 'Track list unavailable';
  }
}

function queueTempoSend() {
  if (tempoSendTimer) clearTimeout(tempoSendTimer);
  tempoSendTimer = setTimeout(() => {
    // Always send the latest on-screen value (not an intermediate captured value).
    const latest = Number(tempoInput.value);
    if (Number.isFinite(latest)) send('setTempo', { tempo: latest });
    tempoSendTimer = null;
  }, 1200);
}

function clearTempoHold() {
  if (tempoHoldTimeout) clearTimeout(tempoHoldTimeout);
  if (tempoHoldInterval) clearInterval(tempoHoldInterval);
  tempoHoldTimeout = null;
  tempoHoldInterval = null;
}

function setupTempoHold(button, direction) {
  const start = (e) => {
    if (e) e.preventDefault();
    clearTempoHold();
    if (tempoSendTimer) {
      clearTimeout(tempoSendTimer);
      tempoSendTimer = null;
    }
    tempoHoldTimeout = setTimeout(() => {
      tempoHoldInterval = setInterval(() => adjustTempoByStep(direction), 85);
    }, 260);
  };

  button.addEventListener('pointerdown', start);
  button.addEventListener('pointerup', clearTempoHold);
  button.addEventListener('pointerleave', clearTempoHold);
  button.addEventListener('pointercancel', clearTempoHold);
}

function adjustTempoByStep(direction) {
  const current = Number(tempoInput.value);
  if (!Number.isFinite(current)) return;

  let next;
  if (direction > 0) {
    next = Number.isInteger(current) ? current + 1 : Math.ceil(current);
  } else {
    next = Number.isInteger(current) ? current - 1 : Math.floor(current);
  }

  next = Math.max(20, Math.min(999, next));
  pendingTempo = { value: next, expiresAt: Date.now() + 2500 };
  tempoInput.value = String(next);
  queueTempoSend();
}

function renderTrackArms(preview) {
  if (!preview?.tracks?.length) {
    trackArmListEl.textContent = 'No tracks found';
    return;
  }

  trackArmListEl.innerHTML = '';

  let topGroupCollapsed = false;
  let inSubgroup = false;
  let subgroupCollapsed = false;

  preview.tracks.forEach((t) => {
    if (!t.isGrouped) {
      topGroupCollapsed = false;
      inSubgroup = false;
      subgroupCollapsed = false;
    }

    if (t.isGroup && !t.isGrouped) {
      topGroupCollapsed = collapsedGroups.has(t.index);
      inSubgroup = false;
      subgroupCollapsed = false;
    }

    // If a top-level group is collapsed, hide everything nested under it
    // including subgroup headers and subgroup tracks.
    if (topGroupCollapsed && t.isGrouped) return;

    if (t.isGroup && t.isGrouped) {
      inSubgroup = true;
      subgroupCollapsed = collapsedGroups.has(t.index);
    }

    // If subgroup is collapsed, hide only non-group children until next subgroup header.
    if (subgroupCollapsed && t.isGrouped && !t.isGroup) return;

    let depth = 0;
    if (t.isGrouped) depth = inSubgroup ? 2 : 1;
    if (t.isGroup) depth = t.isGrouped ? 1 : 0;

    const row = document.createElement('div');
    row.className = 'track-row';

    const labelWrap = document.createElement('div');
    labelWrap.className = `track-label depth-${depth}`;

    const dot = document.createElement('span');
    dot.className = 'color-dot';
    dot.style.background = abletonColorToCss(t.color);

    const label = document.createElement('span');
    label.textContent = `${t.index + 1}. ${t.name}`;
    if (t.isGroup) {
      label.classList.add('group-name');
      const collapsed = collapsedGroups.has(t.index);
      label.textContent = `${collapsed ? '▸' : '▾'} ${label.textContent} [Group]`;

      labelWrap.style.cursor = 'pointer';
      labelWrap.addEventListener('click', async () => {
        if (collapsedGroups.has(t.index)) collapsedGroups.delete(t.index);
        else collapsedGroups.add(t.index);
        await refreshTrackArms();
      });
    }

    labelWrap.appendChild(dot);
    labelWrap.appendChild(label);

    const pending = pendingArm.get(t.index);
    const pendingActive = pending && pending.expiresAt > Date.now();

    const override = armOverride.get(t.index);
    const overrideActive = override && override.expiresAt > Date.now();

    if (!pendingActive && pending) pendingArm.delete(t.index);
    if (!overrideActive && override) armOverride.delete(t.index);

    const effectiveArm = pendingActive ? pending.arm : (overrideActive ? override.arm : t.arm);

    if ((pendingActive || overrideActive) && t.arm === effectiveArm) {
      pendingArm.delete(t.index);
      armOverride.delete(t.index);
    }

    const isArmable = !t.isGroup;

    row.appendChild(labelWrap);

    if (isArmable) {
      const btn = document.createElement('button');
      btn.textContent = pendingActive ? (effectiveArm ? 'Arming…' : 'Disarming…') : (effectiveArm ? 'Armed' : 'Arm');
      if (effectiveArm) btn.classList.add('danger');
      if (pendingActive) btn.classList.add('pressed');

      btn.addEventListener('click', async () => {
        btn.classList.add('pressed');
        setTimeout(() => btn.classList.remove('pressed'), 180);

        const nextArm = !effectiveArm;
        pendingArm.set(t.index, { arm: nextArm, expiresAt: Date.now() + 4000 });
        btn.textContent = nextArm ? 'Arming…' : 'Disarming…';
        btn.classList.toggle('danger', nextArm);
        btn.disabled = true;

        const data = await send('setTrackArm', { trackIndex: t.index, trackName: t.name, arm: nextArm });
        btn.disabled = false;

        if (!data) {
          pendingArm.delete(t.index);
        } else {
          if (data?.state) renderState(data.state);
          armOverride.set(t.index, { arm: nextArm, expiresAt: Date.now() + 4000 });
          verifyTrackArmBurst(t.index, nextArm);
        }

        await refreshTrackArms();
      });

      row.appendChild(btn);
    } else {
      const spacer = document.createElement('span');
      spacer.textContent = '';
      row.appendChild(spacer);
    }
    trackArmListEl.appendChild(row);
  });
}

async function refreshLocators() {
  try {
    const res = await fetch('/api/locators');
    const data = await res.json();
    if (!res.ok || !data?.success) {
      locatorListEl.textContent = 'Locator read failed';
      return;
    }
    renderLocators(data.locators || []);
  } catch {
    locatorListEl.textContent = 'Locator read failed';
  }
}

async function verifyTrackArmBurst(trackIndex, desiredArm) {
  const checks = [140, 300, 550, 900, 1400];

  for (const ms of checks) {
    await new Promise((r) => setTimeout(r, ms));
    try {
      const res = await fetch(`/api/track-arm/${trackIndex}`);
      const data = await res.json();
      if (res.ok && data?.success && typeof data?.track?.arm === 'boolean') {
        if (data.track.arm === desiredArm) {
          pendingArm.delete(trackIndex);
          armOverride.set(trackIndex, { arm: desiredArm, expiresAt: Date.now() + 1500 });
          await refreshTrackArms();
          return;
        }
      }
    } catch {
      // ignore and keep trying in burst window
    }
  }

  // Let normal refresh reconcile if burst didn't confirm.
  await refreshTrackArms();
}

function abletonColorToCss(colorInt) {
  const n = Number(colorInt || 0) >>> 0;
  if (!n) return '#3b4252';
  const hex = `#${(n & 0xffffff).toString(16).padStart(6, '0')}`;
  return hex;
}

function renderLocators(locators) {
  const incoming = Array.isArray(locators) ? locators : [];
  const sorted = [...incoming].sort((a, b) => Number(a.beats || 0) - Number(b.beats || 0));

  // Always include a top "Start" locator.
  const merged = [{ name: 'Start', beats: 0 }, ...sorted.filter((l) => Number(l.beats) !== 0)];

  if (!merged.length) {
    locatorListEl.textContent = 'No project locators detected yet (will keep trying).';
    return;
  }

  locatorListEl.innerHTML = '';
  merged.forEach((loc) => {
    const row = document.createElement('div');
    row.className = 'track-row';

    const label = document.createElement('span');
    const bar = Math.floor(Number(loc.beats || 0) / Math.max(1, beatsPerBar)) + 1;
    label.textContent = `${loc.name} @ Bar ${bar}`;

    const btn = document.createElement('button');
    btn.textContent = 'Go ▶';
    btn.classList.add('primary');
    btn.addEventListener('click', async () => {
      const isStart = Number(loc.beats) === 0;
      const offset = isStart ? 0 : countInBars * beatsPerBar;
      const targetBeats = Math.max(0, Number(loc.beats) - offset);
      btn.classList.add('flash-green', 'pressed');
      setTimeout(() => btn.classList.remove('pressed'), 180);
      setTimeout(() => btn.classList.remove('flash-green'), 500);

      const data = await send('playFromPosition', { beats: targetBeats });
      if (data?.state) renderState(data.state);
      await postCommandRefresh('play');
    });

    row.appendChild(label);
    row.appendChild(btn);
    locatorListEl.appendChild(row);
  });
}
