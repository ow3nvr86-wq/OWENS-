// CHARACTER RIG V2 (feature flag "rigV2"). Same look as rig v1, better motion:
//  - rubber-hose limbs: quadratic curves of constant length that bend more as the hand/foot comes closer,
//    elbows bow back, knees bow forward, limbs taper from root to tip
//  - planted feet: a stance/swing gait driven by distance travelled, so a planted foot never slides; hips dip on
//    contact; footPlant events (used by crowd dust)
//  - head yaw/pitch: features slide across the egg and squash near the edge
//  - eyes jump to a look-at target in ~3 frames and hold, the head follows over ~8 frames, seeded saccades,
//    blinks every 2-6 s and on big head turns
//  - hats/plumes on a spring-damper that overshoots and settles (bounces on steps, swings on head turns)
//  - viseme mouths for lip sync (feature "lipSync")
//  - ragdoll pose for knock-backs (spin + flailing limbs, hat flies off)
// Everything is a pure function of time and seeds: the same frame always renders the same way.

// ---------------- extra costumes, hats and poses (new keys only: rig v1 looks are unchanged) ----------------
Object.assign(COSTUMES, {
  hoodie_green: { body: '#3e8a4e', trim: '#2a5e36', belt: '#3e8a4e', detail: 'hoodie', legs: '#2a3550' },
  jacket_purple: { body: '#6b3fa0', trim: '#2a2235', belt: '#1e1a24', detail: 'zip', legs: '#1f1f26' },
  tracksuit_yellow: { body: '#e8b52a', trim: '#ffffff', belt: '#e8b52a', detail: 'stripes', legs: '#e8b52a' },
  ghillie: { body: '#4f6b2e', trim: '#6f8a3a', belt: '#3a4a22', detail: 'leaves', legs: '#3f5525' },
  tee_red: { body: '#c8382e', trim: '#f2f2f2', belt: '#2a3550', detail: 'none', legs: '#2a3550' },
  tee_blue: { body: '#2f6fc0', trim: '#f2f2f2', belt: '#2b2b33', detail: 'none', legs: '#2b2b33' },
  vest_orange: { body: '#e0742a', trim: '#2b2b33', belt: '#2b2b33', detail: 'zip', legs: '#4a4a52' },
});
Object.assign(HATS, {
  beanie(g, R) { g.beginPath(); g.moveTo(-R * 0.95, -R * 0.38); g.quadraticCurveTo(-R * 0.98, -R * 1.25, 0, -R * 1.25); g.quadraticCurveTo(R * 0.98, -R * 1.25, R * 0.95, -R * 0.38); g.closePath(); fo(g, '#c8382e');
    g.beginPath(); g.rect(-R * 0.98, -R * 0.5, R * 1.96, R * 0.22); fo(g, '#a82c24'); g.beginPath(); g.arc(0, -R * 1.3, R * 0.16, 0, 7); fo(g, '#f2f2f2'); },
  cap(g, R) { g.beginPath(); g.moveTo(-R * 0.94, -R * 0.42); g.quadraticCurveTo(-R * 0.9, -R * 1.18, 0, -R * 1.18); g.quadraticCurveTo(R * 0.9, -R * 1.18, R * 0.94, -R * 0.42); g.closePath(); fo(g, '#1d1b22');
    g.beginPath(); g.moveTo(R * 0.4, -R * 0.45); g.quadraticCurveTo(R * 1.25, -R * 0.5, R * 1.55, -R * 0.32); g.lineTo(R * 0.5, -R * 0.3); g.closePath(); fo(g, '#1d1b22'); },
  bandana(g, R) { g.beginPath(); g.moveTo(-R * 0.95, -R * 0.45); g.quadraticCurveTo(0, -R * 1.35, R * 0.95, -R * 0.45); g.quadraticCurveTo(0, -R * 0.7, -R * 0.95, -R * 0.45); g.closePath(); fo(g, '#2f6fc0');
    g.beginPath(); g.moveTo(-R * 0.9, -R * 0.5); g.lineTo(-R * 1.35, -R * 0.2); g.lineTo(-R * 1.2, -R * 0.62); g.closePath(); fo(g, '#2f6fc0'); },
  hood_leafy(g, R) { g.beginPath(); g.moveTo(-R * 1.05, R * 0.2); g.quadraticCurveTo(-R * 1.15, -R * 1.35, 0, -R * 1.35); g.quadraticCurveTo(R * 1.15, -R * 1.35, R * 1.05, R * 0.2); g.quadraticCurveTo(R * 0.8, -R * 0.75, 0, -R * 0.82); g.quadraticCurveTo(-R * 0.8, -R * 0.75, -R * 1.05, R * 0.2); g.closePath(); fo(g, '#4f6b2e');
    for (let i = 0; i < 9; i++) { const a = -2.6 + i * 0.32; g.beginPath(); g.ellipse(Math.cos(a) * R * 1.12, Math.sin(a) * R * 1.12 - R * 0.15, R * 0.2, R * 0.08, a, 0, 7); fo(g, i % 2 ? '#6f8a3a' : '#3f5525', 4); } },
  headset(g, R) { g.beginPath(); g.arc(0, -R * 0.1, R * 1.02, Math.PI * 1.08, Math.PI * 1.92); g.lineWidth = R * 0.14; g.strokeStyle = C.ink; g.stroke();
    for (const s of [-1, 1]) { g.beginPath(); g.ellipse(s * R * 0.98, -R * 0.05, R * 0.18, R * 0.3, 0, 0, 7); fo(g, '#2f6fc0'); } },
});
// poses: arm angles like rig v1 (+ optional foot targets [x, y] in body space, hip at (0,-118), y up = negative)
const POSES2 = {
  skydive: (t) => ({ armL: -1.95 + Math.sin(t * 6) * 0.08, armR: 1.95 - Math.sin(t * 6) * 0.08, elL: -0.35, elR: 0.35, feet: [[-55, -40 + Math.sin(t * 5) * 6], [55, -40 - Math.sin(t * 5) * 6]] }),
  glide: (t) => ({ armL: -2.75, armR: 2.75, elL: 0.25, elR: -0.25, feet: [[-14 + Math.sin(t * 3) * 6, 0], [16 + Math.sin(t * 3 + 1) * 6, -4]] }),
  build: (t) => ({ armL: -0.3, armR: 1.35 + Math.sin(t * 16) * 0.55, elL: 0.2, elR: -0.7 - Math.sin(t * 16) * 0.3 }),
  dance: (t) => { const p = t * 7.5; return { armL: -1.3 + Math.sin(p) * 1.1, armR: 1.3 + Math.sin(p + Math.PI) * 1.1, elL: 0.9 * Math.sin(p * 2), elR: -0.9 * Math.sin(p * 2),
    feet: [[-26 + Math.sin(p) * 14, -Math.max(0, Math.sin(p)) * 28], [26 + Math.sin(p) * 14, -Math.max(0, -Math.sin(p)) * 28]], bodyRot: Math.sin(p * 0.5) * 0.09, hipDy: -Math.abs(Math.sin(p)) * 10 }; },
  float: (t) => ({ armL: -1.6 + Math.sin(t * 1.9) * 0.7, armR: 1.4 + Math.sin(t * 1.6 + 1) * 0.7, elL: 0.6 * Math.sin(t * 1.3), elR: -0.6 * Math.sin(t * 1.5),
    feet: [[-30 + Math.sin(t * 1.7) * 22, -24 + Math.cos(t * 1.3) * 18], [30 + Math.sin(t * 1.4 + 2) * 22, -18 + Math.cos(t * 1.1 + 1) * 18]] }),
  hold: (t) => ({ armL: 1.05, armR: 1.45, elL: -0.75, elR: -0.25 }),
  aim: (t) => ({ armL: 1.4, armR: 1.58, elL: -0.35, elR: -0.08 }),
  crush: (t) => ({ armL: -0.2, armR: 2.2 + Math.sin(t * 40) * 0.04, elL: 0.1, elR: -1.3 }),
  jump: (t) => ({ armL: -2.6, armR: 2.6, elL: -0.2, elR: 0.2, feet: [[-24, -52], [26, -46]] }),
  fall: (t) => ({ armL: -2.3 + Math.sin(t * 15) * 0.4, armR: 2.3 + Math.cos(t * 14) * 0.4, elL: 0.4, elR: -0.4, feet: [[-40 + Math.sin(t * 11) * 10, -26], [38 + Math.cos(t * 12) * 10, -12]] }),
  sit: (t) => ({ armL: 0.3, armR: -0.3, elL: 0.6, elR: -0.6, feet: [[30, -10], [44, -6]], hipDy: 34 }),
  wave: (t) => ({ armL: -0.15, armR: 2.6 + Math.sin(t * 10) * 0.35, elL: 0.1, elR: 0.3 }),
  facepalm: (t) => ({ armL: -0.15, armR: 2.75, elL: 0.1, elR: -2.3 }),
};

// ---------------- rubber-hose limb ----------------
function hose(g, ax, ay, bx, by, L, side, w0, w1) {
  const dx = bx - ax, dy = by - ay, d = Math.hypot(dx, dy) || 1e-6;
  // control-point offset solved (bisection) so the curve's arc length is exactly L
  const arcLen = c => { let s = 0, px = 0, py = 0; for (let i = 1; i <= 16; i++) { const u = i / 16, x = u * d, y = 2 * (1 - u) * u * c; s += Math.hypot(x - px, y - py); px = x; py = y; } return s; };
  let h = 0; if (d < L) { let lo = 0, hi = L; for (let it = 0; it < 22; it++) { const mid = (lo + hi) / 2; if (arcLen(mid) < L) lo = mid; else hi = mid; } h = lo / 2; }
  const nx = -dy / d * side, ny = dx / d * side, cx = (ax + bx) / 2 + nx * 2 * h, cy = (ay + by) / 2 + ny * 2 * h;
  const N = 14, Lp = [], Rp = [];
  for (let i = 0; i <= N; i++) {
    const u = i / N, a = (1 - u) * (1 - u), b = 2 * (1 - u) * u, c = u * u;
    const x = a * ax + b * cx + c * bx, y = a * ay + b * cy + c * by;
    let tx = 2 * (1 - u) * (cx - ax) + 2 * u * (bx - cx), ty = 2 * (1 - u) * (cy - ay) + 2 * u * (by - cy); const tl = Math.hypot(tx, ty) || 1; tx /= tl; ty /= tl;
    const w = lerp(w0, w1, u) / 2; Lp.push([x - ty * w, y + tx * w]); Rp.push([x + ty * w, y - tx * w]);
  }
  g.beginPath(); g.moveTo(Lp[0][0], Lp[0][1]); for (const p of Lp) g.lineTo(p[0], p[1]); for (let i = Rp.length - 1; i >= 0; i--) g.lineTo(Rp[i][0], Rp[i][1]); g.closePath();
  g.fillStyle = C.ink; g.fill();
  g.beginPath(); g.arc(ax, ay, w0 / 2, 0, 7); g.arc(bx, by, w1 / 2, 0, 7); g.fill();
  return { cx, cy, mx: 0.25 * ax + 0.5 * cx + 0.25 * bx, my: 0.25 * ay + 0.5 * cy + 0.25 * by };
}

// ---------------- gait: stance / swing with planted feet ----------------
const GAIT = { walk: { S: 150, beta: 0.62, lift: 26, bob: 7 }, march: { S: 140, beta: 0.6, lift: 30, bob: 7 }, run: { S: 250, beta: 0.38, lift: 46, bob: 14 } };
const fracp = x => x - Math.floor(x);
function gaitAt(action, d, cyc) {
  const G = GAIT[action] || GAIT.walk, feet = [];
  for (let k = 0; k < 2; k++) {
    const u = fracp(d / G.S + cyc + k * 0.5);
    if (u < G.beta) feet.push({ x: G.beta * G.S / 2 - u * G.S, lift: 0, planted: true, u });
    else { const w = (u - G.beta) / (1 - G.beta); feet.push({ x: -G.beta * G.S / 2 + ease(w) * G.beta * G.S, lift: Math.sin(Math.PI * w) * G.lift, planted: false, u }); }
  }
  const ph2 = fracp(2 * (d / G.S + cyc));
  return { feet, hipDy: G.bob * 0.5 * Math.cos(2 * Math.PI * ph2), G };
}
// distances (body units) at which a foot touches down in (d0, d1]: the footPlant events
function plantEvents(action, d0, d1, cyc) {
  const G = GAIT[action] || GAIT.walk, out = [];
  for (let k = 0; k < 2; k++) { const off = cyc + k * 0.5; for (let n = Math.ceil(d0 / G.S + off); n <= d1 / G.S + off; n++) { const d = (n - off) * G.S; if (d > d0 && d <= d1) out.push({ d, foot: k, x: G.beta * G.S / 2 }); } }
  return out;
}

// ---------------- look-at: eyes jump fast, head follows slow, saccades, blinks ----------------
const VIS_T = 0.045;                                           // eye jump time (~3 frames at 60 fps)
function stepBlend(segs, tau, key) {                           // piecewise-constant values with a quick blend
  let i = 0; while (i + 1 < segs.length && segs[i + 1].t <= tau) i++;
  const cur = segs[i], prev = segs[Math.max(0, i - 1)], u = i === 0 ? 1 : ease((tau - cur.t) / VIS_T);
  return [lerp(prev.v[0], cur.v[0], u), lerp(prev.v[1], cur.v[1], u)];
}
function lookTargets(ch, s) {                                  // [{t, v:[gx, gy]}] from lookAt + keys
  const segs = [{ t: -1e9, v: [0, 0.05] }], tgt = (lk, t) => {
    if (lk == null || lk === 'camera') return [0, 0.05];
    if (lk === 'sky' || lk === 'up') return [0.1, -0.9]; if (lk === 'down') return [0, 0.8];
    if (lk === 'left') return [-0.9, 0]; if (lk === 'right') return [0.9, 0];
    if (Array.isArray(lk)) { const dx = lk[0] * W - ch.x * W, dy = lk[1] * H - (ch.y * H - 300 * (ch.scale || 1)); const l = Math.hypot(dx, dy) || 1; return [dx / l, dy / l * 0.7]; }
    const o = (s.characters || []).find(c => c.id === lk); if (!o) return [0, 0.05];
    const dx = (o.x - ch.x) * W, dy = (o.y * H - 300 * (o.scale || 1)) - (ch.y * H - 300 * (ch.scale || 1)); const l = Math.hypot(dx, dy) || 1; return [dx / l, dy / l * 0.7];
  };
  segs.push({ t: s.start, v: tgt(ch.lookAt, s.start) });
  for (const k of ch.keys || []) if (k.lookAt !== undefined) segs.push({ t: k.t, v: tgt(k.lookAt, k.t) });
  return segs.sort((a, b) => a.t - b.t);
}
function saccades(ch, s) {                                     // small seeded glances every 0.4-2 s
  const segs = [{ t: -1e9, v: [0, 0] }], sd = hash((ch.id || '').length * 13.7 + (s.wi || 0) * 0.91);
  let t = s.start, k = 0;
  while (t < s.end + 0.5 && k < 200) { segs.push({ t, v: k === 0 ? [0, 0] : [(hash(sd * 31 + k) - 0.5) * 0.36, (hash(sd * 17 + k * 3) - 0.5) * 0.18] }); t += 0.4 + hash(sd * 7 + k) * 1.6; k++; }
  return segs;
}
function lookState(ch, s, t, st) {
  if (!ch._look) ch._look = { tg: lookTargets(ch, s), sc: saccades(ch, s) };
  const L = ch._look, flip = ch.flip ? -1 : 1;
  const gaze = tau => { const a = stepBlend(L.tg, tau), b = stepBlend(L.sc, tau); return [clamp((a[0] + b[0]) * flip, -1, 1), clamp(a[1] + b[1], -1, 1)]; };
  const headAt = tau => { let x = 0, y = 0; for (let j = 0; j < 8; j++) { const g2 = gaze(tau - j * 0.021); x += g2[0]; y += g2[1]; } return [x / 8 * 0.7, y / 8 * 0.45]; };
  const gz = gaze(t), hd = headAt(t);
  st.gaze = [gz[0] - hd[0] * 0.6, gz[1] - hd[1] * 0.5];       // eyes = what's left after the head turn
  st.yaw = clamp(hd[0] + (ch.yaw || 0), -1, 1); st.pitch = hd[1] + (ch.pitch || 0);
  st.yawAt = tau => headAt(tau)[0];
  // blink every 2-6 s, and on any big head turn
  const sd = (ch.id || '').length * 7.3 + (ch.x || 0) * 13, per = 2 + hash(sd) * 4, u = (t + hash(sd + 1) * per) % per;
  let b = u < 0.12 ? Math.sin(Math.PI * u / 0.12) : 0;
  const dyaw = Math.abs(headAt(t - 0.03)[0] - headAt(t - 0.2)[0]); if (dyaw > 0.3) b = Math.max(b, 0.85);
  st.blink = Math.max(b, st.blinkKey || 0);
  st.lookDbg = gz;
}

// ---------------- hat spring-damper ----------------
function hatSpring(def, st, t) {
  const p = Object.assign({ freq: 3.2, damping: 0.22, mass: 1 }, def.hatSpring), K = (2 * Math.PI * p.freq) ** 2, Cd = 2 * p.damping * Math.sqrt(K);
  const moving = GAIT[st.action] && st.speedL > 1;
  const drv = tau => {                                           // head position (body units) at time tau
    let x = 0, y = 0;
    if (moving) { const d = st.dist - st.speedL * (t - tau); y = gaitAt(st.action, d, st.cycle || 0).hipDy; }
    else y = Math.sin(tau * 2.4 + (st.seed || 0)) * 3;
    if (st.yawAt) x = st.yawAt(tau) * 60;
    if (st.ragdoll) { x += Math.sin(tau * 9) * 30; y += Math.cos(tau * 7) * 20; }
    return [x, y];
  };
  const dt = 1 / 120, T = st.crowd ? 0.6 : 1.0; let th = 0, w = 0, yo = 0, yv = 0;
  let p0 = drv(t - T - 2 * dt), p1 = drv(t - T - dt);
  for (let tau = t - T; tau <= t + 1e-6; tau += dt) {
    const p2 = drv(tau), ax = (p2[0] - 2 * p1[0] + p0[0]) / (dt * dt), ay = (p2[1] - 2 * p1[1] + p0[1]) / (dt * dt);
    w += (-K * th - Cd * w - ax * 0.0022 / p.mass) * dt; th += w * dt;
    yv += (-K * yo - Cd * yv - ay * 0.08 / p.mass) * dt; yo += yv * dt;
    p0 = p1; p1 = p2;
  }
  return { rot: clamp(th, -0.6, 0.6), dy: clamp(yo, -18, 18) };
}

// ---------------- visemes (lip sync) ----------------
const VISEME = {          // mouth width/height in head radii, roundness, teeth, tongue
  REST: { w: 0.26, h: 0.0, r: 0, tt: 0, tb: 0, tg: 0 }, MBP: { w: 0.24, h: 0.0, r: 0, tt: 0, tb: 0, tg: 0, press: 1 },
  FV: { w: 0.24, h: 0.07, r: 0.2, tt: 1, tb: 0, tg: 0 }, TH: { w: 0.22, h: 0.08, r: 0.3, tt: 0.6, tb: 0, tg: 1 },
  L: { w: 0.22, h: 0.16, r: 0.4, tt: 0.4, tb: 0, tg: 0.8 }, EE: { w: 0.34, h: 0.09, r: 0.1, tt: 1, tb: 0.7, tg: 0 },
  AA: { w: 0.27, h: 0.26, r: 0.5, tt: 0.3, tb: 0, tg: 0.6 }, OH: { w: 0.2, h: 0.21, r: 1, tt: 0, tb: 0, tg: 0.3 },
  OO: { w: 0.12, h: 0.12, r: 1, tt: 0, tb: 0, tg: 0 }, ETC: { w: 0.24, h: 0.08, r: 0.3, tt: 0.5, tb: 0.3, tg: 0.2 },
};
function mouthV2(g, R, mx, my, sq, P, open) {
  const w = P.w * R * sq, h = P.h * R * (0.55 + 0.45 * open);
  g.lineCap = 'round'; g.lineJoin = 'round';
  if (h < R * 0.02) {                                           // closed lips (pressed for M/B/P)
    g.beginPath(); g.moveTo(mx - w / 2, my); g.quadraticCurveTo(mx, my + (P.press ? R * 0.015 : R * 0.03), mx + w / 2, my);
    g.lineWidth = R * (0.07 + 0.03 * (P.press || 0)); g.strokeStyle = C.ink; g.stroke(); return;
  }
  const rr = Math.min(h / 2, w / 2) * (0.35 + 0.65 * P.r);
  g.beginPath(); g.moveTo(mx - w / 2 + rr, my - h / 2); g.arcTo(mx + w / 2, my - h / 2, mx + w / 2, my + h / 2, rr); g.arcTo(mx + w / 2, my + h / 2, mx - w / 2, my + h / 2, rr);
  g.arcTo(mx - w / 2, my + h / 2, mx - w / 2, my - h / 2, rr); g.arcTo(mx - w / 2, my - h / 2, mx + w / 2, my - h / 2, rr); g.closePath();
  g.fillStyle = '#4a1a24'; g.fill(); g.save(); g.clip();
  if (P.tt > 0.05) { g.fillStyle = `rgba(255,255,255,${P.tt})`; g.fillRect(mx - w / 2, my - h / 2, w, Math.max(R * 0.035, h * 0.3)); }
  if (P.tb > 0.05) { g.fillStyle = `rgba(255,255,255,${P.tb})`; g.fillRect(mx - w / 2, my + h / 2 - h * 0.22, w, h * 0.22); }
  if (P.tg > 0.05) { g.beginPath(); g.ellipse(mx, my + h / 2, w * 0.32, h * 0.38, 0, 0, 7); g.fillStyle = `rgba(214,84,98,${P.tg})`; g.fill(); }
  g.restore(); g.lineWidth = R * 0.06; g.strokeStyle = C.ink; g.stroke();
}
function blendVis(a, b, u) { const A = VISEME[a] || VISEME.REST, B = VISEME[b] || VISEME.REST, o = {}; for (const k of ['w', 'h', 'r', 'tt', 'tb', 'tg']) o[k] = lerp(A[k], B[k], u); o.press = lerp(A.press || 0, B.press || 0, u); return o; }

// ---------------- face with a head turn ----------------
function drawFaceV2(g, R, s) {
  const yaw = clamp(s.yaw || 0, -1, 1), pitch = s.pitch || 0, gz = s.gaze || [0, 0];
  const map = (x0, y0) => { const th = Math.asin(clamp(x0 / (R * 0.92), -1, 1)) + yaw * 0.8; const c = Math.cos(th); return [Math.sin(th) * R * 0.92, y0 + pitch * R * 0.28, Math.max(0.15, c)]; };
  const eyY = -R * 0.02, b = s.blink === true ? 1 : (s.blink || 0);
  for (const k of [-1, 1]) {
    const [ex, ey, sq] = map(k * R * 0.32, eyY), ox = gz[0] * R * 0.1 * sq, oy = gz[1] * R * 0.07;
    const ry = R * (s.mood === 'shocked' || s.mood === 'scared' ? 0.12 : 0.1) * (1 - b);
    if (b > 0.8) { g.beginPath(); g.moveTo(ex - R * 0.08 * sq, ey); g.lineTo(ex + R * 0.08 * sq, ey); g.lineWidth = R * 0.07; g.strokeStyle = C.ink; g.lineCap = 'round'; g.stroke(); }
    else { g.beginPath(); g.ellipse(ex + ox, ey + oy + b * R * 0.03, R * 0.075 * sq, Math.max(R * 0.02, ry), 0, 0, 7); g.fillStyle = C.ink; g.fill(); }
  }
  const [bi, bo] = s.brow || BROWS[s.mood] || BROWS.neutral;
  for (const k of [-1, 1]) {
    const [x1, y1] = map(k * R * 0.32 - k * R * 0.16, -R * 0.3 + bi * R), [x2, y2] = map(k * R * 0.32 + k * R * 0.18, -R * 0.3 + bo * R);
    g.beginPath(); g.moveTo(x1, y1); g.lineTo(x2, y2); g.lineWidth = R * 0.13; g.strokeStyle = C.ink; g.lineCap = 'round'; g.stroke();
  }
  const [mx, my, msq] = map(0, R * 0.38);
  if (s.vis) { mouthV2(g, R, mx, my, msq, s.vis, s.visOpen ?? 1); return; }
  g.save(); g.translate(mx, 0); g.scale(msq, 1); g.translate(-mx, 0);
  // reuse rig v1 mouths (mood shapes / amplitude talking) at the turned position
  const s2 = Object.assign({}, s, { look: 0, blink: 1 }); g.save(); g.translate(mx, my - R * 0.38);
  g.beginPath(); g.rect(-R * 0.6, R * 0.15, R * 1.2, R * 0.5); g.clip();
  drawFace(g, R, Object.assign(s2, { brow: [5, 5] }));               // draws only the mouth inside the clip
  g.restore(); g.restore();
}

// ---------------- the V2 character ----------------
function drawCharacterV2(g, def, st) {
  const cos = COSTUMES[def.costume] || COSTUMES.tunic, s = st.scale || 1, t = st.t || 0, dbg = DEBUG.has('rig');
  const pose = (POSES2[st.action] || POSES[st.action] || POSES.idle)(t, st.phase || 0);
  let P = pose;
  if (st.prevAction && st.prevAction !== st.action && t - st.actionT < 0.32) {
    const Q = (POSES2[st.prevAction] || POSES[st.prevAction] || POSES.idle)(t, st.phase || 0), u = eBack(clamp((t - st.actionT) / 0.32), 1.3);
    P = Object.assign({}, pose); for (const k of ['armL', 'armR', 'elL', 'elR']) P[k] = lerp(Q[k], pose[k], u);
  }
  const gaitOn = GAIT[st.action] && !pose.feet;
  const ga = gaitOn ? gaitAt(st.action, st.dist ?? (t * (st.action === 'run' ? 520 : 260)), st.cycle || 0) : null;
  const pop = st.pop != null ? Math.max(0.001, eBack(st.pop, 2.2)) : 1;
  let sy = ga ? 1 - 0.03 * Math.cos(4 * Math.PI * fracp((st.dist || 0) / ga.G.S + (st.cycle || 0))) : 1 + 0.012 * Math.sin(t * 2.2 + (st.seed || 0));
  if (st.actionT != null) sy -= 0.06 * pulse(t, st.actionT, 0.22);
  g.save(); g.translate(st.x, st.y); g.scale((st.flip ? -1 : 1) * s * pop / Math.sqrt(sy), s * pop * sy);
  // soft drop shadow (shrinks when airborne)
  const air = st.air || 0, shw = 95 * (1 - 0.6 * clamp(air / 300));
  const sh = g.createRadialGradient(0, 0, 4, 0, 0, shw); sh.addColorStop(0, `rgba(10,8,12,${0.42 * (1 - 0.7 * clamp(air / 300))})`); sh.addColorStop(1, 'rgba(10,8,12,0)');
  g.save(); g.scale(1, 0.22); g.fillStyle = sh; g.beginPath(); g.arc(0, 0, shw, 0, 7); g.fill(); g.restore();
  g.translate(0, -air);
  // ragdoll / body rotation about the torso centre
  const hipDy = (ga ? ga.hipDy : Math.sin(t * 2.4 + (st.seed || 0)) * 2) + (pose.hipDy || 0);
  const rot = (st.lean || 0) + (pose.bodyRot || 0) + (st.bodyRot || 0) + (st.action === 'run' ? 0.1 : 0);
  if (st.lying) g.translate(0, 132);
  if (rot) { g.translate(0, -180); g.rotate(rot); g.translate(0, 180); }
  const hipY = -118 + hipDy, top = -232 + hipDy;
  // legs: hip -> planted / swinging foot, knees bow forward
  const feet = pose.feet ? pose.feet.map(f => ({ x: f[0], y: f[1], planted: false })) :
    ga ? ga.feet.map((f, k) => ({ x: f.x + (k ? 12 : -12) * 0.3, y: -f.lift, planted: f.planted })) : [{ x: -20, y: 0, planted: true }, { x: 20, y: 0, planted: true }];
  if (st.ragdoll) { feet[0] = { x: -40 + Math.sin(t * 13) * 26, y: -30 + Math.cos(t * 11) * 22 }; feet[1] = { x: 40 + Math.cos(t * 12) * 26, y: -20 + Math.sin(t * 14) * 22 }; }
  feet.forEach((f, k) => {
    const hx = k ? 14 : -14, L = 118, d = Math.hypot(f.x - hx, f.y - hipY);
    const fx = d > L ? hx + (f.x - hx) * L / d : f.x, fy = d > L ? hipY + (f.y - hipY) * L / d : f.y;
    const side = (fx - hx) * 0 + 1; const r = hose(g, hx, hipY, fx, fy, L, -side, 11, 9);
    const toe = f.planted ? 0 : clamp(-(f.y) / 120, -0.4, 0.5);
    g.save(); g.translate(fx, fy); g.rotate(-toe); g.beginPath(); g.ellipse(9, -2, 17, 8, 0, 0, 7); fo(g, '#1f1b1d', 4); g.restore();
    if (dbg) { g.fillStyle = f.planted ? '#2f2' : '#f33'; g.beginPath(); g.arc(fx, fy, 9, 0, 7); g.fill(); g.fillStyle = '#ff0'; g.beginPath(); g.arc(r.cx, r.cy, 5, 0, 7); g.fill(); }
  });
  // torso (same costume drawing as rig v1, plus the new details)
  g.beginPath(); g.moveTo(-40, top); g.quadraticCurveTo(0, top - 10, 40, top); g.lineTo(46, hipY + 6); g.quadraticCurveTo(0, hipY + 16, -46, hipY + 6); g.closePath(); fo(g, cos.body);
  if (cos.detail === 'lamellar') { g.strokeStyle = 'rgba(0,0,0,0.28)'; g.lineWidth = 3; for (let y = top + 22; y < hipY; y += 16) { g.beginPath(); g.moveTo(-40, y); g.lineTo(40, y); g.stroke(); } }
  if (cos.detail === 'plates') { for (let y = top + 30; y < hipY - 4; y += 26) { g.beginPath(); g.rect(-40, y, 80, 12); g.fillStyle = cos.trim; g.fill(); } }
  if (cos.detail === 'buttons' || cos.detail === 'rivets') { for (let y = top + 24; y < hipY - 6; y += 22) { g.beginPath(); g.arc(cos.detail === 'rivets' ? -24 : 0, y, 5, 0, 7); fo(g, cos.trim, 3); } }
  if (cos.detail === 'hoodie') { g.beginPath(); g.rect(-24, hipY - 44, 48, 22); fo(g, cos.trim, 3); for (const x of [-9, 9]) { g.beginPath(); g.moveTo(x, top + 14); g.lineTo(x + (x > 0 ? 2 : -2), top + 46); g.lineWidth = 3; g.strokeStyle = '#f2f2f2'; g.stroke(); } }
  if (cos.detail === 'zip') { g.beginPath(); g.moveTo(0, top + 6); g.lineTo(0, hipY + 8); g.lineWidth = 4; g.strokeStyle = cos.trim; g.stroke(); }
  if (cos.detail === 'stripes') { for (const x of [-34, 30]) { g.beginPath(); g.rect(x, top + 8, 5, hipY - top - 4); g.fillStyle = cos.trim; g.fill(); } }
  if (cos.detail === 'leaves') { for (let i = 0; i < 10; i++) { const x = -34 + hash(i * 3.1) * 68, y = top + 10 + hash(i * 5.7) * (hipY - top - 10); g.beginPath(); g.ellipse(x, y, 12, 5, hash(i) * 3, 0, 7); fo(g, i % 2 ? cos.trim : '#3f5525', 3); } }
  if (cos.detail !== 'none' && cos.detail !== 'hoodie' && cos.detail !== 'leaves') { g.beginPath(); g.rect(-45, hipY - 22, 90, 16); fo(g, cos.belt, 4); }
  g.beginPath(); g.moveTo(-40, top); g.lineTo(0, top + 26); g.lineTo(40, top); g.lineWidth = 6; g.strokeStyle = cos.trim; g.stroke();
  // arms: rubber hose from shoulder to hand (the elbow from the pose sets the bend side)
  const hands = [];
  const arms = st.ragdoll ? [[-38, top + 14, -2.3 + Math.sin(t * 15) * 0.7, 0.5, -1], [38, top + 14, 2.3 + Math.cos(t * 14) * 0.7, -0.5, 1]] : [[-38, top + 14, P.armL, P.elL, -1], [38, top + 14, P.armR, P.elR, 1]];
  for (const [sx, sy0, a, e] of arms) {
    const ex = sx + Math.sin(a) * 52, ey = sy0 + Math.cos(a) * 52, ha = a + e, hx = ex + Math.sin(ha) * 50, hy = ey + Math.cos(ha) * 50;
    const side = Math.sign((hx - sx) * (ey - sy0) - (hy - sy0) * (ex - sx)) || 1;
    const r = hose(g, sx, sy0, hx, hy, 102, side, 10, 8);
    hands.push([hx, hy, ha]);
    if (dbg) { g.fillStyle = '#ff0'; g.beginPath(); g.arc(r.cx, r.cy, 5, 0, 7); g.fill(); g.strokeStyle = '#0ff'; g.lineWidth = 2; g.beginPath(); g.moveTo(sx, sy0); g.lineTo(r.cx, r.cy); g.lineTo(hx, hy); g.stroke(); }
  }
  if (st.prop && window.drawHandProp) drawHandProp(g, st.prop, hands, t, st);
  for (const [hx, hy] of hands) { g.beginPath(); g.arc(hx, hy, 11, 0, 7); fo(g, C.skin, 5); }
  // head
  const R = 82, hcY = top - R * 0.95;
  let tilt = (st.headTilt || 0) + (ga ? 0.04 * Math.sin(4 * Math.PI * fracp((st.dist || 0) / ga.G.S + (st.cycle || 0)) - 1.0) : 0.03 * Math.sin(t * 1.3 + (st.seed || 0) * 1.7));
  if (st.moodT != null) tilt += 0.07 * pulse(t, st.moodT, 0.3);
  g.save(); g.translate(0, hcY); g.rotate(tilt);
  if (def.hair) { g.beginPath(); g.arc(0, -R * 0.15, R * 1.04, Math.PI * 1.05, Math.PI * 1.95); g.closePath(); fo(g, def.hair); }
  g.beginPath(); g.ellipse(0, 0, R * 0.92, R * 1.08, 0, 0, 7); fo(g, C.skin);
  const mood = st.mood || def.mood || 'neutral';
  let brow = BROWS[mood] || BROWS.neutral;
  if (st.prevMood && st.prevMood !== mood && t - st.moodT < 0.3) { const a = BROWS[st.prevMood] || BROWS.neutral, u = eBack(clamp((t - st.moodT) / 0.3), 1.6); brow = [lerp(a[0], brow[0], u), lerp(a[1], brow[1], u)]; }
  drawFaceV2(g, R, { mood, blink: st.blink, talk: st.talk, brow, yaw: st.yaw || 0, pitch: st.pitch || 0, gaze: st.gaze, vis: st.vis, visOpen: st.visOpen });
  // facial hair rides with the turn
  if (def.facial) { const yaw = st.yaw || 0; g.save(); g.translate(Math.sin(yaw * 0.8) * R * 0.92, (st.pitch || 0) * R * 0.28); g.scale(Math.max(0.3, Math.cos(yaw * 0.8)), 1); facialHair(g, R, def.facial); g.restore(); }
  // hat on a spring; knocked-off hats are drawn by the crowd FX
  if (!st.hatOff) {
    const hs = def.hat && def.hat !== 'none' ? hatSpring(def, st, t) : { rot: 0, dy: 0 };
    g.save(); g.translate((st.yaw || 0) * R * 0.08, -R * 0.55 + hs.dy); g.rotate(hs.rot + (st.yaw || 0) * 0.06); g.translate(0, R * 0.55);
    (HATS[def.hat] || HATS.none)(g, R, { t, sway: hs.rot });
    if (dbg && def.hat && def.hat !== 'none') { g.fillStyle = '#f0f'; g.beginPath(); g.arc(0, -R * 0.55, 7, 0, 7); g.fill(); }
    g.restore();
  }
  if (dbg && st.lookDbg) { g.strokeStyle = '#f0f'; g.lineWidth = 4; g.beginPath(); g.moveTo(0, 0); g.lineTo(st.lookDbg[0] * 260, st.lookDbg[1] * 260); g.stroke(); }
  if (DEBUG.has('lipsync') && st.visLabel) { g.save(); g.scale(1 / s, 1 / s); g.font = '700 34px monospace'; g.textAlign = 'center'; g.fillStyle = '#000c'; g.fillRect(-150, R * s * 0.9, 300, 76); g.fillStyle = '#ff0'; g.fillText(st.visLabel, 0, R * s * 0.9 + 32); g.fillStyle = '#fff'; g.fillText(st.visWord || '', 0, R * s * 0.9 + 68); g.restore(); }
  g.restore();
  g.restore();
  return { headY: st.y + (hcY - air) * s };
}
// a knocked-off hat flying on its own arc (called by crowd FX)
function drawLooseHat(g, def, x, y, rot, s) { if (!def.hat || def.hat === 'none') return; g.save(); g.translate(x, y); g.scale(s, s); g.rotate(rot); (HATS[def.hat] || HATS.none)(g, 82, { t: 0, sway: 0 }); g.restore(); }

// ---------------- lip sync: viseme keys (tools/visemes.py) -> mouth shape for the speaking character ----------------
let VISKEYS = null;
function lipAt(ch, s, t, st) {
  if (!VISKEYS || !ch.talkT || t < ch.talkT[0] - 0.05 || t > ch.talkT[1] + 0.3) return;      // only the speaking character
  let lo = 0, hi = VISKEYS.length - 1;
  while (lo < hi) { const m = (lo + hi + 1) >> 1; if (VISKEYS[m].t <= t) lo = m; else hi = m - 1; }
  const cur = VISKEYS[lo].t <= t ? VISKEYS[lo] : { v: 'REST', word: '' }, nxt = VISKEYS[lo + 1];
  const bl = 0.04;                                                   // blend over ~1-2 frames into the next shape
  const u = nxt && nxt.t - t < bl ? 1 - (nxt.t - t) / bl : 0;
  st.vis = blendVis(cur.v, nxt ? nxt.v : 'REST', ease(u));
  st.visOpen = 0.35 + 0.65 * clamp(amp(t) / 0.55);                  // loudness only scales the opening
  st.visLabel = u > 0.5 && nxt ? nxt.v : cur.v; st.visWord = cur.word; st.talk = undefined;
}
