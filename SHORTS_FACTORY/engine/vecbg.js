// VECTOR LOCATIONS: flat illustrated backgrounds drawn in code (dusk palette, starry purple sky, rolling green
// hills, pines), split into depth layers for the multiplane camera (sky 1000 / far 400 / mid 150 / fg 50 / near 20).
// A scene uses one with  "loc": "v_town"  (or any key of VLOC). Layers are drawn once at load, 30 % larger than
// the frame, in frame coordinates (0..1080 x 0..1920, overscan reaches -162..1242 x -288..2208). Seeded, so every
// render is identical.
const VPAL = {
  sky: [[0, '#120d2e'], [0.42, '#2b1a5a'], [0.6, '#5a2a78'], [0.69, '#b2486f'], [0.74, '#ee8a5a'], [0.78, '#f3b26a']],
  farHill: ['#5a3478', '#3f2862'], mount: ['#4a2d6a', '#2f1f4e'],
  midHill: ['#3a7a48', '#2a5a38'], nearHill: ['#4f9a4c', '#3a7a40'], ground: ['#5aa852', '#3f8644'],
  pine: '#1f4e2e', pineDark: '#173c23', pineFar: '#2d5640',
  bld: ['#c99a62', '#b07c4c', '#d9aa70', '#9c6a44', '#c08a58'], win: '#f6c85a', winOff: '#5a3a52', roof: '#6a4030',
};
const vr = (k) => hash(k * 12.9898 + 4.1414);               // seeded random 0..1

function vSky(g, o = {}) {
  const gr = g.createLinearGradient(0, -300, 0, o.horizon ?? 1500);
  for (const [p, c] of (o.pal || VPAL.sky)) gr.addColorStop(p, c);
  g.fillStyle = gr; g.fillRect(-200, -320, 1500, 2600);
  for (let i = 0; i < (o.stars ?? 300); i++) {                // stars
    const x = -170 + vr(i) * 1420, y = -290 + Math.pow(vr(i + 500), 1.6) * ((o.horizon ?? 1500) * 0.82);
    const r = 0.8 + vr(i + 900) * 2.6, a = 0.35 + vr(i + 1300) * 0.65;
    g.beginPath(); g.arc(x, y, r, 0, 7); g.fillStyle = `rgba(255,255,255,${a})`; g.fill();
    if (r > 3.0) { g.globalAlpha = 0.25; g.beginPath(); g.arc(x, y, r * 3, 0, 7); g.fill(); g.globalAlpha = 1; }
  }
  for (const [x, y, L, a] of (o.shooting || [[150, -120, 380, 0.55], [430, 60, 420, 0.5], [660, -220, 300, 0.48], [880, -40, 260, 0.5], [120, 300, 240, 0.52]])) {
    const ex = x + Math.cos(a) * L, ey = y + Math.sin(a) * L, gg = g.createLinearGradient(x, y, ex, ey);
    gg.addColorStop(0, 'rgba(255,255,255,0)'); gg.addColorStop(1, 'rgba(255,240,255,0.95)');
    g.beginPath(); g.moveTo(x, y); g.lineTo(ex, ey); g.lineWidth = 4; g.strokeStyle = gg; g.lineCap = 'round'; g.stroke();
    glowDot(g, ex, ey, 26, '235,210,255', 0.8); g.beginPath(); g.arc(ex, ey, 6, 0, 7); g.fillStyle = '#fff'; g.fill();
  }
  if (o.sunGlow !== false) glowDot(g, o.glowX ?? 540, (o.horizon ?? 1500) * 0.74, 520, '255,150,110', 0.42);
  if (o.rocket) vRocket(g, o.rocket[0], o.rocket[1], o.rocket[2] || 1);
}
function glowDot(g, x, y, r, rgb, a) { const gr = g.createRadialGradient(x, y, 0, x, y, r); gr.addColorStop(0, `rgba(${rgb},${a})`); gr.addColorStop(1, `rgba(${rgb},0)`); g.fillStyle = gr; g.fillRect(x - r, y - r, r * 2, r * 2); }
function vRocket(g, x, y, s) {                                 // the rocket launch and the crack in the sky
  g.save(); g.lineJoin = 'round'; g.lineCap = 'round';
  const pts = [[-260, -170], [-150, -110], [-90, -160], [40, -60], [120, -120], [250, -10], [320, -40], [430, 50]].map(([a, b]) => [x + a * s, y + b * s]);
  for (const [w, c] of [[30, 'rgba(120,200,255,0.18)'], [16, 'rgba(170,225,255,0.45)'], [6, 'rgba(240,250,255,1)']]) {
    g.beginPath(); pts.forEach(([a, b], i) => i ? g.lineTo(a, b) : g.moveTo(a, b)); g.lineWidth = w * s; g.strokeStyle = c; g.stroke();
  }
  for (const [i, dx, dy] of [[1, -25, -55], [3, 30, 50], [5, -20, -50]]) { g.beginPath(); g.moveTo(pts[i][0], pts[i][1]); g.lineTo(pts[i][0] + dx * s, pts[i][1] + dy * s); g.lineWidth = 3 * s; g.strokeStyle = '#e8f6ff'; g.stroke(); }
  const rx = x + 80 * s, ry = y + 60 * s;
  for (let k = 0; k < 9; k++) { g.beginPath(); g.arc(rx + Math.sin(k * 1.7) * 14 * s, ry + 70 * s + k * 45 * s, (26 + k * 6) * s, 0, 7); g.fillStyle = `rgba(245,240,250,${0.92 - k * 0.07})`; g.fill(); }
  g.save(); g.translate(rx, ry); g.rotate(-0.25); g.scale(s, s);
  g.beginPath(); g.moveTo(0, -80); g.quadraticCurveTo(26, -40, 22, 40); g.lineTo(-22, 40); g.quadraticCurveTo(-26, -40, 0, -80); g.fillStyle = '#f2f2f6'; g.fill(); g.lineWidth = 4; g.strokeStyle = '#2a2236'; g.stroke();
  g.beginPath(); g.moveTo(0, -80); g.quadraticCurveTo(14, -62, 16, -48); g.lineTo(-16, -48); g.quadraticCurveTo(-14, -62, 0, -80); g.fillStyle = '#e04a3a'; g.fill(); g.stroke();
  for (const sd of [-1, 1]) { g.beginPath(); g.moveTo(sd * 20, 10); g.lineTo(sd * 40, 46); g.lineTo(sd * 20, 40); g.closePath(); g.fillStyle = '#e04a3a'; g.fill(); g.stroke(); }
  g.beginPath(); g.arc(0, -18, 9, 0, 7); g.fillStyle = '#4aa8ff'; g.fill(); g.stroke();
  g.beginPath(); g.moveTo(-12, 42); g.quadraticCurveTo(0, 90, 12, 42); g.fillStyle = '#ffcf4a'; g.fill();
  g.restore(); g.restore();
}
function vHills(g, base, amp, seed, cols, opts = {}) {        // a rolling ridge filled down past the frame
  const pts = [];
  for (let x = -200; x <= 1300; x += 20) pts.push([x, base - amp * (0.55 * Math.sin(x * 0.0042 + seed) + 0.3 * Math.sin(x * 0.011 + seed * 2.3) + 0.15 * Math.sin(x * 0.027 + seed * 4.1)) - (opts.bump ? opts.bump(x) : 0)]);
  g.beginPath(); g.moveTo(-200, 2300); pts.forEach(([x, y]) => g.lineTo(x, y)); g.lineTo(1300, 2300); g.closePath();
  const gr = g.createLinearGradient(0, base - amp, 0, base + (opts.depth ?? 500)); gr.addColorStop(0, cols[0]); gr.addColorStop(1, cols[1]); g.fillStyle = gr; g.fill();
  if (opts.rim) { g.beginPath(); pts.forEach(([x, y], i) => i ? g.lineTo(x, y) : g.moveTo(x, y)); g.lineWidth = opts.rim[1]; g.strokeStyle = opts.rim[0]; g.stroke(); }
  return x => { const i = clamp(Math.round((x + 200) / 20), 0, pts.length - 1); return pts[i][1]; };
}
function vPine(g, x, y, h, col = VPAL.pine, dark = VPAL.pineDark) {
  g.fillStyle = '#3a2618'; g.fillRect(x - h * 0.04, y - h * 0.16, h * 0.08, h * 0.17);
  for (let k = 0; k < 3; k++) {
    const by = y - h * (0.12 + k * 0.24), w = h * (0.36 - k * 0.08), ty = by - h * 0.42;
    g.beginPath(); g.moveTo(x - w, by); g.lineTo(x, ty); g.lineTo(x + w, by); g.closePath(); g.fillStyle = col; g.fill();
    g.beginPath(); g.moveTo(x, ty); g.lineTo(x + w, by); g.lineTo(x + w * 0.15, by); g.closePath(); g.fillStyle = dark; g.fill();
  }
}
function vPines(g, n, x0, x1, groundFn, hMin, hMax, seed, col, dark) {
  const list = []; for (let i = 0; i < n; i++) { const x = lerp(x0, x1, vr(seed + i)); list.push([x, groundFn(x) + 6, lerp(hMin, hMax, vr(seed + i + 77))]); }
  list.sort((a, b) => a[1] - b[1]).forEach(([x, y, h]) => vPine(g, x, y, h, col, dark));
}
function vBuilding(g, x, base, w, h, col, seed, o = {}) {
  g.fillStyle = col; g.fillRect(x, base - h, w, h);
  g.fillStyle = 'rgba(0,0,0,0.16)'; g.fillRect(x + w * 0.82, base - h, w * 0.18, h);
  g.fillStyle = VPAL.roof; g.fillRect(x - 6, base - h - 12, w + 12, 14);
  const cols = Math.max(2, Math.floor(w / 34)), rows = Math.floor((h - 30) / 40), cw = (w - 16) / cols;
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
    g.fillStyle = vr(seed * 31 + r * 7 + c) > 0.35 ? VPAL.win : VPAL.winOff;
    g.fillRect(x + 10 + c * cw, base - h + 22 + r * 40, cw * 0.55, 22);
  }
  if (o.tank) {                                                 // a water tower on the roof
    const tx = x + w * o.tank, ty = base - h - 12;
    g.strokeStyle = '#3a2618'; g.lineWidth = 5; g.beginPath(); g.moveTo(tx - 18, ty); g.lineTo(tx - 14, ty - 34); g.moveTo(tx + 18, ty); g.lineTo(tx + 14, ty - 34); g.stroke();
    g.fillStyle = '#9a6038'; g.beginPath(); g.roundRect(tx - 26, ty - 84, 52, 54, 8); g.fill(); g.strokeStyle = '#3a2618'; g.lineWidth = 4; g.stroke();
    g.beginPath(); g.moveTo(tx - 30, ty - 84); g.lineTo(tx, ty - 108); g.lineTo(tx + 30, ty - 84); g.closePath(); g.fillStyle = '#7a4a2a'; g.fill(); g.stroke();
  }
  if (o.sign) { g.fillStyle = '#d8403a'; g.fillRect(x + w * 0.1, base - h - 52, w * 0.8, 36); g.strokeStyle = '#3a2618'; g.lineWidth = 4; g.strokeRect(x + w * 0.1, base - h - 52, w * 0.8, 36); }
}
function vTown(g, cx, base, s = 1) {                           // a skyline around a central clock tower
  g.save(); g.translate(cx, base); g.scale(s, s); g.translate(-cx, -base);
  const B = [[-330, 92, 250, 1], [-240, 110, 330, 0], [-130, 100, 400, 3], [80, 118, 380, 2, { sign: 1 }], [200, 92, 290, 4], [295, 86, 210, 3, { tank: 0.5 }], [-420, 96, 190, 4, {}], [390, 80, 160, 1]];
  B.sort((a, b) => a[2] - b[2]);
  g.fillStyle = 'rgba(255,180,120,0.18)'; g.beginPath(); g.ellipse(cx, base - 160, 520, 330, 0, 0, 7); g.fill();
  vBuilding(g, cx - 240, base, 110, 330, VPAL.bld[0], 1, { tank: 0.45 });
  for (const [dx, w, h, ci, o] of B) if (dx !== -240) vBuilding(g, cx + dx, base, w, h, VPAL.bld[ci], dx + 99, o || {});
  // clock tower
  const tx = cx - 22, tw = 64, th = 520;
  g.fillStyle = '#e2c99a'; g.fillRect(tx, base - th, tw, th); g.fillStyle = 'rgba(0,0,0,0.12)'; g.fillRect(tx + tw * 0.75, base - th, tw * 0.25, th);
  g.fillStyle = '#c9a06a'; g.fillRect(tx - 6, base - th - 12, tw + 12, 16);
  g.beginPath(); g.moveTo(tx - 12, base - th - 12); g.lineTo(tx + tw / 2, base - th - 110); g.lineTo(tx + tw + 12, base - th - 12); g.closePath(); g.fillStyle = '#8a3a2a'; g.fill(); g.lineWidth = 4; g.strokeStyle = '#3a2218'; g.stroke();
  g.beginPath(); g.arc(tx + tw / 2, base - th + 50, 25, 0, 7); g.fillStyle = '#fff6e2'; g.fill(); g.lineWidth = 5; g.strokeStyle = '#3a2218'; g.stroke();
  g.beginPath(); g.moveTo(tx + tw / 2, base - th + 50); g.lineTo(tx + tw / 2, base - th + 34); g.moveTo(tx + tw / 2, base - th + 50); g.lineTo(tx + tw / 2 + 12, base - th + 56); g.lineWidth = 4; g.stroke();
  for (const [yy, c] of [[120, '#f6c85a'], [200, '#3a2a3a'], [280, '#f6c85a']]) { g.beginPath(); g.ellipse(tx + tw / 2, base - th + yy, 11, 20, 0, 0, 7); g.fillStyle = c; g.fill(); }
  g.restore();
}
function vCloud(g, x, y, s, top = '#8a6aa8', bot = '#4a3570') {
  const gr = g.createLinearGradient(0, y - 80 * s, 0, y + 40 * s); gr.addColorStop(0, top); gr.addColorStop(1, bot); g.fillStyle = gr;
  for (const [dx, dy, r] of [[-110, 10, 52], [-55, -24, 66], [10, -40, 80], [80, -16, 62], [135, 12, 46], [0, 18, 64]]) { g.beginPath(); g.arc(x + dx * s, y + dy * s, r * s, 0, 7); g.fill(); }
}
function vCrystal(g, x, y, s, a = 1) {
  glowDot(g, x, y - 18 * s, 46 * s, '170,90,255', 0.45 * a);
  g.beginPath(); g.moveTo(x - 14 * s, y); g.lineTo(x - 6 * s, y - 40 * s); g.lineTo(x + 4 * s, y - 52 * s); g.lineTo(x + 14 * s, y); g.closePath();
  const gr = g.createLinearGradient(x - 14 * s, 0, x + 14 * s, 0); gr.addColorStop(0, '#c9a0ff'); gr.addColorStop(1, '#6a2fd0'); g.fillStyle = gr; g.fill();
  g.beginPath(); g.moveTo(x - 6 * s, y - 40 * s); g.lineTo(x + 1 * s, y); g.lineWidth = 1.5 * s; g.strokeStyle = 'rgba(255,255,255,0.6)'; g.stroke();
}
function vCrater(g, cx, cy, rx, ry) {                          // the comet crater: rim, floor, lab, the meteor in scaffolding
  glowDot(g, cx, cy, rx * 1.15, '230,170,110', 0.35);
  g.beginPath(); g.ellipse(cx, cy, rx, ry, 0, 0, 7); g.fillStyle = '#c99a62'; g.fill();
  g.beginPath(); g.ellipse(cx, cy + ry * 0.05, rx * 0.9, ry * 0.8, 0, 0, 7); g.fillStyle = '#6a442c'; g.fill();
  g.beginPath(); g.ellipse(cx, cy + ry * 0.14, rx * 0.68, ry * 0.58, 0, 0, 7); g.fillStyle = '#4a2c1e'; g.fill();
  const mx = cx + 10, my = cy + ry * 0.02;
  glowDot(g, mx, my - 70, 330, '180,90,255', 0.7);
  g.beginPath(); const P = [[-120, 20], [-95, -95], [-20, -150], [70, -130], [125, -55], [110, 40], [20, 70], [-80, 60]];
  P.forEach(([a, b], i) => i ? g.lineTo(mx + a, my + b) : g.moveTo(mx + a, my + b)); g.closePath();
  const mg = g.createLinearGradient(mx - 120, my - 150, mx + 120, my + 70); mg.addColorStop(0, '#e2c4ff'); mg.addColorStop(0.45, '#a865f0'); mg.addColorStop(1, '#5a24b0'); g.fillStyle = mg; g.fill();
  g.strokeStyle = 'rgba(255,255,255,0.55)'; g.lineWidth = 2; for (const [a, b, c, d] of [[-95, -95, 0, -20], [-20, -150, 0, -20], [70, -130, 0, -20], [125, -55, 0, -20], [0, -20, 20, 70], [0, -20, -80, 60]]) { g.beginPath(); g.moveTo(mx + a, my + b); g.lineTo(mx + c, my + d); g.stroke(); }
  g.strokeStyle = '#d6dbe6'; g.lineWidth = 5;                   // scaffold
  g.strokeRect(mx - 150, my - 175, 300, 250); g.beginPath(); for (const yy of [-110, -40, 20]) { g.moveTo(mx - 150, my + yy); g.lineTo(mx + 150, my + yy); }
  g.moveTo(mx - 150, my - 175); g.lineTo(mx - 60, my - 110); g.moveTo(mx + 150, my - 175); g.lineTo(mx + 60, my - 110); g.stroke();
  for (const [dx, dy, r] of [[-300, 10, 70], [310, 0, 80]]) {   // lab domes
    g.beginPath(); g.ellipse(cx + dx, cy + dy, r, r * 0.62, 0, Math.PI, 0); g.closePath(); g.fillStyle = '#eef0f6'; g.fill(); g.strokeStyle = '#8a90a0'; g.lineWidth = 3; g.stroke();
    g.beginPath(); g.moveTo(cx + dx, cy + dy - r * 0.62); g.lineTo(cx + dx, cy + dy - r * 0.95); g.stroke();
  }
  for (const [dx, dy, w, h, c] of [[-260, 60, 70, 40, '#e05a3a'], [-120, 110, 90, 50, '#3a6ad0'], [150, 70, 80, 44, '#e8b44a'], [170, 112, 110, 52, '#e05a3a']]) { g.fillStyle = c; g.fillRect(cx + dx, cy + dy, w, h); g.strokeStyle = 'rgba(0,0,0,0.35)'; g.lineWidth = 3; g.strokeRect(cx + dx, cy + dy, w, h); }
  for (let i = 0; i < 40; i++) { const a = vr(i + 3000) * 6.283, rr = 0.25 + vr(i + 3100) * 0.5; g.beginPath(); g.arc(mx + Math.cos(a) * 220 * rr, my - 60 + Math.sin(a) * 140 * rr, 2 + vr(i) * 3, 0, 7); g.fillStyle = 'rgba(230,200,255,0.85)'; g.fill(); }
  for (let i = 0; i < 26; i++) { const a = vr(i + 4000) * 6.283, k = 0.86 + vr(i + 4100) * 0.2; vCrystal(g, cx + Math.cos(a) * rx * k, cy + Math.sin(a) * ry * k + 10, 0.8 + vr(i + 4200) * 0.8); }
}
function vScreen(g, cx, top, w, h) {                           // a drive-in screen with a picture on it
  for (const dx of [-w * 0.42, w * 0.42]) { g.fillStyle = '#2a2230'; g.fillRect(cx + dx - 8, top + h, 16, 300); }
  g.fillStyle = '#2a2230'; g.fillRect(cx - 40, top + h, 80, 300);
  g.fillStyle = '#2a2230'; g.fillRect(cx - w / 2 - 16, top - 16, w + 32, h + 32);
  const sg = g.createLinearGradient(0, top, 0, top + h); sg.addColorStop(0, '#dfe2ff'); sg.addColorStop(1, '#b8b8f0'); g.fillStyle = sg; g.fillRect(cx - w / 2, top, w, h);
  g.beginPath(); g.arc(cx, top + h * 0.42, h * 0.2, 0, 7); g.fillStyle = '#f7d55a'; g.fill();
  g.beginPath(); g.moveTo(cx - w / 2, top + h); g.lineTo(cx - w * 0.2, top + h * 0.5); g.lineTo(cx + w * 0.02, top + h * 0.78); g.lineTo(cx + w * 0.24, top + h * 0.45); g.lineTo(cx + w / 2, top + h * 0.85); g.lineTo(cx + w / 2, top + h); g.closePath(); g.fillStyle = '#8a74d8'; g.fill();
}
function vCar(g, x, y, s, col) {
  g.save(); g.translate(x, y); g.scale(s, s);
  g.beginPath(); g.roundRect(-120, -70, 240, 56, 18); g.fillStyle = col; g.fill(); g.lineWidth = 6; g.strokeStyle = '#1e1824'; g.stroke();
  g.beginPath(); g.moveTo(-70, -70); g.lineTo(-45, -120); g.lineTo(55, -120); g.lineTo(80, -70); g.closePath(); g.fill(); g.stroke();
  g.fillStyle = '#bfe6ff'; g.fillRect(-48, -112, 42, 36); g.fillRect(4, -112, 46, 36);
  for (const dx of [-70, 70]) { g.beginPath(); g.arc(dx, -12, 26, 0, 7); g.fillStyle = '#1e1824'; g.fill(); g.beginPath(); g.arc(dx, -12, 10, 0, 7); g.fillStyle = '#9a9aa8'; g.fill(); }
  g.restore();
}
function vRock(g, x, y, s, col = '#8a8296') { g.beginPath(); g.moveTo(x - 60 * s, y); g.lineTo(x - 44 * s, y - 40 * s); g.lineTo(x - 6 * s, y - 58 * s); g.lineTo(x + 40 * s, y - 42 * s); g.lineTo(x + 62 * s, y); g.closePath(); g.fillStyle = col; g.fill();
  g.beginPath(); g.moveTo(x - 6 * s, y - 58 * s); g.lineTo(x + 40 * s, y - 42 * s); g.lineTo(x + 62 * s, y); g.lineTo(x + 8 * s, y); g.closePath(); g.fillStyle = 'rgba(0,0,0,0.18)'; g.fill(); }
function vGrass(g, n, y0, y1, seed, col = 'rgba(30,70,30,0.5)') { for (let i = 0; i < n; i++) { const x = -160 + vr(seed + i) * 1400, y = lerp(y0, y1, vr(seed + i + 50)), h = 10 + vr(seed + i + 90) * 18;
  g.beginPath(); g.moveTo(x - 6, y); g.lineTo(x - 2, y - h); g.lineTo(x + 1, y); g.lineTo(x + 4, y - h * 0.8); g.lineTo(x + 7, y); g.closePath(); g.fillStyle = col; g.fill(); } }

// ---- the locations: name -> [layer name, z, draw(g)] ----
const VLOC = {
  v_town: { sky: '#5a2a78', layers: [
    ['sky', 1000, g => vSky(g, { rocket: [930, 120, 0.9] })],
    ['far', 400, g => { vHills(g, 1140, 90, 1.3, VPAL.farHill); vHills(g, 1210, 60, 4.2, ['#4a3070', '#352458']); }],
    ['mid', 150, g => { const gf = vHills(g, 1262, 40, 2.2, VPAL.midHill, { bump: x => 60 * Math.exp(-(((x - 540) / 320) ** 2)) }); vTown(g, 540, 1225, 1.0); vHills(g, 1290, 26, 5.1, VPAL.midHill); vPines(g, 10, -150, 220, gf, 110, 170, 30); vPines(g, 9, 860, 1240, gf, 110, 170, 60); }],
    ['fg', 50, g => { const gf = vHills(g, 1430, 34, 0.7, VPAL.ground, { depth: 700 }); g.fillStyle = 'rgba(220,190,140,0.55)'; g.beginPath(); g.moveTo(440, 1380); g.lineTo(640, 1380); g.lineTo(900, 2250); g.lineTo(180, 2250); g.closePath(); g.fill(); vGrass(g, 60, 1450, 2150, 7); }],
    ['near', 20, g => { vPine(g, -110, 2120, 900); vPine(g, 1200, 2180, 1000); }],
  ] },
  v_crater: { sky: '#5a2a78', layers: [
    ['sky', 1000, g => vSky(g, { rocket: [880, 60, 0.75] })],
    ['far', 400, g => { vHills(g, 1000, 110, 2.7, VPAL.mount); vTown(g, 560, 1070, 0.45); vHills(g, 1090, 50, 0.4, VPAL.farHill); }],
    ['mid', 150, g => { const gf = vHills(g, 1180, 45, 3.3, VPAL.midHill); vPines(g, 12, -160, 250, gf, 120, 190, 11); vPines(g, 12, 830, 1250, gf, 120, 190, 41); vHills(g, 1270, 20, 1.9, VPAL.nearHill, { depth: 600 }); vCrater(g, 540, 1460, 600, 200); }],
    ['fg', 50, g => { vHills(g, 1790, 60, 2.4, VPAL.ground, { bump: x => 140 * (Math.exp(-(((x + 80) / 260) ** 2)) + Math.exp(-(((x - 1160) / 260) ** 2))) - 90 }); for (let i = 0; i < 7; i++) vCrystal(g, 120 + i * 140 + vr(i + 70) * 60, 1780 + vr(i + 80) * 120, 1.4 + vr(i + 90)); }],
    ['near', 20, g => { vPine(g, -60, 2210, 820, VPAL.pineDark, '#0f2a18'); vPine(g, 1180, 2250, 900, VPAL.pineDark, '#0f2a18'); }],
  ] },
  v_field: { sky: '#5a2a78', layers: [
    ['sky', 1000, g => vSky(g, {})],
    ['far', 400, g => { vHills(g, 1060, 150, 0.9, VPAL.mount); vHills(g, 1140, 70, 3.1, VPAL.farHill); }],
    ['mid', 150, g => { const gf = vHills(g, 1180, 50, 4.4, VPAL.midHill, { bump: x => 150 * Math.exp(-(((x - 850) / 170) ** 2)) }); vPines(g, 9, -160, 380, gf, 120, 200, 21);
      for (let i = 0; i < 6; i++) vRock(g, 790 + i * 26 - vr(i) * 40, gf(820 + i * 20) + 14, 0.9 + vr(i + 3) * 0.6); vPines(g, 4, 1000, 1250, gf, 120, 180, 52); }],
    ['fg', 50, g => { vHills(g, 1330, 40, 1.6, VPAL.ground, { depth: 800 }); vGrass(g, 70, 1360, 2180, 17); vRock(g, 820, 1700, 1.2); vRock(g, 160, 1620, 0.8); }],
    ['near', 20, g => { vPine(g, -120, 2160, 900); vGrass(g, 30, 2080, 2220, 33, 'rgba(25,60,25,0.85)'); }],
  ] },
  v_drivein: { sky: '#5a2a78', layers: [
    ['sky', 1000, g => vSky(g, { shooting: [[300, -100, 360, 0.6], [760, -50, 280, 0.5]] })],
    ['far', 400, g => { vHills(g, 1080, 90, 1.1, VPAL.farHill); vPines(g, 16, -160, 1250, x => 1100, 70, 110, 5, VPAL.pineFar, '#22462f'); }],
    ['mid', 150, g => { vHills(g, 1210, 8, 0.2, ['#7a6a5a', '#5a4a40'], { depth: 900 }); vScreen(g, 540, 560, 760, 420);
      for (const [x, c] of [[160, '#d8403a'], [470, '#3a7ad0'], [800, '#e8b44a'], [1060, '#5aa852']]) vCar(g, x, 1290, 0.9, c);
      for (let i = 0; i < 6; i++) vCrystal(g, 80 + i * 190 + vr(i + 20) * 50, 1250 + vr(i + 30) * 40, 1.2 + vr(i + 40) * 0.8); }],
    ['fg', 50, g => { vHills(g, 1420, 10, 0.5, ['#8a7a66', '#6a5a4c'], { depth: 800 }); for (const x of [120, 420, 720, 1010]) { g.fillStyle = '#2a2230'; g.fillRect(x - 5, 1440, 10, 120); g.fillRect(x - 22, 1430, 44, 26); } vCar(g, 120, 1720, 1.5, '#d8403a'); }],
  ] },
  v_sky: { sky: '#5a2a78', layers: [
    ['sky', 1000, g => vSky(g, { horizon: 2000, rocket: [860, 220, 0.8] })],
    ['far', 400, g => { vHills(g, 1720, 120, 2.0, VPAL.farHill); vHills(g, 1820, 60, 0.6, VPAL.midHill); vCrater(g, 700, 1860, 150, 40); }],
    ['mid', 150, g => { vCloud(g, 120, 1040, 1.4); vCloud(g, 920, 760, 1.2); vCloud(g, 560, 1400, 1.6); }],
    ['fg', 50, g => { vCloud(g, -60, 1600, 2.2, '#a080c0', '#5a4080'); vCloud(g, 1160, 1250, 2.0, '#a080c0', '#5a4080'); }],
    ['near', 20, g => { vCloud(g, 300, 2240, 3.0, '#b898d0', '#6a5090'); }],
  ] },
  v_lobby: { sky: '#1a1240', layers: [
    ['sky', 1000, g => { vSky(g, { pal: [[0, '#0c0a26'], [0.6, '#1e1450'], [0.85, '#3a1f6e'], [1, '#5a2a78']], stars: 180, shooting: [], sunGlow: false });
      for (const [x, c] of [[260, '120,140,255'], [820, '200,110,255']]) { g.save(); g.globalCompositeOperation = 'lighter'; const gr = g.createLinearGradient(x, -200, 540, 1500); gr.addColorStop(0, `rgba(${c},0.0)`); gr.addColorStop(1, `rgba(${c},0.35)`);
        g.beginPath(); g.moveTo(x - 40, -300); g.lineTo(x + 40, -300); g.lineTo(700, 1500); g.lineTo(380, 1500); g.closePath(); g.fillStyle = gr; g.fill(); g.restore(); } }],
    ['mid', 150, g => { for (let i = 0; i < 26; i++) { const x = -120 + vr(i + 700) * 1320, y = -100 + vr(i + 720) * 1100, s = 14 + vr(i + 740) * 30; g.save(); g.translate(x, y); g.rotate(vr(i + 760) * 3);
      g.fillStyle = ['#5a7aff', '#b26aff', '#ffcf4a'][i % 3]; g.globalAlpha = 0.85; g.fillRect(-s, -s, 2 * s, 2 * s); g.restore(); } }],
    ['fg', 50, g => { glowDot(g, 540, 1460, 600, '120,160,255', 0.35); g.beginPath(); g.ellipse(540, 1480, 460, 120, 0, 0, 7); g.fillStyle = '#c8cde0'; g.fill();
      g.beginPath(); g.ellipse(540, 1470, 460, 112, 0, 0, 7); g.fillStyle = '#e8ecf8'; g.fill(); g.beginPath(); g.ellipse(540, 1480, 470, 124, 0, 0, 7); g.lineWidth = 12; g.strokeStyle = '#6ad0ff'; g.stroke();
      g.fillStyle = '#9aa2bc'; g.beginPath(); g.moveTo(80, 1480); g.lineTo(1000, 1480); g.lineTo(1000, 1560); g.ellipse(540, 1560, 460, 120, 0, 0, Math.PI); g.closePath(); g.fill(); }],
  ] },
};
async function buildVectorLocation(name, script) {
  const V = VLOC[name]; if (!V) return null;
  const S = MODE === 'draft' ? 0.6 : 0.9, cw = Math.round(1404 * S), ch = Math.round(2496 * S), layers = [];
  for (const [lname, z, draw] of V.layers) {
    const c = document.createElement('canvas'); c.width = cw; c.height = ch; const g = c.getContext('2d');
    g.setTransform(S, 0, 0, S, 162 * S, 288 * S); draw(g); g.setTransform(1, 0, 0, 1, 0, 0);
    layers.push({ name: lname, z, img: c, baked: bakeLayer(c, z, V.sky, script.grade, { atmosphere: 0.35, blur: z <= 25 ? Math.round(clamp(600 * Math.abs(1 / z - 1 / 150), 0, 10) * S) : 0 }) });
  }
  layers.sort((a, b) => b.z - a.z);
  return { layers, sky: V.sky, focusZ: 150 };
}
