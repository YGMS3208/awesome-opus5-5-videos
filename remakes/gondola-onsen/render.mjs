// 使い方: node render.mjs            → frames を ffmpeg に流して video.mp4 を作成
//         node render.mjs --stills 1,8,20  → 指定秒の静止画を stills/ に保存
import { createRequire } from 'node:module';
const { chromium } = createRequire(import.meta.url)('playwright');
import { spawn } from 'node:child_process';
import { writeFileSync, mkdirSync } from 'node:fs';
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { extname, join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = dirname(fileURLToPath(import.meta.url));
const MIME = { '.html': 'text/html', '.ttf': 'font/ttf', '.wav': 'audio/wav' };
const server = createServer(async (req, res) => {
  try { const p = join(ROOT, decodeURIComponent(req.url.split('?')[0]) || '/'); const f = p.endsWith('/') ? p + 'index.html' : p;
    const body = await readFile(f); res.writeHead(200, { 'Content-Type': MIME[extname(f)] || 'application/octet-stream' }); res.end(body); }
  catch { res.writeHead(404); res.end(); }
}).listen(0);
const port = server.address().port;

const args = process.argv.slice(2);
const stillsArg = args.includes('--stills') ? args[args.indexOf('--stills') + 1] : null;
const browser = await chromium.launch({ args: ['--disable-gpu-vsync'] });
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
page.on('pageerror', e => console.error('PAGE ERROR', e.message));
page.on('console', m => console.log('console:', m.text()));
await page.goto(`http://127.0.0.1:${port}/index.html?render`);
await page.evaluate(() => window.ready);
const tl = await page.evaluate(() => window.TIMELINE);
writeFileSync(join(ROOT, 'timeline.json'), JSON.stringify(tl));
const canvas = await page.$('canvas');

if (stillsArg) {
  mkdirSync(join(ROOT, 'stills'), { recursive: true });
  for (const s of stillsArg.split(',').map(Number)) {
    await page.evaluate(t => window.render(t), s);
    await canvas.screenshot({ path: join(ROOT, 'stills', `t${String(s).padStart(5, '0')}.jpg`), type: 'jpeg', quality: 85 });
  }
} else {
  const out = join(ROOT, 'video_silent.mp4');
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(tl.fps), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-preset', 'medium', '-crf', '19', '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const N = Math.round(tl.dur * tl.fps);
  for (let i = 0; i < N; i++) {
    await page.evaluate(t => window.render(t), i / tl.fps);
    const buf = await canvas.screenshot({ type: 'jpeg', quality: 93 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 150 === 0) console.log(`frame ${i}/${N}`);
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r));
  console.log('wrote', out);
}
await browser.close(); server.close();
