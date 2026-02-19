/**
 * Send a push notification to all stored subscriptions.
 * Requires .env with VAPID keys:
 *  VAPID_PUBLIC_KEY
 *  VAPID_PRIVATE_KEY
 */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import webpush from 'web-push';
import dotenv from 'dotenv';

dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const DATA_PATH = path.join(__dirname, '..', 'data', 'subscriptions.json');

const VAPID_PUBLIC_KEY = process.env.VAPID_PUBLIC_KEY;
const VAPID_PRIVATE_KEY = process.env.VAPID_PRIVATE_KEY;
if (!VAPID_PUBLIC_KEY || !VAPID_PRIVATE_KEY) {
  console.error('Missing VAPID_PUBLIC_KEY or VAPID_PRIVATE_KEY in .env');
  process.exit(1);
}

webpush.setVapidDetails('mailto:you@example.com', VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY);

const subs = fs.existsSync(DATA_PATH) ? JSON.parse(fs.readFileSync(DATA_PATH, 'utf-8')) : [];
console.log(`Loaded ${subs.length} subscriptions`);

const payload = JSON.stringify({
  title: 'Morning Voca',
  body: '오늘의 단어를 확인하세요!',
  url: '/',
});

const sendAll = async () => {
  for (const sub of subs) {
    try {
      await webpush.sendNotification(sub, payload);
      console.log(`Sent to ${sub.endpoint.slice(0, 40)}...`);
    } catch (e) {
      console.error(`Failed to send to ${sub.endpoint.slice(0, 40)}...`, e.statusCode, e.body || e.message);
    }
  }
};

sendAll().then(() => console.log('Done'));
