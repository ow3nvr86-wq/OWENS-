// CHARACTER STYLE "rc" (script.json  "charStyle": "rc"): the illustrated 2D look used by popular history Shorts
// - proportions: round head ~28 % of the height, a tall bean torso ~32 %, long thin stick legs ~40 %
// - a white head with a soft grey shadow on one side, a dark hand-drawn outline
// - deadpan faces: dot eyes with heavy half-lids, wide ringed eyes when shocked, thick angled brows, small dark mouths
// - fully illustrated costumes: fabric shading (light left, shade right), texture, stitching, pockets, buttons, trims
// All the motion systems of rig V2 are reused (planted feet, rubber-hose limbs, look-at, hat springs, visemes).
const RC = { R: 74, ink: '#1d1719', torsoW: 116, torsoH: 196, leg: 228, arm: 152 };

// ---- seeded fabric texture (a small noise tile multiplied over costumes) ----
let _RCTEX = null;
function rcTexture() {
  if (_RCTEX) return _RCTEX;
  const c = document.createElement('canvas'); c.width = c.height = 96; const g = c.getContext('2d'); const id = g.createImageData(96, 96);
  for (let i = 0; i < 96 * 96; i++) { const v = 200 + Math.floor(hash(i * 1.37) * 55); id.data[i * 4] = id.data[i * 4 + 1] = id.data[i * 4 + 2] = v; id.data[i * 4 + 3] = 255; }
  g.putImageData(id, 0, 0); _RCTEX = g.createPattern(c, 'repeat'); return _RCTEX;
}
const shade = (hex, k) => { const n = parseInt(hex.slice(1), 16); let r = n >> 16, gg = (n >> 8) & 255, b = n & 255;
  const f = v => Math.max(0, Math.min(255, Math.round(k > 0 ? v + (255 - v) * k : v * (1 + k)))); return `rgb(${f(r)},${f(gg)},${f(b)})`; };

// ---- costumes (rc) ----
const RC_COSTUMES = {
  hoodie_green: { body: '#3f9a52', detail: 'hoodie', pants: '#2c3a5c' },
  jacket_purple: { body: '#6c3fa6', detail: 'jacket', pants: '#232028' },
  tracksuit_yellow: { body: '#f0b928', detail: 'track', pants: '#f0b928' },
  ghillie: { body: '#55703a', detail: 'ghillie', pants: '#3f5525' },
  tee_red: { body: '#cf3b33', detail: 'tee', pants: '#2c3a5c' },
  tee_blue: { body: '#2f72c4', detail: 'tee', pants: '#2b2b33' },
  vest_orange: { body: '#e47a2c', detail: 'vest', pants: '#4a4a52' },
};
function rcTorso(g, cos, w, h, t) {
  const x = -w / 2, y = -h, r = w * 0.48;
  const path = () => { g.beginPath(); g.moveTo(x + r, y); g.lineTo(x + w - r, y); g.quadraticCurveTo(x + w, y, x + w, y + r);
    g.lineTo(x + w, y + h - r * 0.6); g.quadraticCurveTo(x + w, y + h, x + w - r * 0.6, y + h); g.lineTo(x + r * 0.6, y + h); g.quadraticCurveTo(x, y + h, x, y + h - r * 0.6);
    g.lineTo(x, y + r); g.quadraticCurveTo(x, y, x + r, y); g.closePath(); };
  path(); const gr = g.createLinearGradient(x, 0, x + w, 0); gr.addColorStop(0, shade(cos.body, 0.18)); gr.addColorStop(0.45, cos.body); gr.addColorStop(1, shade(cos.body, -0.32));
  g.fillStyle = gr; g.fill();
  g.save(); path(); g.clip();
  g.globalCompositeOperation = 'multiply'; g.fillStyle = rcTexture(); g.fillRect(x, y, w, h); g.globalCompositeOperation = 'source-over';
  const ink = RC.ink, dark = shade(cos.body, -0.42), light = shade(cos.body, 0.35);
  const stitch = (pts) => { g.save(); g.setLineDash([7, 6]); g.lineWidth = 2.5; g.strokeStyle = light; g.beginPath(); pts.forEach(([a, b], i) => i ? g.lineTo(a, b) : g.moveTo(a, b)); g.stroke(); g.restore(); };
  if (cos.detail === 'hoodie') {
    g.beginPath(); g.ellipse(0, y + 8, w * 0.52, 30, 0, 0, Math.PI); g.fillStyle = dark; g.fill();                      // hood rim
    for (const s of [-1, 1]) { g.beginPath(); g.moveTo(s * 13, y + 26); g.quadraticCurveTo(s * 16, y + 70, s * 11, y + 92); g.lineWidth = 4; g.strokeStyle = '#f4f1ea'; g.stroke();
      g.beginPath(); g.roundRect(s * 11 - 4, y + 90, 8, 13, 3); g.fillStyle = '#c9c4b8'; g.fill(); }
    g.beginPath(); g.roundRect(-w * 0.36, y + h * 0.56, w * 0.72, h * 0.27, 14); g.fillStyle = shade(cos.body, -0.15); g.fill(); g.lineWidth = 3; g.strokeStyle = dark; g.stroke();
    stitch([[-w * 0.32, y + h * 0.6], [w * 0.32, y + h * 0.6]]);
    g.fillStyle = dark; g.fillRect(x, y + h - 22, w, 22);                                                                   // ribbed hem
    for (let k = 0; k < 12; k++) { g.fillStyle = 'rgba(0,0,0,0.18)'; g.fillRect(x + k * w / 12, y + h - 22, 2, 22); }
  } else if (cos.detail === 'jacket') {
    g.beginPath(); g.moveTo(0, y); g.lineTo(0, y + h); g.lineWidth = 4; g.strokeStyle = '#c9c9d4'; g.stroke();             // zip
    for (let k = 0; k < 18; k++) { g.fillStyle = '#9a9aa8'; g.fillRect(-3, y + 10 + k * 10, 6, 3); }
    g.beginPath(); g.moveTo(-w * 0.45, y + 6); g.lineTo(-4, y + 44); g.lineTo(-4, y + 6); g.closePath(); g.fillStyle = dark; g.fill();
    g.beginPath(); g.moveTo(w * 0.45, y + 6); g.lineTo(4, y + 44); g.lineTo(4, y + 6); g.closePath(); g.fill();
    for (const s of [-1, 1]) { g.beginPath(); g.moveTo(s * w * 0.18, y + h * 0.62); g.lineTo(s * w * 0.38, y + h * 0.56); g.lineWidth = 3; g.strokeStyle = dark; g.stroke(); }
    stitch([[x + 8, y + h * 0.3], [x + 8, y + h - 10]]); stitch([[x + w - 8, y + h * 0.3], [x + w - 8, y + h - 10]]);
  } else if (cos.detail === 'track') {
    for (const s of [-1, 1]) { g.fillStyle = '#ffffff'; g.fillRect(s > 0 ? x + w - 18 : x + 8, y + 12, 9, h - 20); g.fillStyle = '#1d1d24'; g.fillRect(s > 0 ? x + w - 9 : x + 17, y + 12, 3, h - 20); }
    g.beginPath(); g.moveTo(0, y); g.lineTo(0, y + h); g.lineWidth = 3; g.strokeStyle = '#d6a21e'; g.stroke();
    g.beginPath(); g.ellipse(0, y + 6, w * 0.4, 18, 0, 0, Math.PI); g.fillStyle = '#ffffff'; g.fill();
  } else if (cos.detail === 'ghillie') {
    for (let k = 0; k < 46; k++) { const lx = x + hash(k * 3.1) * w, ly = y + hash(k * 5.7) * h, a = hash(k * 2.3) * 3;
      g.save(); g.translate(lx, ly + Math.sin(t * 2 + k) * 1.5); g.rotate(a); g.beginPath(); g.ellipse(0, 0, 15, 6, 0, 0, 7);
      g.fillStyle = ['#3f5a26', '#6f8a3a', '#8a9a4a', '#4b6a2c'][k % 4]; g.fill(); g.lineWidth = 1.5; g.strokeStyle = 'rgba(0,0,0,0.35)'; g.stroke(); g.restore(); }
    g.fillStyle = '#5a4430'; g.fillRect(x, y + h * 0.62, w, 14); g.beginPath(); g.roundRect(-14, y + h * 0.62 - 3, 28, 20, 4); g.fillStyle = '#c9a85a'; g.fill();
  } else if (cos.detail === 'tee') {
    g.beginPath(); g.ellipse(0, y + 4, w * 0.3, 16, 0, 0, Math.PI); g.fillStyle = dark; g.fill();
    g.beginPath(); g.arc(0, y + h * 0.42, 22, 0, 7); g.fillStyle = light; g.fill(); g.beginPath(); g.moveTo(-10, y + h * 0.42); g.lineTo(0, y + h * 0.42 - 12); g.lineTo(10, y + h * 0.42); g.lineTo(0, y + h * 0.42 + 12); g.closePath(); g.fillStyle = dark; g.fill();
    stitch([[x + 6, y + h - 14], [x + w - 6, y + h - 14]]);
  } else if (cos.detail === 'vest') {
    g.fillStyle = '#2b2b33'; g.fillRect(-w * 0.16, y, w * 0.32, h);
    for (let k = 0; k < 4; k++) { g.beginPath(); g.roundRect(-w * 0.44 + (k % 2) * w * 0.6, y + h * (0.3 + Math.floor(k / 2) * 0.28), w * 0.28, h * 0.18, 6); g.fillStyle = dark; g.fill(); }
    for (const yy of [0.3, 0.5, 0.7]) { g.fillStyle = '#e8e8e8'; g.fillRect(x, y + h * yy, w, 5); }
  }
  // soft form shading: darker right side and bottom
  const sg = g.createLinearGradient(x, 0, x + w, 0); sg.addColorStop(0.55, 'rgba(0,0,0,0)'); sg.addColorStop(1, 'rgba(0,0,0,0.22)'); g.fillStyle = sg; g.fillRect(x, y, w, h);
  g.restore();
  path(); g.lineWidth = 6.5; g.strokeStyle = RC.ink; g.lineJoin = 'round'; g.stroke();
}

// ---- face (rc) ----
const RC_LIDS = { smug: 0.5, determined: 0.38, angry: 0.42, sad: 0.32, neutral: 0.12, happy: 0, worried: 0.05, shocked: 0, scared: 0 };
function rcFace(g, R, s) {
  const yaw = clamp(s.yaw || 0, -1, 1), pitch = s.pitch || 0, gz = s.gaze || [0, 0], mood = s.mood || 'neutral';
  const map = (x0, y0) => { const th = Math.asin(clamp(x0 / R, -1, 1)) + yaw * 0.8; return [Math.sin(th) * R, y0 + pitch * R * 0.28, Math.max(0.2, Math.cos(th))]; };
  const b = s.blink === true ? 1 : (s.blink || 0), wide = mood === 'shocked' || mood === 'scared' || mood === 'worried';
  const lid = Math.max(RC_LIDS[mood] ?? 0.12, b);
  for (const k of [-1, 1]) {
    const [ex, ey, sq] = map(k * R * 0.3, -R * 0.02), ox = gz[0] * R * 0.08 * sq, oy = gz[1] * R * 0.06;
    if (wide) {                                                         // ringed eye with a pupil
      const er = R * 0.2 * (mood === 'worried' ? 0.82 : 1);
      g.beginPath(); g.ellipse(ex, ey, er * sq, er * (1 - b * 0.9), 0, 0, 7); g.fillStyle = '#ffffff'; g.fill(); g.lineWidth = R * 0.055; g.strokeStyle = RC.ink; g.stroke();
      if (b < 0.7) { g.beginPath(); g.arc(ex + ox, ey + oy, R * 0.07, 0, 7); g.fillStyle = RC.ink; g.fill(); }
    } else {
      const rx = R * 0.075 * sq, ry = R * 0.095;
      g.save(); g.beginPath(); g.rect(ex - R * 0.2, ey - ry + lid * 2 * ry, R * 0.4, R * 0.4); g.clip();
      g.beginPath(); g.ellipse(ex + ox, ey + oy, rx, ry, 0, 0, 7); g.fillStyle = RC.ink; g.fill(); g.restore();
      if (lid > 0.08) { const ly = ey - ry + lid * 2 * ry; g.beginPath(); g.moveTo(ex - R * 0.13 * sq, ly + (k > 0 ? 1 : -1) * 0); g.lineTo(ex + R * 0.13 * sq, ly); g.lineWidth = R * 0.05; g.strokeStyle = RC.ink; g.lineCap = 'round'; g.stroke(); }
    }
  }
  const [bi, bo] = s.brow || BROWS[mood] || BROWS.neutral, by = wide ? -R * 0.36 : -R * 0.27;
  for (const k of [-1, 1]) {
    const [x1, y1] = map(k * R * 0.3 - k * R * 0.14, by + bi * R * 1.1), [x2, y2] = map(k * R * 0.3 + k * R * 0.16, by + bo * R * 1.1);
    g.beginPath(); g.moveTo(x1, y1); g.lineTo(x2, y2); g.lineWidth = R * 0.085; g.strokeStyle = RC.ink; g.lineCap = 'round'; g.stroke();
  }
  const [mx, my, msq] = map(R * 0.04, R * 0.36);
  if (s.vis) { mouthV2(g, R * 0.85, mx, my, msq, s.vis, s.visOpen ?? 1); return; }
  g.lineCap = 'round'; g.strokeStyle = RC.ink; g.lineWidth = R * 0.05;
  const shape = s.talk != null && s.talk > 0.1 ? 'talk' : ({ happy: 'smile', smug: 'smirk', angry: 'flat', determined: 'flat', worried: 'wavy', shocked: 'o', scared: 'o', sad: 'frown' }[mood] || 'small');
  if (shape === 'talk' || shape === 'o') { const o = shape === 'o' ? 0.75 : clamp((s.talk - 0.08) / 0.6); g.beginPath(); g.ellipse(mx, my, R * 0.09 * msq, R * (0.05 + 0.09 * o), 0, 0, 7); g.fillStyle = '#3a1418'; g.fill(); }
  else if (shape === 'smile') { g.beginPath(); g.moveTo(mx - R * 0.15, my - R * 0.03); g.quadraticCurveTo(mx, my + R * 0.13, mx + R * 0.15, my - R * 0.03); g.closePath(); g.fillStyle = '#3a1418'; g.fill(); }
  else if (shape === 'smirk') { g.beginPath(); g.moveTo(mx - R * 0.1, my + R * 0.02); g.quadraticCurveTo(mx + R * 0.05, my + R * 0.05, mx + R * 0.13, my - R * 0.04); g.stroke(); }
  else if (shape === 'frown') { g.beginPath(); g.moveTo(mx - R * 0.11, my + R * 0.04); g.quadraticCurveTo(mx, my - R * 0.05, mx + R * 0.11, my + R * 0.04); g.stroke(); }
  else if (shape === 'wavy') { g.beginPath(); g.moveTo(mx - R * 0.12, my); for (let i = 1; i <= 4; i++) g.lineTo(mx - R * 0.12 + i * R * 0.06, my + (i % 2 ? -1 : 1) * R * 0.025); g.stroke(); }
  else if (shape === 'flat') { g.beginPath(); g.moveTo(mx - R * 0.1, my); g.lineTo(mx + R * 0.1, my); g.stroke(); }
  else { g.beginPath(); g.ellipse(mx, my, R * 0.05, R * 0.035, 0, 0, 7); g.fillStyle = '#3a1418'; g.fill(); }
}
function rcHead(g, R, def, st, face) {
  // shaded white head + hand-drawn outline
  const gr = g.createRadialGradient(-R * 0.38, -R * 0.42, R * 0.2, -R * 0.1, -R * 0.1, R * 1.2); gr.addColorStop(0, '#ffffff'); gr.addColorStop(0.62, '#fbfbfd'); gr.addColorStop(1, '#c9c9d6');
  g.beginPath(); g.ellipse(0, 0, R * 1.03, R, 0, 0, 7); g.fillStyle = gr; g.fill();
  g.lineWidth = 6.5; g.strokeStyle = RC.ink; g.stroke();
  if (def.hair) { g.save(); g.beginPath(); g.ellipse(0, 0, R * 1.03, R, 0, 0, 7); g.clip(); g.beginPath(); g.ellipse(-R * 0.15, -R * 0.95, R * 1.1, R * 0.5, -0.1, 0, 7); g.fillStyle = def.hair; g.fill();
    for (let k = 0; k < 7; k++) { g.beginPath(); g.moveTo(-R * 0.8 + k * R * 0.25, -R * 0.62); g.quadraticCurveTo(-R * 0.7 + k * R * 0.25, -R * 0.85, -R * 0.55 + k * R * 0.25, -R * 0.95); g.lineWidth = 3; g.strokeStyle = shade(def.hair, 0.25); g.stroke(); }
    g.restore(); g.beginPath(); g.ellipse(0, 0, R * 1.03, R, 0, 0, 7); g.lineWidth = 6.5; g.strokeStyle = RC.ink; g.stroke(); }
  rcFace(g, R, face);
  if (def.facial) { const yaw = st.yaw || 0; g.save(); g.translate(Math.sin(yaw * 0.8) * R, R * 0.06 + (st.pitch || 0) * R * 0.28); g.scale(Math.max(0.3, Math.cos(yaw * 0.8)) * 0.85, 0.85); facialHair(g, R, def.facial); g.restore(); }
}

// ---- the rc character ----
function drawCharacterRC(g, def, st) {
  const cos = RC_COSTUMES[def.costume] || { body: (COSTUMES[def.costume] || COSTUMES.tunic).body, detail: 'tee', pants: '#2b2b33' };
  const s = st.scale || 1, t = st.t || 0, dbg = DEBUG.has('rig'), R = RC.R, LK = RC.leg / 118;
  const pose = (POSES2[st.action] || POSES[st.action] || POSES.idle)(t, st.phase || 0);
  let P = pose;
  if (st.prevAction && st.prevAction !== st.action && t - st.actionT < 0.32) {
    const Q = (POSES2[st.prevAction] || POSES[st.prevAction] || POSES.idle)(t, st.phase || 0), u = eBack(clamp((t - st.actionT) / 0.32), 1.3);
    P = Object.assign({}, pose); for (const k of ['armL', 'armR', 'elL', 'elR']) P[k] = lerp(Q[k], pose[k], u);
  }
  const gaitOn = GAIT[st.action] && !pose.feet;
  const ga = gaitOn ? gaitAt(st.action, (st.dist ?? (t * (st.action === 'run' ? 520 : 260))) / LK, st.cycle || 0) : null;
  const pop = st.pop != null ? Math.max(0.001, eBack(st.pop, 2.2)) : 1;
  let sy = ga ? 1 - 0.022 * Math.cos(4 * Math.PI * fracp(((st.dist || 0) / LK) / ga.G.S + (st.cycle || 0))) : 1 + 0.01 * Math.sin(t * 2.2 + (st.seed || 0));
  if (st.actionT != null) sy -= 0.05 * pulse(t, st.actionT, 0.22);
  g.save(); g.translate(st.x, st.y); g.scale((st.flip ? -1 : 1) * s * pop / Math.sqrt(sy), s * pop * sy);
  const air = st.air || 0, shw = 80 * (1 - 0.6 * clamp(air / 300));
  const sh = g.createRadialGradient(0, 0, 4, 0, 0, shw); sh.addColorStop(0, `rgba(10,8,12,${0.45 * (1 - 0.7 * clamp(air / 300))})`); sh.addColorStop(1, 'rgba(10,8,12,0)');
  g.save(); g.scale(1, 0.2); g.fillStyle = sh; g.beginPath(); g.arc(0, 0, shw, 0, 7); g.fill(); g.restore();
  g.translate(0, -air);
  const hipDy = (ga ? ga.hipDy * LK * 0.8 : Math.sin(t * 2.4 + (st.seed || 0)) * 2) + (pose.hipDy || 0) * LK;
  const rot = (st.lean || 0) + (pose.bodyRot || 0) + (st.bodyRot || 0) + (st.action === 'run' ? 0.08 : 0);
  if (st.lying) g.translate(0, 230);
  if (rot) { g.translate(0, -330); g.rotate(rot); g.translate(0, 330); }
  const hipY = -RC.leg + hipDy, top = hipY - RC.torsoH + 14;
  // legs: long thin sticks with small dark feet (planted gait scaled to the long legs)
  const feet = pose.feet ? pose.feet.map(f => ({ x: f[0] * LK * 0.8, y: f[1] * LK, planted: false })) :
    ga ? ga.feet.map((f, k) => ({ x: f.x * LK + (k ? 4 : -4), y: -f.lift * LK, planted: f.planted })) : [{ x: -18, y: 0, planted: true }, { x: 18, y: 0, planted: true }];
  if (st.ragdoll) { feet[0] = { x: -70 + Math.sin(t * 13) * 50, y: -60 + Math.cos(t * 11) * 40 }; feet[1] = { x: 70 + Math.cos(t * 12) * 50, y: -40 + Math.sin(t * 14) * 40 }; }
  feet.forEach((f, k) => {
    const hx = k ? 20 : -20, L = RC.leg, d = Math.hypot(f.x - hx, f.y - hipY);
    const fx = d > L ? hx + (f.x - hx) * L / d : f.x, fy = d > L ? hipY + (f.y - hipY) * L / d : f.y;
    const r = hose(g, hx, hipY, fx, fy, L, -1, 8.5, 7.5);
    const toe = f.planted ? 0 : clamp(-f.y / 200, -0.4, 0.5);
    g.save(); g.translate(fx, fy); g.rotate(-toe); g.beginPath(); g.ellipse(8, -3, 15, 7, 0, 0, 7); g.fillStyle = RC.ink; g.fill(); g.restore();
    if (dbg) { g.fillStyle = f.planted ? '#2f2' : '#f33'; g.beginPath(); g.arc(fx, fy, 9, 0, 7); g.fill(); g.fillStyle = '#ff0'; g.beginPath(); g.arc(r.cx, r.cy, 5, 0, 7); g.fill(); }
  });
  // torso
  g.save(); g.translate(0, hipY + 14); rcTorso(g, cos, RC.torsoW, RC.torsoH, t); g.restore();
  // arms: thin rubber-hose lines, small dark round hands
  const hands = [], sY = top + 40;
  const arms = st.ragdoll ? [[-RC.torsoW / 2 + 4, sY, -2.3 + Math.sin(t * 15) * 0.7, 0.5], [RC.torsoW / 2 - 4, sY, 2.3 + Math.cos(t * 14) * 0.7, -0.5]]
    : [[-RC.torsoW / 2 + 4, sY, P.armL, P.elL], [RC.torsoW / 2 - 4, sY, P.armR, P.elR]];
  const A = RC.arm / 2;
  for (const [sx, sy0, a, e] of arms) {
    const ex = sx + Math.sin(a) * A, ey = sy0 + Math.cos(a) * A, ha = a + e, hx = ex + Math.sin(ha) * A, hy = ey + Math.cos(ha) * A;
    const side = Math.sign((hx - sx) * (ey - sy0) - (hy - sy0) * (ex - sx)) || 1;
    hose(g, sx, sy0, hx, hy, RC.arm, side, 7.5, 6.5); hands.push([hx, hy, ha]);
  }
  if (st.prop && window.drawHandProp) drawHandProp(g, st.prop, hands, t, st);
  for (const [hx, hy] of hands) { g.beginPath(); g.arc(hx, hy, 10, 0, 7); g.fillStyle = RC.ink; g.fill(); }
  // head
  const hcY = top - R * 0.78;
  let tilt = (st.headTilt || 0) + (ga ? 0.03 * Math.sin(4 * Math.PI * fracp(((st.dist || 0) / LK) / ga.G.S + (st.cycle || 0)) - 1.0) : 0.025 * Math.sin(t * 1.3 + (st.seed || 0) * 1.7));
  if (st.moodT != null) tilt += 0.06 * pulse(t, st.moodT, 0.3);
  g.save(); g.translate(0, hcY); g.rotate(tilt);
  const mood = st.mood || def.mood || 'neutral';
  let brow = BROWS[mood] || BROWS.neutral;
  if (st.prevMood && st.prevMood !== mood && t - st.moodT < 0.3) { const a = BROWS[st.prevMood] || BROWS.neutral, u = eBack(clamp((t - st.moodT) / 0.3), 1.6); brow = [lerp(a[0], brow[0], u), lerp(a[1], brow[1], u)]; }
  rcHead(g, R, def, st, { mood, blink: st.blink, talk: st.talk, brow, yaw: st.yaw || 0, pitch: st.pitch || 0, gaze: st.gaze, vis: st.vis, visOpen: st.visOpen });
  if (!st.hatOff) {
    const hs = def.hat && def.hat !== 'none' ? hatSpring(def, st, t) : { rot: 0, dy: 0 };
    g.save(); g.translate((st.yaw || 0) * R * 0.08, -R * 0.55 + hs.dy); g.rotate(hs.rot + (st.yaw || 0) * 0.06); g.translate(0, R * 0.55); g.scale(1.06, 1.06);
    (HATS[def.hat] || HATS.none)(g, R, { t, sway: hs.rot }); g.restore();
  }
  if (DEBUG.has('lipsync') && st.visLabel) { g.save(); g.scale(1 / s, 1 / s); g.font = '700 34px monospace'; g.textAlign = 'center'; g.fillStyle = '#000c'; g.fillRect(-150, R * s, 300, 76); g.fillStyle = '#ff0'; g.fillText(st.visLabel, 0, R * s + 32); g.fillStyle = '#fff'; g.fillText(st.visWord || '', 0, R * s + 68); g.restore(); }
  g.restore();
  g.restore();
  return { headY: st.y + (hcY - air) * s };
}
