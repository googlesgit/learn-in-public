#!/usr/bin/env node
/**
 * Minimal demo: Cache-Control + ETag + 304 Not Modified
 * Run: node examples/2026-05-19-cache-headers-demo.js
 */
const http = require('http');
const crypto = require('crypto');

const PORT = 3456;

// Simulated "data version" — bump to simulate a content change
let payload = { message: 'Hello from origin', version: 1 };

function etagFor(body) {
  return `"${crypto.createHash('sha256').update(body).digest('hex').slice(0, 16)}"`;
}

const server = http.createServer((req, res) => {
  if (req.url !== '/data') {
    res.writeHead(404, { 'Content-Type': 'text/plain' });
    res.end('Not found. Try GET /data\n');
    return;
  }

  const body = JSON.stringify(payload);
  const etag = etagFor(body);
  const clientEtag = req.headers['if-none-match'];

  res.setHeader('Content-Type', 'application/json');
  res.setHeader('Cache-Control', 'public, max-age=60');
  res.setHeader('ETag', etag);

  if (clientEtag === etag) {
    res.writeHead(304);
    res.end();
    console.log('→ 304 Not Modified (client had current ETag)');
    return;
  }

  res.writeHead(200);
  res.end(body);
  console.log('→ 200 OK', body);
});

server.listen(PORT, () => {
  console.log(`Cache demo: http://localhost:${PORT}/data`);
  console.log('Try: curl -i http://localhost:' + PORT + '/data');
  console.log('Then repeat with: -H "If-None-Match: <etag from first response>"');
});
