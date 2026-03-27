#!/usr/bin/env node
// Minimal JSON-RPC websocket client for Ableton Bridge MVP

import WebSocket from 'ws';

const url = process.env.ABLETON_BRIDGE_URL || 'ws://127.0.0.1:8765';
const method = process.argv[2] || 'health';
const paramsArg = process.argv[3] || '{}';
let params = {};
try { params = JSON.parse(paramsArg); } catch { console.error('Invalid JSON params'); process.exit(2); }

const id = Date.now();
const ws = new WebSocket(url);

ws.on('open', () => {
  ws.send(JSON.stringify({ jsonrpc: '2.0', id, method, params }));
});

ws.on('message', (buf) => {
  try {
    const msg = JSON.parse(buf.toString());
    if (msg.id === id) {
      console.log(JSON.stringify(msg, null, 2));
      ws.close();
    }
  } catch (e) {
    console.error('Bad response', e.message);
  }
});

ws.on('error', (err) => {
  console.error('Connection error:', err.message);
  process.exit(1);
});
