// Node for Max: telemetry_post.js
// Receives JSON strings from Max inlet and POSTs to Ableton Bridge HTTP ingest.

const Max = require('max-api');

const ENDPOINT = process.env.ABLETON_BRIDGE_HTTP || 'http://127.0.0.1:8767/duck-telemetry';

async function postPayload(raw) {
  try {
    const text = Array.isArray(raw) ? raw.join(' ') : String(raw);
    const payload = JSON.parse(text);

    const res = await fetch(ENDPOINT, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(payload),
    });

    const body = await res.text();
    Max.post(`telemetry_post: ${res.status} ${body}`);
    Max.outlet(['ok', res.status]);
  } catch (e) {
    Max.post(`telemetry_post error: ${e.message}`);
    Max.outlet(['error', String(e.message)]);
  }
}

Max.addHandler('anything', (...args) => postPayload(args));
Max.addHandler('list', (...args) => postPayload(args));
Max.addHandler('post', (...args) => postPayload(args));
