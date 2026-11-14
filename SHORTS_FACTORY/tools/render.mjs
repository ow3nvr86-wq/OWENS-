// Render an episode's frames:  node tools/render.mjs episodes/<name> [frames-spec] [outdir]
//   frames-spec: "all" (default) | "0-899" | "10,200,450";  RESUME=1 skips frames already on disk; WORKERS=n pages
//   MODE=draft (no motion blur, half-res) | final (default);  DEBUG=depth,rig,lipsync,crowd (overlays)
import { createRequire } from 'module'; import fs from 'fs'; import path from 'path'; import { serve } from './serve.mjs';
const { chromium } = createRequire(import.meta.url)('playwright');
const [ep, spec = 'all', outArg] = process.argv.slice(2);
const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const out = outArg || path.join(ep, 'work', 'frames'); fs.mkdirSync(out, { recursive: true });
const { server, port } = await serve(root);
const b = await chromium.launch({ args: ['--disable-gpu'] });
const open = async () => { const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  p.on('console', m => { if (m.type() === 'error') console.log('[page]', m.text()); }); p.on('pageerror', e => console.log('[pageerror]', e.message));
  await p.goto(`http://127.0.0.1:${port}/engine/index.html?ep=${ep}&mode=${process.env.MODE || 'final'}&debug=${process.env.DEBUG || ''}`); await p.waitForFunction('window.ready === true || window.loadError', null, { timeout: 120000 });
  const err = await p.evaluate(() => window.loadError); if (err) { console.log('load error:', err); process.exit(2); } return p; };
const first = await open();
const N = await first.evaluate(() => window.FRAMES);
let frames = [];
if (spec === 'all') frames = [...Array(N).keys()];
else for (const part of spec.split(',')) { if (part.includes('-')) { const [a, c] = part.split('-').map(Number); for (let f = a; f <= c; f++) frames.push(f); } else frames.push(Number(part)); }
frames = frames.filter(f => !(process.env.RESUME && fs.existsSync(path.join(out, `f${String(f).padStart(5, '0')}.jpg`))));
const workers = Math.max(1, Number(process.env.WORKERS || 3));
const pages = [first]; for (let k = 1; k < workers; k++) pages.push(await open());
const t0 = Date.now(); let done = 0;
await Promise.all(pages.map(async (p, k) => {
  for (let j = k; j < frames.length; j += workers) {
    const f = frames[j]; const file = path.join(out, `f${String(f).padStart(5, '0')}.jpg`);
    const data = await p.evaluate(fr => window.exportFrame ? window.exportFrame(fr) : (window.renderFrame(fr), document.getElementById("c").toDataURL("image/jpeg", 0.94)), f);
    fs.writeFileSync(file + '.tmp', Buffer.from(data.split(',')[1], 'base64')); fs.renameSync(file + '.tmp', file);
    if (++done % 100 === 0) console.log(`${done}/${frames.length} frames, ${((Date.now() - t0) / done).toFixed(0)} ms/frame`);
  }
}));
console.log(`done ${done} frames in ${((Date.now() - t0) / 1000).toFixed(0)} s (of ${N})`);
await b.close(); server.close();
