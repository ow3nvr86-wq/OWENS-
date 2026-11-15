// COLOUR LOOK: the house grade, applied to every finished frame (after motion blur, before captions). Same maths as
// tools/look.py: a tone curve, saturation, split toning (shadow / highlight tint) and a vignette. The default look is
// looks/ricks_clips.json (fitted to Rick's Clips frames); script.json "look": "<name>" picks another, "none" turns it off.
let LOOK = null, LOOK_V = null, LOOK_CURVE = null;
async function loadLook(name) {
  if (name === 'none') return;
  try { LOOK = await (await fetch('../looks/' + name + '.json')).json(); } catch (e) { console.log('no look', name); return; }
  const xs = LOOK.curve_x, ys = LOOK.curve_y; LOOK_CURVE = new Float32Array(256);
  for (let i = 0; i < 256; i++) { const x = i / 255; let k = 1; while (k < xs.length - 1 && xs[k] < x) k++; const u = (x - xs[k - 1]) / Math.max(1e-6, xs[k] - xs[k - 1]); LOOK_CURVE[i] = ys[k - 1] + (ys[k] - ys[k - 1]) * Math.min(1, Math.max(0, u)); }
}
function lookVignette(w, h) {
  if (LOOK_V && LOOK_V.w === w && LOOK_V.h === h) return LOOK_V;
  LOOK_V = new Float32Array(w * h); LOOK_V.w = w; LOOK_V.h = h;
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) { const r = Math.hypot((x - w / 2) / (w / 2), (y - h / 2) / (h / 2)), u = Math.min(1, Math.max(0, (r - 0.45) / 0.7)); LOOK_V[y * w + x] = 1 - LOOK.vignette * u * u * (3 - 2 * u); }
  return LOOK_V;
}
function applyLook(g) {
  if (!LOOK) return;
  const cw = g.canvas.width, ch = g.canvas.height; g.save(); g.setTransform(1, 0, 0, 1, 0, 0);
  const im = g.getImageData(0, 0, cw, ch), d = im.data, C = LOOK_CURVE, V = lookVignette(cw, ch), s = LOOK.sat, [sr, sg, sb] = LOOK.shadow_tint, [hr, hg, hb] = LOOK.high_tint;
  for (let i = 0, p = 0; i < d.length; i += 4, p++) {
    let r = C[d[i]], gg = C[d[i + 1]], b = C[d[i + 2]]; const L = 0.2126 * r + 0.7152 * gg + 0.0722 * b;
    r = L + s * (r - L); gg = L + s * (gg - L); b = L + s * (b - L);
    let ws = 1 - L / 0.35; ws = ws > 0 ? ws * ws : 0; let wh = (L - 0.6) / 0.4; wh = wh > 0 ? (wh > 1 ? 1 : wh * wh) : 0;
    const v = V[p] * 255;
    d[i] = (r + ws * sr + wh * hr) * v; d[i + 1] = (gg + ws * sg + wh * hg) * v; d[i + 2] = (b + ws * sb + wh * hb) * v;   // Uint8Clamped clips
  }
  g.putImageData(im, 0, 0); g.restore();
}
