// Environments: sky, sea, ships, islands, the burning walls of Troy, the cave, the underworld, the storm and the
// palace hall. Bright, saturated, ink-outlined. Drawn in world pixels around the 1080x1920 frame.
function sky(ctx, top, bot, x0 = -1200, x1 = 2300, y0 = -1500, y1 = 2000) {
  const g = ctx.createLinearGradient(0, y0, 0, y1); g.addColorStop(0, top); g.addColorStop(1, bot);
  ctx.fillStyle = g; ctx.fillRect(x0, y0, x1 - x0, y1 - y0);
}
function sun(ctx, x, y, r, t) {
  glow(ctx, x, y, r * 2.4, 'rgba(255,240,170,A)', 0.55);
  circ(ctx, x, y, r); fs(ctx, '#ffe25c', 10);
  for (let i = 0; i < 12; i++) { const a = i / 12 * Math.PI * 2 + t * 0.3; line(ctx, [[x + Math.cos(a) * r * 1.25, y + Math.sin(a) * r * 1.25], [x + Math.cos(a) * r * 1.55, y + Math.sin(a) * r * 1.55]], 10, '#ffcf3a'); }
}
function cloud(ctx, x, y, s, col = '#ffffff') {
  ctx.beginPath();
  for (const [dx, dy, r] of [[-90, 10, 60], [-30, -25, 75], [45, -10, 70], [100, 15, 50], [0, 25, 60]]) { ctx.moveTo(x + (dx + r) * s, y + dy * s); ctx.arc(x + dx * s, y + dy * s, r * s, 0, Math.PI * 2); }
  ctx.lineWidth = 16 * s; ctx.strokeStyle = INK; ctx.stroke();      // outline first, then the fill covers the inner half
  ctx.fillStyle = col; ctx.fill();
}
function sea(ctx, y, t, col = '#2b8ee6', col2 = '#5ab4f5', x0 = -1200, x1 = 2300) {
  ctx.fillStyle = col; ctx.fillRect(x0, y, x1 - x0, 3000);
  for (let row = 0; row < 7; row++) {
    const yy = y + 30 + row * row * 28, amp = 10 + row * 4, sp = 1 + row * 0.3;
    ctx.beginPath();
    for (let x = x0; x <= x1; x += 30) { const v = Math.sin(x * 0.012 + t * sp + row) * amp; x === x0 ? ctx.moveTo(x, yy + v) : ctx.lineTo(x, yy + v); }
    ctx.lineWidth = 6 + row; ctx.strokeStyle = row % 2 ? col2 : 'rgba(255,255,255,0.55)'; ctx.stroke();
  }
  ctx.beginPath();
  for (let x = x0; x <= x1; x += 24) { const v = Math.sin(x * 0.01 + t * 1.3) * 8; x === x0 ? ctx.moveTo(x, y + v) : ctx.lineTo(x, y + v); }
  ctx.lineWidth = 10; ctx.strokeStyle = INK; ctx.stroke();
}
function ship(ctx, x, y, s, t, o = {}) {
  const rock = Math.sin(t * 1.6 + (o.seed || 0)) * 0.05 + (o.tilt || 0);
  withT(ctx, x, y, rock, s, () => {
    if (o.sail !== false) {
      line(ctx, [[0, 0], [0, -430]], 16);
      ctx.beginPath(); ctx.moveTo(-170, -400); ctx.quadraticCurveTo(0, -390 + (o.billow ?? 30), 170, -400); ctx.lineTo(160, -140); ctx.quadraticCurveTo(0, -120 + (o.billow ?? 30) * 2, -160, -140); ctx.closePath();
      fs(ctx, o.sailCol || '#f6efe0', 10);
      if (o.stripes !== false) for (const dx of [-100, 0, 100]) { ctx.save(); ctx.clip(); ctx.fillStyle = o.stripeCol || '#e2403b'; ctx.fillRect(dx - 22, -420, 44, 320); ctx.restore(); }
      if (o.emblem) withT(ctx, 0, -270, 0, 0.9, () => headgear(ctx, 64, { gear: { helmet: true } }, false));
      line(ctx, [[-180, -405], [180, -405]], 12, '#7a4a26');
    }
    ctx.beginPath(); ctx.moveTo(-300, -40); ctx.quadraticCurveTo(-280, 60, -150, 70); ctx.lineTo(170, 70); ctx.quadraticCurveTo(300, 50, 330, -70);
    ctx.lineTo(300, -60); ctx.lineTo(290, -40); ctx.closePath(); fs(ctx, o.hull || '#8a5432', 10);
    line(ctx, [[-290, -20], [300, -20]], 6, '#5b331b');
    for (let i = 0; i < 6; i++) circ(ctx, -200 + i * 80, 20, 14), fs(ctx, '#e0a63a', 5);
    ctx.beginPath(); ctx.moveTo(330, -70); ctx.quadraticCurveTo(380, -130, 350, -170); ctx.quadraticCurveTo(330, -120, 300, -90); fs(ctx, o.hull || '#8a5432', 8);
    if (o.oars) for (let i = 0; i < 5; i++) { const a = Math.sin(t * 4 + i) * 0.3; line(ctx, [[-180 + i * 80, 30], [-200 + i * 80 + Math.sin(a) * 60, 130]], 7, '#b88a5a'); }
  });
}
function island(ctx, x, y, s, t, o = {}) {
  withT(ctx, x, y, 0, s, () => {
    ctx.beginPath(); ctx.moveTo(-420, 0); ctx.quadraticCurveTo(-250, -150, 0, -160); ctx.quadraticCurveTo(260, -150, 420, 0); ctx.closePath(); fs(ctx, '#ffd98a', 10);
    if (o.palm !== false) palm(ctx, 60, -150, 1, t);
  });
}
function palm(ctx, x, y, s, t) {
  withT(ctx, x, y, Math.sin(t * 1.2) * 0.03, s, () => {
    ctx.beginPath(); ctx.moveTo(-14, 0); ctx.quadraticCurveTo(-40, -200, 20, -380); ctx.lineTo(44, -375); ctx.quadraticCurveTo(-10, -200, 16, 0); ctx.closePath(); fs(ctx, '#b07a45', 8);
    for (let i = 0; i < 6; i++) { const a = -Math.PI / 2 + (i - 2.5) * 0.55 + Math.sin(t * 2 + i) * 0.05; withT(ctx, 32, -378, a + Math.PI / 2, 1, () => { ctx.beginPath(); ctx.moveTo(0, 0); ctx.quadraticCurveTo(80, -70, 190, -10); ctx.quadraticCurveTo(90, -20, 0, 0); fs(ctx, '#3fbf5a', 7); }); }
    for (const dx of [10, 40]) { circ(ctx, dx, -362, 16); fs(ctx, '#7a4a26', 5); }
  });
}
function rock(ctx, x, y, w, h, col = '#8f8a99') {
  ctx.beginPath(); ctx.moveTo(x - w, y); ctx.lineTo(x - w * 0.7, y - h * 0.7); ctx.lineTo(x - w * 0.2, y - h); ctx.lineTo(x + w * 0.4, y - h * 0.85); ctx.lineTo(x + w, y - h * 0.3); ctx.lineTo(x + w, y); ctx.closePath(); fs(ctx, col, 9);
}
function flames(ctx, x, y, w, h, t, seed = 0) {
  for (let i = 0; i < 7; i++) {
    const fx = x - w / 2 + (i + 0.5) * w / 7, fh = h * (0.6 + 0.4 * Math.abs(Math.sin(t * 6 + i * 1.7 + seed)));
    ctx.beginPath(); ctx.moveTo(fx - w / 9, y); ctx.quadraticCurveTo(fx - w / 14, y - fh * 0.6, fx + Math.sin(t * 9 + i) * 10, y - fh); ctx.quadraticCurveTo(fx + w / 14, y - fh * 0.5, fx + w / 9, y); ctx.closePath();
    fs(ctx, i % 2 ? '#ffb02e' : '#ff5a2e', 6);
  }
}
function troyWalls(ctx, t, burn = 1) {
  sky(ctx, '#3a1d4a', '#ff7a3d');
  glow(ctx, 540, 900, 900, 'rgba(255,120,40,A)', 0.45 * burn);
  // walls and towers
  ctx.fillStyle = '#c99a6a';
  for (const [x, w, h] of [[-200, 420, 520], [260, 240, 760], [560, 380, 560], [980, 300, 700]]) {
    rrect(ctx, x, 1300 - h, w, h + 700, 4); fs(ctx, '#d9a978', 10);
    for (let yy = 1300 - h + 40; yy < 1300; yy += 70) line(ctx, [[x + 10, yy], [x + w - 10, yy]], 4, '#a8794d');
    for (let k = 0; k < Math.floor(w / 70); k++) { rrect(ctx, x + 10 + k * 70, 1300 - h - 40, 44, 44, 4); fs(ctx, '#d9a978', 8); }
    if (burn) flames(ctx, x + w / 2, 1300 - h - 30, w * 0.9, 220, t, x);
  }
  // smoke
  for (let i = 0; i < 6; i++) { const u = (t * 0.15 + i / 6) % 1; ctx.save(); ctx.globalAlpha = 0.35 * (1 - u); circ(ctx, 200 + i * 150 + u * 80, 600 - u * 700, 90 + u * 120); ctx.fillStyle = '#2b2233'; ctx.fill(); ctx.restore(); }
  ctx.fillStyle = '#7b5a3a'; ctx.fillRect(-1200, 1300, 3500, 1400); line(ctx, [[-1200, 1300], [2300, 1300]], 10);
}
function trojanHorse(ctx, x, y, s) {
  withT(ctx, x, y, 0, s, () => {
    for (const dx of [-120, -60, 80, 140]) line(ctx, [[dx, -40], [dx, -230]], 26, '#8a5432');
    rrect(ctx, -170, -360, 340, 150, 50); fs(ctx, '#b07a45', 10);
    for (let k = 0; k < 4; k++) line(ctx, [[-150, -330 + k * 32], [150, -330 + k * 32]], 4, '#8a5432');
    poly(ctx, [[110, -330], [170, -520], [250, -520], [270, -470], [200, -440], [170, -300]]); fs(ctx, '#b07a45', 10);
    circ(ctx, 220, -495, 8); ctx.fillStyle = INK; ctx.fill();
    for (const dx of [-140, 120]) { circ(ctx, dx, -20, 30); fs(ctx, '#6b4426', 8); }
    rrect(ctx, -180, -60, 360, 30, 10); fs(ctx, '#7a4a26', 8);
  });
}
function cave(ctx, t) {
  sky(ctx, '#2a1c16', '#5a3a28');
  for (let i = 0; i < 9; i++) { const x = -100 + i * 160; poly(ctx, [[x - 70, -400], [x + 70, -400], [x, -150 - hash(i) * 220]]); fs(ctx, '#4a3022', 8); }
  ctx.fillStyle = '#3b2619'; ctx.fillRect(-1200, 1450, 3500, 1200); line(ctx, [[-1200, 1450], [2300, 1450]], 10);
  glow(ctx, 300, 1200, 500, 'rgba(255,170,80,A)', 0.35);
}
function hades(ctx, t) {
  sky(ctx, '#1b0f3a', '#5b2a8a');
  for (let i = 0; i < 40; i++) { const x = hash(i) * 1400 - 160, y = hash(i * 3) * 1600, tw = 0.5 + 0.5 * Math.sin(t * 3 + i); circ(ctx, x, y, 3 + tw * 3); ctx.fillStyle = `rgba(190,255,240,${0.4 + tw * 0.5})`; ctx.fill(); }
  // glowing river
  ctx.fillStyle = '#2fd6c0'; ctx.fillRect(-1200, 1480, 3500, 120);
  for (let k = 0; k < 3; k++) { ctx.beginPath(); for (let x = -1200; x < 2300; x += 30) { const v = Math.sin(x * 0.01 + t * 2 + k) * 8; x === -1200 ? ctx.moveTo(x, 1500 + k * 35 + v) : ctx.lineTo(x, 1500 + k * 35 + v); } ctx.lineWidth = 5; ctx.strokeStyle = 'rgba(255,255,255,0.5)'; ctx.stroke(); }
  ctx.fillStyle = '#2a1640'; ctx.fillRect(-1200, 1600, 3500, 1200); line(ctx, [[-1200, 1480], [2300, 1480]], 10);
  for (const [x, h] of [[-80, 700], [200, 520], [880, 640], [1150, 800]]) { poly(ctx, [[x - 120, 1480], [x - 30, 1480 - h], [x + 60, 1480 - h * 0.8], [x + 140, 1480]]); fs(ctx, '#3b1f5a', 9); }
}
function stormSky(ctx, t, flash = 0) {
  sky(ctx, '#1d2433', '#3d4a63');
  for (let i = 0; i < 6; i++) cloud(ctx, -100 + i * 260 + Math.sin(t + i) * 30, 220 + (i % 2) * 120, 2.0, '#4b556b');
  ctx.save(); ctx.strokeStyle = 'rgba(180,200,230,0.55)'; ctx.lineWidth = 4;
  for (let i = 0; i < 80; i++) { const x = (hash(i) * 1600 - 200 + t * 300) % 1600 - 200, y = (hash(i * 7) * 2200 + t * 1600) % 2200 - 200; ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x - 20, y + 60); ctx.stroke(); }
  ctx.restore();
  if (flash > 0) { ctx.save(); ctx.globalAlpha = flash * 0.7; ctx.fillStyle = '#e8f0ff'; ctx.fillRect(-1200, -1500, 3500, 3500); ctx.restore(); }
}
function bolt(ctx, x0, y0, x1, y1, seed = 1) {
  const pts = [[x0, y0]];
  for (let i = 1; i < 8; i++) { const u = i / 8; pts.push([lerp(x0, x1, u) + (hash(i * 3 + seed) - 0.5) * 140, lerp(y0, y1, u)]); }
  pts.push([x1, y1]);
  line(ctx, pts, 34, INK); line(ctx, pts, 20, '#fff36b'); line(ctx, pts, 8, '#ffffff');
}
function hall(ctx, t) {
  sky(ctx, '#f3d9a6', '#e8b97a');
  ctx.fillStyle = '#c98b52'; ctx.fillRect(-1200, 1350, 3500, 1300);
  for (let x = -1200; x < 2300; x += 120) for (let row = 0; row < 6; row++) if ((x / 120 + row) % 2 === 0) { ctx.fillStyle = '#b5773f'; ctx.fillRect(x, 1350 + row * 90, 120, 90); }
  line(ctx, [[-1200, 1350], [2300, 1350]], 10);
  for (const x of [-60, 300, 780, 1140]) {
    rrect(ctx, x - 55, 200, 110, 1150, 6); fs(ctx, '#fff6e6', 10);
    for (const dx of [-25, 0, 25]) line(ctx, [[x + dx, 240], [x + dx, 1310]], 4, '#e6d6b8');
    rrect(ctx, x - 80, 170, 160, 50, 6); fs(ctx, '#fff6e6', 9); rrect(ctx, x - 80, 1320, 160, 40, 6); fs(ctx, '#fff6e6', 9);
  }
  for (const x of [120, 960]) { rrect(ctx, x - 70, 300, 140, 380, 6); fs(ctx, '#3a7bd5', 8); poly(ctx, [[x - 70, 680], [x, 740], [x + 70, 680]]); fs(ctx, '#3a7bd5', 8); circ(ctx, x, 470, 40); fs(ctx, ACC.gold, 6); }
}
function throne(ctx, x, y, s) {
  withT(ctx, x, y, 0, s, () => {
    rrect(ctx, -110, -420, 220, 300, 30); fs(ctx, ACC.gold, 10); rrect(ctx, -130, -140, 260, 60, 14); fs(ctx, '#d4402e', 9);
    for (const dx of [-115, 115]) { rrect(ctx, dx - 18, -150, 36, 150, 8); fs(ctx, ACC.gold, 8); }
  });
}
function axes(ctx, x, y, n, gap, s) {
  for (let i = 0; i < n; i++) withT(ctx, x + i * gap, y, 0, s, () => {
    line(ctx, [[0, 0], [0, -180]], 14, '#8a5432');
    ctx.beginPath(); ctx.moveTo(0, -200); ctx.quadraticCurveTo(70, -230, 80, -170); ctx.quadraticCurveTo(70, -110, 0, -140); ctx.closePath(); fs(ctx, '#c9d2dc', 7);
    circ(ctx, 34, -170, 16); fs(ctx, '#2b2a36', 5);
  });
}
function grassBeach(ctx, y, col = '#ffd98a') { ctx.fillStyle = col; ctx.fillRect(-1200, y, 3500, 1500); line(ctx, [[-1200, y], [2300, y]], 10); }
function deck(ctx, y) {
  ctx.fillStyle = '#b8814f'; ctx.fillRect(-1200, y, 3500, 1500);
  for (let k = 0; k < 8; k++) line(ctx, [[-1200, y + 30 + k * 60], [2300, y + 30 + k * 60]], 5, '#8a5a32');
  line(ctx, [[-1200, y], [2300, y]], 10);
}
