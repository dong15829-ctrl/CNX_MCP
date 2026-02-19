/**
 * Minimal subscription store server.
 * POST /api/subscribe  {endpoint, keys:{p256dh,auth}, expirationTime?}
 * Data is stored in data/subscriptions.json (array).
 */
import http from 'http';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const DATA_PATH = path.join(__dirname, '..', 'data', 'subscriptions.json');
const PORT = process.env.PUSH_PORT || 4000;

const ensureFile = () => {
  if (!fs.existsSync(DATA_PATH)) {
    fs.mkdirSync(path.dirname(DATA_PATH), { recursive: true });
    fs.writeFileSync(DATA_PATH, '[]', 'utf-8');
  }
};

const readSubs = () => {
  ensureFile();
  try {
    return JSON.parse(fs.readFileSync(DATA_PATH, 'utf-8'));
  } catch (e) {
    return [];
  }
};

const writeSubs = (subs) => {
  fs.writeFileSync(DATA_PATH, JSON.stringify(subs, null, 2), 'utf-8');
};

const server = http.createServer((req, res) => {
  // CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  if (req.method === 'POST' && req.url === '/api/subscribe') {
    let body = '';
    req.on('data', (chunk) => (body += chunk));
    req.on('end', () => {
      try {
        const sub = JSON.parse(body);
        if (!sub || !sub.endpoint) throw new Error('Invalid subscription');
        const subs = readSubs();
        const exists = subs.find((s) => s.endpoint === sub.endpoint);
        if (!exists) {
          subs.push(sub);
          writeSubs(subs);
        }
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true }));
      } catch (e) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: false, error: e.message }));
      }
    });
    return;
  }

  res.writeHead(404);
  res.end();
});

server.listen(PORT, () => {
  console.log(`Push subscription server running on http://localhost:${PORT}`);
  console.log(`Subscriptions stored at ${DATA_PATH}`);
});
