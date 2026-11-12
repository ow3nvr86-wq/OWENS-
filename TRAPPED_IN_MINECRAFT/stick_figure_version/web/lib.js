// Shared helpers: easing, keyframes, noise and ink-outlined shapes. All drawing is in 1080x1920 frame pixels.
const INK = '#221c22';
const W = 1080, H = 1920, FPS = 60;
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const lerp = (a, b, t) => a + (b - a) * t;
const ease = t => { t = clamp(t); return t * t * (3 - 2 * t); };
const ease5 = t => { t = clamp(t); return t * t * t * (t * (t * 6 - 15) + 10); };
const eOut = t => { t = clamp(t); return 1 - Math.pow(1 - t, 3); };
const eIn = t => { t = clamp(t); return t * t * t; };
const eBack = (t, s = 1.8) => { t = clamp(t) - 1; return t * t * ((s + 1) * t + s) + 1; };
const eElastic = t => { t = clamp(t); return t === 0 || t === 1 ? t : Math.pow(2, -10 * t) * Math.sin((t * 10 - 0.75) * (2 * Math.PI / 3)) + 1; };
const ramp = (t, a, b) => clamp((t - a) / Math.max(1e-6, b - a));
const pulse = (t, at, len) => { const u = (t - at) / len; return u < 0 || u > 1 ? 0 : Math.sin(Math.PI * u); };
const decay = (t, at, k = 6) => t < at ? 0 : Math.exp(-(t - at) * k);
function hash(n) { const s = Math.sin(n * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); }
function noise(x, seed = 0) { const i = Math.floor(x), f = x - i, u = f * f * (3 - 2 * f); return lerp(hash(i + seed * 57), hash(i + 1 + seed * 57), u) * 2 - 1; }
// keyframes: kf(t, [[t0, v0], [t1, v1], ...], easeFn) -> number or array
function kf(t, keys, fn = ease) {
  if (t <= keys[0][0]) return keys[0][1];
  for (let i = 0; i < keys.length - 1; i++) {
    const [a, va] = keys[i], [b, vb] = keys[i + 1];
    if (t <= b) {
      const e = (keys[i + 1][2] || fn)((t - a) / (b - a));
      return Array.isArray(va) ? va.map((v, k) => lerp(v, vb[k], e)) : lerp(va, vb, e);
    }
  }
  return keys[keys.length - 1][1];
}
// ink helpers
function fs(ctx, fill, lw = 8, stroke = INK) {
  if (fill) { ctx.fillStyle = fill; ctx.fill(); }
  if (lw > 0) { ctx.lineWidth = lw; ctx.strokeStyle = stroke; ctx.lineJoin = 'round'; ctx.lineCap = 'round'; ctx.stroke(); }
}
function circ(ctx, x, y, r) { ctx.beginPath(); ctx.arc(x, y, Math.max(0.1, r), 0, Math.PI * 2); }
function ell(ctx, x, y, rx, ry, rot = 0) { ctx.beginPath(); ctx.ellipse(x, y, Math.max(0.1, rx), Math.max(0.1, ry), rot, 0, Math.PI * 2); }
function line(ctx, pts, lw = 10, col = INK) {
  ctx.beginPath(); ctx.moveTo(pts[0][0], pts[0][1]);
  for (const p of pts.slice(1)) ctx.lineTo(p[0], p[1]);
  ctx.lineWidth = lw; ctx.strokeStyle = col; ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.stroke();
}
function poly(ctx, pts) { ctx.beginPath(); ctx.moveTo(pts[0][0], pts[0][1]); for (const p of pts.slice(1)) ctx.lineTo(p[0], p[1]); ctx.closePath(); }
function rrect(ctx, x, y, w, h, r) { ctx.beginPath(); ctx.roundRect(x, y, w, h, r); }
function shadow(ctx, x, y, w, a = 0.22) { ell(ctx, x, y, w, w * 0.18); ctx.fillStyle = `rgba(20,10,30,${a})`; ctx.fill(); }
function withT(ctx, x, y, rot, s, fn) { ctx.save(); ctx.translate(x, y); ctx.rotate(rot || 0); ctx.scale(s || 1, s || 1); fn(); ctx.restore(); }
// soft glow blob
function glow(ctx, x, y, r, col, a = 0.6) {
  const g = ctx.createRadialGradient(x, y, 0, x, y, r);
  g.addColorStop(0, col.replace('A', a)); g.addColorStop(1, col.replace('A', 0));
  ctx.fillStyle = g; ctx.fillRect(x - r, y - r, r * 2, r * 2);
}
// cartoon burst (impact star)
function burst(ctx, x, y, r, t, col = '#ffe14d') {
  if (t <= 0 || t >= 1) return;
  const s = eOut(t) * r, a = 1 - t;
  ctx.save(); ctx.globalAlpha = a;
  ctx.beginPath();
  for (let i = 0; i < 24; i++) {
    const rr = i % 2 ? s * 0.45 : s; const an = i / 24 * Math.PI * 2 + t * 0.6;
    i ? ctx.lineTo(x + Math.cos(an) * rr, y + Math.sin(an) * rr) : ctx.moveTo(x + Math.cos(an) * rr, y + Math.sin(an) * rr);
  }
  ctx.closePath(); fs(ctx, col, 8);
  ctx.restore();
}
// speed lines radiating from a point
function speedLines(ctx, x, y, t, n = 26, r0 = 380, r1 = 1300, a = 0.5) {
  ctx.save(); ctx.globalAlpha = a; ctx.strokeStyle = '#ffffff'; ctx.lineCap = 'round';
  for (let i = 0; i < n; i++) {
    const an = hash(i * 3.1) * Math.PI * 2, off = ((t * 3 + hash(i)) % 1);
    const ra = r0 + off * 300, rb = ra + 160 + hash(i * 7) * 260;
    ctx.lineWidth = 4 + hash(i * 5) * 8;
    ctx.beginPath(); ctx.moveTo(x + Math.cos(an) * ra, y + Math.sin(an) * ra); ctx.lineTo(x + Math.cos(an) * Math.min(rb, r1), y + Math.sin(an) * Math.min(rb, r1)); ctx.stroke();
  }
  ctx.restore();
}
