// Deterministic offline renderer for the Lemoine pixel-explosion animation.
//
// The page's requestAnimationFrame and performance.now are replaced with a
// virtual clock, so every frame advances exactly 1/FPS seconds no matter how
// slow the (software) GPU is. Frames are screenshotted and piped to ffmpeg.
//
// Env knobs: CAP_W, CAP_H, CAP_FPS, CAP_SECONDS, CAP_OUT, CAP_CRF,
//            CAP_MODE (intro | outro), CHROMIUM_PATH (optional executable).
import { chromium } from 'playwright';
import http from 'http';
import fs from 'fs';
import path from 'path';
import { spawn } from 'child_process';
import { createRequire } from 'module';

const require = createRequire(import.meta.url);
const ffmpegPath = require('ffmpeg-static');

const DIR = path.dirname(new URL(import.meta.url).pathname);

const W = parseInt(process.env.CAP_W || '1280', 10);
const H = parseInt(process.env.CAP_H || '720', 10);
const FPS = parseInt(process.env.CAP_FPS || '30', 10);
const DURATION = parseFloat(process.env.CAP_SECONDS || '8');
const OUT = process.env.CAP_OUT || path.join(DIR, 'out/render.mp4');
const CRF = process.env.CAP_CRF || '18';
const MODE = process.env.CAP_MODE || 'intro';

const mime = { '.html': 'text/html', '.js': 'text/javascript' };
const server = http.createServer((req, res) => {
  const file = path.join(DIR, req.url === '/' ? 'harness.html' : req.url.split('?')[0]);
  try {
    const data = fs.readFileSync(file);
    res.writeHead(200, { 'Content-Type': mime[path.extname(file)] || 'application/octet-stream' });
    res.end(data);
  } catch {
    res.writeHead(404); res.end('not found');
  }
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const port = server.address().port;

const browser = await chromium.launch({
  executablePath: process.env.CHROMIUM_PATH || undefined,
  args: ['--use-gl=angle', '--use-angle=swiftshader', '--no-sandbox'],
});
const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });

await page.addInitScript(() => {
  let vt = 0;
  const queue = [];
  window.requestAnimationFrame = (cb) => { queue.push(cb); return queue.length; };
  window.cancelAnimationFrame = () => {};
  performance.now = () => vt;
  window.__step = (dtMs) => {
    vt += dtMs;
    const cbs = queue.splice(0);
    for (const cb of cbs) cb(vt);
  };
});

page.on('pageerror', (e) => console.error('PAGE ERROR:', e.message));

await page.goto(`http://127.0.0.1:${port}/harness.html`, { waitUntil: 'networkidle' });
await page.waitForSelector('canvas', { timeout: 15000 });

fs.mkdirSync(path.dirname(OUT), { recursive: true });
const ff = spawn(ffmpegPath, [
  '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-',
  '-c:v', 'libx264', '-preset', 'medium', '-crf', CRF,
  '-pix_fmt', 'yuv420p', '-movflags', '+faststart', OUT,
], { stdio: ['pipe', 'inherit', 'inherit'] });

const totalFrames = Math.round(DURATION * FPS);
const dtMs = 1000 / FPS;
const cx = W / 2, cy = H / 2;

// Choreography: a list of press windows [start, end] in seconds during which
// the virtual pointer holds down on the lemon and slowly circles it.
const CHOREO = {
  // quiet logo → one sustained burst → let it decay to a clean logo
  intro: [[1.0, 4.0]],
  // two pulses, second one bigger, long tail for end-card overlay room
  outro: [[0.5, 1.6], [3.0, 6.0]],
};
const windows = CHOREO[MODE] || CHOREO.intro;

let pressed = false;
for (let f = 0; f < totalFrames; f++) {
  const t = f / FPS;
  const win = windows.find(([a, b]) => t >= a && t < b);

  if (win && !pressed) {
    await page.mouse.move(cx, cy);
    await page.mouse.down();
    pressed = true;
  }
  if (win && pressed) {
    const a = (t - win[0]) * 1.6;
    const r = Math.min(Math.min(W, H) * 0.11, (t - win[0]) * 90);
    await page.mouse.move(cx + Math.cos(a) * r, cy + Math.sin(a) * r * 0.6);
  }
  if (!win && pressed) {
    await page.mouse.up();
    pressed = false;
  }

  await page.evaluate((dt) => window.__step(dt), dtMs);
  const png = await page.screenshot({ type: 'png' });
  if (!ff.stdin.write(png)) await new Promise(r => ff.stdin.once('drain', r));
  if (f % (FPS * 2) === 0) console.log(`frame ${f}/${totalFrames}`);
}

ff.stdin.end();
await new Promise((res, rej) => ff.on('close', (c) => (c === 0 ? res() : rej(new Error('ffmpeg exit ' + c)))));
await browser.close();
server.close();
console.log('wrote', OUT);
