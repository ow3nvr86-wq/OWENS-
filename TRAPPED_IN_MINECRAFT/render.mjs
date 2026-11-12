// Render frames with headless Chromium (CPU WebGL via SwiftShader).
//   node render.mjs frames "0-1255"        -> frames/f0000.jpg ...   (RESUME=1 skips frames already on disk)
//   node render.mjs stills/a "5,40,300"    -> stills/a/f0005.jpg ...
//   SCALE=0.5 renders at 540x960 (look-dev)
import { createRequire } from 'module'; import fs from 'fs'; import path from 'path';
import { serve } from './tools/serve.mjs';
const { chromium } = createRequire(import.meta.url)('playwright');
const [outDir, spec] = process.argv.slice(2);
const frames = [];
for (const part of spec.split(',')) {
  if (part.includes('-')) { const [a, b] = part.split('-').map(Number); for (let f = a; f <= b; f++) frames.push(f); }
  else frames.push(Number(part));
}
fs.mkdirSync(outDir, { recursive: true });
const root = path.join(path.dirname(new URL(import.meta.url).pathname), 'web');
const { server, port } = await serve(root);
const scale = process.env.SCALE || '1';
const b = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--js-flags=--max-old-space-size=4096'] });
const W = Math.round(1080 * scale), H = Math.round(1920 * scale);
const p = await b.newPage({ viewport: { width: W, height: H } });
p.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') console.log('[page]', m.text()); });
p.on('pageerror', e => { console.log('[pageerror]', e.message); process.exitCode = 2; });
await p.goto(`http://127.0.0.1:${port}/index.html?scale=${scale}`);
await p.waitForFunction('window.ready === true', null, { timeout: 300000 });
const t0 = Date.now(); let n = 0;
for (const f of frames) {
  const file = path.join(outDir, `f${String(f).padStart(4, '0')}.jpg`);
  if (process.env.RESUME && fs.existsSync(file) && fs.statSync(file).size > 10000) continue;
  const t = Date.now();
  const data = await p.evaluate(fr => { window.renderFrame(fr); return document.querySelector('canvas').toDataURL('image/jpeg', 0.95); }, f);
  fs.writeFileSync(file + '.tmp', Buffer.from(data.split(',')[1], 'base64')); fs.renameSync(file + '.tmp', file);
  n++;
  console.log(`frame ${f} ${((Date.now() - t) / 1000).toFixed(1)} s`);
}
console.log(`done ${n} frames in ${((Date.now() - t0) / 1000).toFixed(0)} s`);
await b.close(); server.close();
