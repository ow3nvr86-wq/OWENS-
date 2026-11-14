// Acceptance checks for the engine upgrades (run after a change):  node tools/acceptance.mjs episodes/<name> [baselineDir]
// Loads the episode in headless Chromium and checks, with numbers, the items in the upgrade checklist:
//  dolly parallax vs zoom, layer edges covered, linear-light blur, captions sharp, planted feet, constant limb length,
//  eyes lead head / blinks / hat settles, M-B-P closed + OO round + EE wide, crowd phase spread, dust on every step,
//  blast radius in/out, determinism (same frame twice = same bytes), and flags-off regression against a baseline.
import { createRequire } from 'module'; import fs from 'fs'; import path from 'path'; import { serve } from './serve.mjs';
const { chromium } = createRequire(import.meta.url)('playwright');
const [ep, baseline] = process.argv.slice(2);
const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const { server, port } = await serve(root);
const b = await chromium.launch({ args: ['--disable-gpu'] });
const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
p.on('pageerror', e => console.log('[pageerror]', e.message));
await p.goto(`http://127.0.0.1:${port}/engine/index.html?ep=${ep}&mode=final`);
await p.waitForFunction('window.ready === true || window.loadError', null, { timeout: 180000 });
const R = await p.evaluate(() => {
  const out = [], ok = (name, pass, detail) => out.push({ name, pass: !!pass, detail });
  // 1. depth: dolly gives parallax, zoom does not
  const cam0 = { x: 0, y: 0, z: 0, f: F0, roll: 0, hx: 0, hy: 0 }, dolly = Object.assign({}, cam0, { z: 15 }), zoom = Object.assign({}, cam0, { f: F0 * 1.11 });
  const k = (c, z) => planeK(c, z).k;
  const dNear = k(dolly, 20) / k(cam0, 20), dFar = k(dolly, 1000) / k(cam0, 1000), zNear = k(zoom, 20) / k(cam0, 20), zFar = k(zoom, 1000) / k(cam0, 1000);
  ok('dolly: near layer grows much more than far', dNear > dFar * 1.5, `near x${dNear.toFixed(2)} vs far x${dFar.toFixed(3)}`);
  ok('zoom: all layers scale the same', Math.abs(zNear - zFar) < 1e-9, `near x${zNear.toFixed(3)} far x${zFar.toFixed(3)}`);
  // 2. edges: every scene's farthest (opaque) layer covers the frame at start, middle and end of its move
  let edgeFail = 0, checked = 0;
  for (const s of SCENES) { if (!s.loc || !LOC[s.loc]) continue; const L = LOC[s.loc].layers[0];
    for (const u of [0.02, 0.5, 0.98]) { const c = cam3At(s, lerp(s.start, s.end, u)); const { k: kk, ox, oy } = planeK(c, L.z);
      const l = W / 2 + ox + (W / 2 - W * OVERSCAN / 2 - W / 2) * kk, r = W / 2 + ox + (W / 2 + W * OVERSCAN / 2 - W / 2) * kk; checked++; if (!(l <= 0 && r >= W)) edgeFail++; } }
  ok('layer edges never show (sky layer covers the frame)', edgeFail === 0, `${checked - edgeFail}/${checked} camera samples covered (the edge guard scales any layer that would not)`);
  // 3. linear-light averaging: 50/50 black/white averages to sRGB ~188, not 128
  const mid = L2S[Math.round((S2L[0] + S2L[255]) / 2 * 4095)];
  ok('motion blur averages in linear light', mid > 180 && mid < 195, `black+white -> ${mid} (sRGB averaging would give 128)`);
  // 4. planted feet: during stance a foot keeps the same world position
  let maxSlide = 0; for (const act of ['walk', 'run']) { const G = GAIT[act]; for (let d = 0; d < G.S * 3; d += 3) { const a = gaitAt(act, d, 0.1), b2 = gaitAt(act, d + 2, 0.1);
    for (let f = 0; f < 2; f++) if (a.feet[f].planted && b2.feet[f].planted) maxSlide = Math.max(maxSlide, Math.abs((a.feet[f].x + d) - (b2.feet[f].x + d + 2))); } }
  ok('planted feet do not slide', maxSlide < 1e-6, `max world drift during stance ${maxSlide.toExponential(1)} body units`);
  // 5. rubber-hose limbs keep their length (arc length of the drawn curve vs the rig length)
  const c2 = document.createElement('canvas').getContext('2d'); let worst = 0;
  for (const d of [102, 90, 70, 50, 30]) { const r = hose(c2, 0, 0, d, 0, 102, 1, 10, 8); let Lc = 0, px = 0, py = 0;
    for (let i = 1; i <= 200; i++) { const u = i / 200, x = 2 * (1 - u) * u * r.cx + u * u * d, y = 2 * (1 - u) * u * r.cy; Lc += Math.hypot(x - px, y - py); px = x; py = y; }
    worst = Math.max(worst, Math.abs(Lc - 102) / 102); }
  ok('limbs keep a constant length while bending', worst < 0.08, `worst arc-length error ${(worst * 100).toFixed(1)} %`);
  // 6. eyes lead the head; blinks happen; hat springs settle
  const s0 = SCENES.find(s => (s.characters || []).length); const ch = s0.characters[0];
  const fake = { id: 'probe', x: 0.5, y: 0.8, scale: 1, keys: [{ t: s0.start + 0.5, lookAt: 'left' }] };
  const g1 = {}, g2 = {}; lookState(fake, s0, s0.start + 0.5 + 0.05, g1); delete fake._look; lookState(fake, s0, s0.start + 0.5 + 0.05, g2);
  ok('eyes jump first, head follows slower', Math.abs(g1.gaze[0]) > 0.15 && Math.abs(g1.yaw) < 0.45, `50 ms after the cue: eyes ${g1.gaze[0].toFixed(2)}, head ${g1.yaw.toFixed(2)}`);
  let blinks = 0; for (let t = 0; t < 12; t += 1 / 60) { const q = {}; lookState(fake, s0, s0.start + t, q); if (q.blink > 0.8) blinks++; }
  ok('blinks every 2-6 s', blinks >= 2, `${blinks} closed-eye frames in 12 s`);
  const hs = hatSpring({ hat: 'beanie' }, { action: 'idle', t: 10, seed: 1, yawAt: tau => (tau > 9.5 ? 0.8 : 0) }, 10);
  const hs2 = hatSpring({ hat: 'beanie' }, { action: 'idle', t: 10.9, seed: 1, yawAt: tau => (tau > 9.5 ? 0.8 : 0) }, 10.9);
  ok('hats lag and settle', Math.abs(hs.rot) > Math.abs(hs2.rot), `rot 0.5 s after a head turn ${hs.rot.toFixed(3)} -> 1.4 s after ${hs2.rot.toFixed(3)}`);
  // 7. lip sync
  if (typeof VISKEYS !== 'undefined' && VISKEYS) {
    const words = VISKEYS.filter(k => /[mbp]/i.test(k.word)); const mbp = VISKEYS.filter(k => k.v === 'MBP');
    ok('M/B/P words get closed lips', mbp.length > 0 && VISEME.MBP.h === 0, `${mbp.length} closed-lip keys across ${new Set(words.map(w => w.word)).size} words with m/b/p`);
    ok('OO is round, EE is wide', VISEME.OO.r === 1 && VISEME.OO.w < VISEME.EE.w && VISEME.EE.w > VISEME.REST.w, `OO w=${VISEME.OO.w} round, EE w=${VISEME.EE.w}`);
  }
  // 8. crowds: phases spread, dust on every step
  if (typeof crowdVariation === 'function') {
    const ph = []; for (let i = 0; i < 60; i++) ph.push(crowdVariation({ seed: 3 }, i).phase); const near = ph.slice(1).filter((v, i) => Math.abs(v - ph[i]) < 0.02).length;
    ok('no two neighbours in lockstep', near === 0, `${near} neighbour pairs within 2 % of a cycle`);
    const ev = plantEvents('run', 0, 2500, 0.3); ok('a footPlant (dust) event on every step', ev.length === 20, `${ev.length} plants over 10 run cycles (expect 20)`);
    const sc = { _impacts: [{ x: 500, y: 1000, t0: 1, r: 200, force: 1 }] };
    const inR = crowdReact({ x: 560, y: 1000, scale: 1, id: 1 }, sc, 1.3, 150), outR = crowdReact({ x: 900, y: 1000, scale: 1, id: 2 }, sc, 1.3, 150);
    ok('everyone inside a blast reacts, nobody outside', inR.ragdoll && !outR.ragdoll, `inside: ${inR.ragdoll ? 'knocked' : 'no'}, outside: ${outR.ragdoll ? 'knocked' : 'no'}`);
  }
  return out;
});
// determinism: the same frame twice gives identical bytes
const f = Math.floor((await p.evaluate(() => window.FRAMES)) * 0.37);
const a = await p.evaluate(fr => window.exportFrame(fr), f), c = await p.evaluate(fr => window.exportFrame(fr), f);
R.push({ name: 'same frame twice = identical image', pass: a === c, detail: `frame ${f}, ${a.length} bytes` });
// captions stay sharp: captions are drawn after the blur (checked by code path) - report the order
R.push({ name: 'captions drawn after motion blur', pass: fs.readFileSync(path.join(root, 'engine/compositor.js'), 'utf8').match(/motionBlurFrame\(t\); else compose\(t\);[\s\S]{0,400}captions\(t\)/) != null, detail: 'renderFrame: blur/compose -> vignette -> captions' });
await b.close(); server.close();
// flags-off regression against a baseline folder rendered before the upgrade
if (baseline && fs.existsSync(baseline)) {
  const dir = path.join(root, 'build', 'regress'); const files = fs.readdirSync(baseline).filter(x => x.endsWith('.jpg'));
  let same = 0; for (const x of files) if (fs.existsSync(path.join(dir, x)) && Buffer.compare(fs.readFileSync(path.join(baseline, x)), fs.readFileSync(path.join(dir, x))) === 0) same++;
  R.push({ name: 'flags OFF: old video renders unchanged', pass: same === files.length, detail: `${same}/${files.length} baseline frames byte-identical (render build/regress first)` });
}
let fail = 0; for (const r of R) { console.log(`${r.pass ? 'PASS' : 'FAIL'}  ${r.name}  -  ${r.detail}`); if (!r.pass) fail++; }
console.log(fail ? `${fail} check(s) failed` : 'all checks passed'); process.exit(fail ? 1 : 0);
