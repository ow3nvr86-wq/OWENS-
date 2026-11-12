// 60 fps compositor with motion blur: every output frame averages 4 sub-frames across a 180-degree shutter.
// Whip transitions with directional blur, gentle handheld drift, impact shakes, flashes, calm grain, vignette and
// 1-2 word lowercase captions (numbers as digits). window.renderFrame(f) draws frame f (f / 60 s).
const cv = document.getElementById('c'), X = cv.getContext('2d');
const mk = () => { const c = document.createElement('canvas'); c.width = W; c.height = H; return [c, c.getContext('2d')]; };
const [A, AX] = mk(), [B, BX] = mk(), [CMP, CX] = mk(), [ACCV, ACX] = mk();
const WHIP = 0.16, SUB = 4, SHUTTER = 0.5 / FPS;
let WORDS = [], CHUNKS = [];
const SWAPS = [[['Sixty-four'], '64'], [['a', 'hundred', 'and', 'fifty'], '150'], [['ten'], '10']];

function renderShot(c, i, t) {
  const sh = SHOTS[i]; const lt = Math.max(0, t - sh.start);
  c.save(); c.setTransform(1, 0, 0, 1, 0, 0); c.fillStyle = '#000'; c.fillRect(0, 0, W, H);
  const [cx, cy, z, r] = kf(lt, sh.cam, ease5);
  let dx = noise(t * 0.35, 1) * 6, dy = noise(t * 0.3, 2) * 7;                    // gentle handheld drift
  for (const [st, amp] of (sh.shakes || [])) { const k = t - st; if (k > 0 && k < 0.4) { const a = amp * Math.exp(-k * 9); dx += Math.sin(k * 90) * a; dy += Math.cos(k * 77) * a; } }
  c.translate(W / 2, H / 2 - (sh.lift ?? 100)); c.rotate(r + noise(t * 0.25, 3) * 0.003); c.scale(z, z); c.translate(-cx + dx, -cy + dy);
  sh.draw(c, lt, t);
  c.restore();
  if (sh.sat != null) { c.save(); c.globalCompositeOperation = 'saturation'; c.fillStyle = 'hsl(0,0%,50%)'; c.globalAlpha = 1 - sh.sat; c.fillRect(0, 0, W, H); c.restore(); }
}
function blurDraw(dst, src, x, amt) {
  dst.globalAlpha = 1; dst.drawImage(src, x, 0);
  if (amt < 1) return;
  for (let k = 0; k < 8; k++) { dst.globalAlpha = 0.15; dst.drawImage(src, x + (k / 7 - 0.5) * amt, 0); }
  dst.globalAlpha = 1;
}
function shotIndex(t) { for (let i = 0; i < SHOTS.length; i++) if (t < SHOTS[i].end) return i; return SHOTS.length - 1; }
function composite(t) {                       // one sharp moment -> CMP
  const i = shotIndex(t), sh = SHOTS[i], prev = SHOTS[i - 1], next = SHOTS[i + 1];
  CX.setTransform(1, 0, 0, 1, 0, 0);
  if (next && sh.tr === 'whip' && t > sh.end - WHIP) {
    const p = (t - (sh.end - WHIP)) / (2 * WHIP); renderShot(AX, i, t); renderShot(BX, i + 1, next.start);
    const off = ease5(p) * W, amt = Math.sin(p * Math.PI) * 140; blurDraw(CX, A, -off, amt); blurDraw(CX, B, W - off, amt);
  } else if (prev && prev.tr === 'whip' && t < sh.start + WHIP) {
    const p = (t - (sh.start - WHIP)) / (2 * WHIP); renderShot(AX, i - 1, prev.end); renderShot(BX, i, t);
    const off = ease5(p) * W, amt = Math.sin(p * Math.PI) * 140; blurDraw(CX, A, -off, amt); blurDraw(CX, B, W - off, amt);
  } else { renderShot(AX, i, t); CX.globalAlpha = 1; CX.drawImage(A, 0, 0); }
  return sh;
}

// captions
function clean(s) { return s.toLowerCase().replace(/[^a-z0-9%' -]/g, '').replace(/-/g, ' ').replace(/'/g, '’').trim(); }
function buildChunks() {
  // merge spoken numbers into digit tokens
  const toks = []; let i = 0;
  while (i < WORDS.length) {
    let hit = null;
    for (const [seq, rep] of SWAPS) if (seq.every((s, k) => WORDS[i + k] && WORDS[i + k].word.replace(/[.,?!]/g, '') === s)) { hit = [seq.length, rep]; break; }
    if (hit) { const last = WORDS[i + hit[0] - 1]; toks.push({ word: hit[1] + (/[.,?!]$/.test(last.word) ? last.word.slice(-1) : ''), start: WORDS[i].start, end: last.end }); i += hit[0]; }
    else { toks.push(WORDS[i]); i++; }
  }
  const ph = []; let cur = [];
  for (const w of toks) { cur.push(w); if (/[.,?!:;]$/.test(w.word)) { ph.push(cur); cur = []; } }
  if (cur.length) ph.push(cur);
  const out = [];
  for (const p of ph) { let j = 0; while (j < p.length) { const rest = p.length - j; let take = rest === 3 ? 1 : Math.min(2, rest);
    if (take === 2 && clean(p[j].word).length + clean(p[j + 1].word).length > 13) take = 1; out.push(p.slice(j, j + take)); j += take; } }
  CHUNKS = out.map((c, k) => ({ text: c.map(w => clean(w.word)).join(' '), start: c[0].start - 0.04, end: Math.min(c[c.length - 1].end + 0.3, out[k + 1] ? out[k + 1][0].start - 0.04 : 1e9) }));
}
function captions(t) {
  const ch = CHUNKS.find(c => t >= c.start && t < c.end); if (!ch) return;
  const age = t - ch.start, sc = age >= 0.12 ? 1 : 0.72 + 0.28 * eBack(age / 0.12, 2.2);
  X.save(); X.translate(W / 2, 1335); X.scale(sc, sc);
  X.font = '700 104px Poppins'; X.textAlign = 'center'; X.textBaseline = 'middle'; X.lineJoin = 'round'; X.miterLimit = 2;
  X.shadowColor = 'rgba(0,0,0,0.45)'; X.shadowBlur = 18; X.shadowOffsetY = 8;
  X.lineWidth = 22; X.strokeStyle = INK; X.strokeText(ch.text, 0, 0);
  X.shadowColor = 'transparent'; X.fillStyle = '#ffffff'; X.fillText(ch.text, 0, 0); X.restore();
}
// calm grain: one tile, drifting slowly, very light
const GR = (() => { const g = document.createElement('canvas'); g.width = g.height = 256; const gc = g.getContext('2d'); const id = gc.createImageData(256, 256);
  for (let i = 0; i < id.data.length; i += 4) { const v = hash(i * 0.37) * 255; id.data[i] = id.data[i + 1] = id.data[i + 2] = v; id.data[i + 3] = 12; } gc.putImageData(id, 0, 0); return g; })();

function renderFrame(f) {
  const t = f / FPS;
  ACX.setTransform(1, 0, 0, 1, 0, 0);
  let sh;
  for (let k = 0; k < SUB; k++) {                // motion blur: running average of sub-frames
    const tk = Math.max(0, t + (k / (SUB - 1) - 0.5) * SHUTTER);
    sh = composite(tk);
    ACX.globalAlpha = 1 / (k + 1); ACX.drawImage(CMP, 0, 0);
  }
  ACX.globalAlpha = 1;
  sh = SHOTS[shotIndex(t)];
  X.setTransform(1, 0, 0, 1, 0, 0); X.globalAlpha = 1; X.drawImage(ACCV, 0, 0);
  // flashes on hard cuts into a scare
  for (const ft of [38.35]) { const a = t >= ft ? Math.exp(-(t - ft) * 10) : 0; if (a > 0.01) { X.fillStyle = `rgba(255,255,255,${a * 0.6})`; X.fillRect(0, 0, W, H); } }
  const vg = X.createRadialGradient(W / 2, H / 2, H * 0.32, W / 2, H / 2, H * 0.72);
  vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, 'rgba(10,0,20,0.38)'); X.fillStyle = vg; X.fillRect(0, 0, W, H);
  X.save(); X.globalCompositeOperation = 'overlay'; const o = Math.floor(f / 8) * 37 % 256;
  for (let y = -256; y < H; y += 256) for (let x = -256; x < W; x += 256) X.drawImage(GR, x + o, y + (o * 3) % 256); X.restore();
  if (sh.blackAt && t >= sh.blackAt) { X.fillStyle = '#000'; X.fillRect(0, 0, W, H); return true; }
  captions(t);
  return true;
}
window.renderFrame = renderFrame;
fetch('words.json').then(r => r.json()).then(j => { WORDS = j.words; window.FRAMES = j.frames; buildChunks(); window.CHUNKS = CHUNKS; return document.fonts.load('700 104px Poppins'); }).then(() => { window.ready = true; });
