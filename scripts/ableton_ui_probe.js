#!/usr/bin/osascript -l JavaScript
ObjC.import('stdlib');

function lower(s){ return (s || '').toString().toLowerCase(); }

function walk(elem, needle, out, depth) {
  if (!elem || depth > 6) return;
  try {
    var role = elem.role && elem.role();
    var title = elem.title && elem.title();
    var desc = elem.description && elem.description();
    var line = `${role || ''} | ${title || ''} | ${desc || ''}`;
    if (!needle || lower(line).includes(needle)) out.push(line);
  } catch(e) {}
  try {
    var kids = elem.uiElements();
    for (var i = 0; i < kids.length; i++) walk(kids[i], needle, out, depth + 1);
  } catch(e) {}
}

function run(argv) {
  var needle = lower((argv && argv.length) ? argv[0] : '');
  var se = Application('System Events');
  var live = se.processes.byName('Live');
  if (!live.exists()) {
    console.log('Live process not found');
    return;
  }
  var out = [];
  try {
    var win = live.windows[0];
    var kids = win.uiElements();
    for (var i = 0; i < kids.length; i++) walk(kids[i], needle, out, 0);
  } catch(e) {
    console.log('Probe failed: ' + e);
    return;
  }
  out.slice(0, 400).forEach(x => console.log(x));
}
