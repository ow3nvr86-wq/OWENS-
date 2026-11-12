// Motion helpers: easing, springs, camera keys, idle life, walks. Everything is a pure function of the frame.
export const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const lerp = (a, b, t) => a + (b - a) * t;
export const smooth = t => { t = clamp(t); return t * t * (3 - 2 * t); };
export const smoother = t => { t = clamp(t); return t * t * t * (t * (t * 6 - 15) + 10); };
export const easeOut = t => { t = clamp(t); return 1 - Math.pow(1 - t, 3); };
export const easeIn = t => { t = clamp(t); return t * t * t; };
export const easeInOut = smoother;
// overshoot then settle (anticipation is done by the caller with a small negative lead-in)
export const back = (t, s = 1.70158) => { t = clamp(t) - 1; return t * t * ((s + 1) * t + s) + 1; };
// damped spring 0 -> 1
export const spring = (t, freq = 3.2, damp = 5.0) => t <= 0 ? 0 : 1 - Math.exp(-damp * t) * Math.cos(freq * Math.PI * 2 * t * 0.5);
export const ramp = (f, a, b) => clamp((f - a) / Math.max(1e-6, b - a));
export const pulse = (f, at, len) => { const t = (f - at) / len; return t < 0 || t > 1 ? 0 : Math.sin(Math.PI * t); };

// cheap deterministic noise
export function hash(n) { const s = Math.sin(n * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); }
export function noise1(x, seed = 0) {
  const i = Math.floor(x), f = x - i, u = f * f * (3 - 2 * f);
  return lerp(hash(i + seed * 57.0), hash(i + 1 + seed * 57.0), u) * 2 - 1;
}

// Catmull-Rom through points [[x,y,z],...], t 0..1 over the whole path
export function catmull(pts, t) {
  const n = pts.length - 1;
  if (n < 1) return pts[0].slice();
  const s = clamp(t) * n, i = Math.min(n - 1, Math.floor(s)), u = s - i;
  const p0 = pts[Math.max(0, i - 1)], p1 = pts[i], p2 = pts[i + 1], p3 = pts[Math.min(n, i + 2)];
  return [0, 1, 2].map(k => 0.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * u + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * u * u +
    (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * u * u * u));
}

const V = (a, b, t) => [lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t)];

// Camera from keys: [{f, pos, look, fov, roll, ease, path:[via points]}]. Between keys the move glides with the
// next key's ease (default smoother). Every hold creeps slightly (creep) so nothing is static. kicks: [{f, amp}]
// give a 7-frame flip-shake.
export function camFromKeys(keys, f, opt = {}) {
  let k0 = keys[0], k1 = keys[0];
  for (let i = 0; i < keys.length; i++) { if (keys[i].f <= f) { k0 = keys[i]; k1 = keys[Math.min(keys.length - 1, i + 1)]; } }
  if (f < keys[0].f) { k0 = k1 = keys[0]; }
  const span = Math.max(1, k1.f - k0.f);
  const e = (k1.ease || smoother)(clamp((f - k0.f) / span));
  let pos = k1.path ? catmull([k0.pos, ...k1.path, k1.pos], e) : V(k0.pos, k1.pos, e);
  let look = k1.lpath ? catmull([k0.look, ...k1.lpath, k1.look], e) : V(k0.look, k1.look, e);
  const fov = lerp(k0.fov ?? 40, k1.fov ?? k0.fov ?? 40, e);
  let roll = lerp(k0.roll ?? 0, k1.roll ?? 0, e);
  // creep: a slow drift so a held frame still breathes
  const c = opt.creep ?? 0.035;
  pos = [pos[0] + noise1(f / 70, 1) * c, pos[1] + noise1(f / 80, 2) * c * 0.6, pos[2] + noise1(f / 75, 3) * c];
  for (const kk of (opt.kicks || [])) {
    const t = f - kk.f;
    if (t >= 0 && t < 7) {
      const a = kk.amp * (1 - t / 7) * (t % 2 ? -1 : 1);
      pos = [pos[0] + a * 0.6, pos[1] + a, pos[2]];
      roll += a * 6;
    }
  }
  return { pos, look, fov, roll };
}

// idle life for a card: tiny sway, breathing squash and a bob; seed keeps characters out of sync
export function idle(f, seed = 0, amt = 1) {
  return {
    tilt: noise1(f / 45, seed) * 0.025 * amt,
    sx: 1 + Math.sin(f / 19 + seed) * 0.008 * amt,
    sy: 1 - Math.sin(f / 19 + seed) * 0.008 * amt,
    bob: Math.abs(Math.sin(f / 23 + seed * 2)) * 0.01 * amt,
  };
}

// blink: true for 3 frames roughly every 2-4 s
export function blinkAt(f, seed = 0) {
  const period = 70 + Math.floor(hash(seed) * 50);
  return ((f + Math.floor(hash(seed + 3) * period)) % period) < 3;
}

// walk/run: distance travelled and step phase (0..1 per stride)
export function walk(f, f0, speed, stride, fps = 30) {
  const t = Math.max(0, f - f0) / fps;
  const d = t * speed;
  return { d, phase: (d / stride) % 1 };
}
