// Frame compositor: renders shots into offscreen canvases, whip transitions with motion blur, handheld drift,
// grade, vignette, grain and the 1-2 word captions. window.renderFrame(f) draws frame f; window.ready when fonts load.
const cv = document.getElementById('c'), X = cv.getContext('2d');
const A = document.createElement('canvas'), B = document.createElement('canvas');
A.width = B.width = W; A.height = B.height = H;
const AX = A.getContext('2d'), BX = B.getContext('2d');
const WHIP = 0.14;                       // half-length of a whip transition, seconds
let WORDS = [], CHUNKS = [];

function renderShot(c, i, t) {
  const sh = SHOTS[i];
  const lt = Math.max(0, t - sh.start);
  c.save(); c.setTransform(1, 0, 0, 1, 0, 0); c.fillStyle = '#000'; c.fillRect(0, 0, W, H);
  const [cx, cy, z, r] = kf(lt, sh.cam, ease5);
  // handheld drift
  const dx = noise(t * 0.7, 1) * 10, dy = noise(t * 0.6, 2) * 12, dr = noise(t * 0.5, 3) * 0.006;
  // lift: keep the action above the caption band
  c.translate(W / 2, H / 2 - (sh.lift ?? 100)); c.rotate(r + dr); c.scale(z, z); c.translate(-cx + dx, -cy + dy);
  sh.draw(c, lt, t);
  c.restore();
  if (sh.sat != null) { c.save(); c.globalCompositeOperation = 'saturation'; c.fillStyle = `hsl(0,0%,${50}%)`; c.globalAlpha = 1 - sh.sat; c.fillRect(0, 0, W, H); c.restore(); }
}
function blurDraw(src, x, amt) {
  if (amt < 1) { X.drawImage(src, x, 0); return; }
  const n = 9;
  X.globalAlpha = 1; X.drawImage(src, x, 0);
  for (let k = 0; k < n; k++) { X.globalAlpha = 0.16; X.drawImage(src, x + (k / (n - 1) - 0.5) * amt, 0); }
  X.globalAlpha = 1;
}
function shotIndex(t) { for (let i = 0; i < SHOTS.length; i++) if (t < SHOTS[i].end) return i; return SHOTS.length - 1; }

// captions: 1-2 words, lowercase, no punctuation
function buildChunks() {
  const ph = []; let cur = [];
  for (const w of WORDS) { cur.push(w); if (/[.,?!:;]$/.test(w.word) || /\.\.\.$/.test(w.word)) { ph.push(cur); cur = []; } }
  if (cur.length) ph.push(cur);
  const out = [];
  for (const p of ph) {
    let i = 0;
    while (i < p.length) {
      const rest = p.length - i;
      let take = rest === 3 ? 1 : Math.min(2, rest);
      if (take === 2 && (clean(p[i].word).length + clean(p[i + 1].word).length > 13)) take = 1;
      out.push(p.slice(i, i + take)); i += take;
    }
  }
  CHUNKS = out.map((c, k) => ({ text: c.map(w => clean(w.word)).join(' '), start: c[0].start - 0.04, end: Math.min(c[c.length - 1].end + 0.3, out[k + 1] ? out[k + 1][0].start - 0.04 : 1e9) }));
}
function clean(s) { return s.toLowerCase().replace(/[^a-z0-9%' ]/g, '').replace(/'/g, '’'); }
function captions(t) {
  const ch = CHUNKS.find(c => t >= c.start && t < c.end);
  if (!ch) return;
  const age = (t - ch.start) * FPS;
  const sc = age >= 4 ? 1 : 0.7 + 0.3 * eBack(age / 4, 2.2);
  X.save(); X.translate(W / 2, 1335); X.scale(sc, sc);
  X.font = '700 104px Poppins'; X.textAlign = 'center'; X.textBaseline = 'middle';
  X.lineJoin = 'round'; X.miterLimit = 2;
  X.shadowColor = 'rgba(0,0,0,0.45)'; X.shadowBlur = 18; X.shadowOffsetY = 8;
  X.lineWidth = 22; X.strokeStyle = INK; X.strokeText(ch.text, 0, 0);
  X.shadowColor = 'transparent'; X.fillStyle = '#ffffff'; X.fillText(ch.text, 0, 0);
  X.restore();
}
// grain: a few prebuilt noise tiles
const GRAIN = [0, 1, 2].map(k => { const g = document.createElement('canvas'); g.width = g.height = 256; const gc = g.getContext('2d'); const id = gc.createImageData(256, 256);
  for (let i = 0; i < id.data.length; i += 4) { const v = hash(i * 0.37 + k * 911) * 255; id.data[i] = id.data[i + 1] = id.data[i + 2] = v; id.data[i + 3] = 22; } gc.putImageData(id, 0, 0); return g; });

function renderFrame(f) {
  const t = f / FPS;
  const i = shotIndex(t), sh = SHOTS[i];
  X.setTransform(1, 0, 0, 1, 0, 0);
  const prev = SHOTS[i - 1], next = SHOTS[i + 1];
  if (next && sh.tr === 'whip' && t > sh.end - WHIP) {
    const p = (t - (sh.end - WHIP)) / (2 * WHIP);
    renderShot(AX, i, t); renderShot(BX, i + 1, next.start);
    const off = ease5(p) * W, amt = Math.sin(p * Math.PI) * 160;
    blurDraw(A, -off, amt); blurDraw(B, W - off, amt);
  } else if (prev && prev.tr === 'whip' && t < sh.start + WHIP) {
    const p = (t - (sh.start - WHIP)) / (2 * WHIP);
    renderShot(AX, i - 1, prev.end); renderShot(BX, i, t);
    const off = ease5(p) * W, amt = Math.sin(p * Math.PI) * 160;
    blurDraw(A, -off, amt); blurDraw(B, W - off, amt);
  } else {
    renderShot(AX, i, t); X.drawImage(A, 0, 0);
  }
  // flash on hard cuts into impacts
  const flashes = [3.9, 23.13];
  for (const ft of flashes) { const a = decay(t, ft, 9) * (t >= ft ? 1 : 0); if (a > 0.01) { X.fillStyle = `rgba(255,255,255,${a * 0.85})`; X.fillRect(0, 0, W, H); } }
  // vignette
  const vg = X.createRadialGradient(W / 2, H / 2, H * 0.32, W / 2, H / 2, H * 0.72);
  vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, 'rgba(10,0,20,0.42)'); X.fillStyle = vg; X.fillRect(0, 0, W, H);
  // grain
  const g = GRAIN[f % 3]; X.save(); X.globalCompositeOperation = 'overlay'; for (let y = 0; y < H; y += 256) for (let x = 0; x < W; x += 256) X.drawImage(g, x, y); X.restore();
  if (sh.blackAt && t >= sh.blackAt) { X.fillStyle = '#000'; X.fillRect(0, 0, W, H); return true; }
  captions(t);
  return true;
}
window.renderFrame = renderFrame;
fetch('words.json').then(r => r.json()).then(j => { WORDS = j.words; window.FRAMES = j.frames; buildChunks(); window.CHUNKS = CHUNKS; return document.fonts.load('700 104px Poppins'); }).then(() => { window.ready = true; });
