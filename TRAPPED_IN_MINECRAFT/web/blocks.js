// The blocky world, drawn in side view: pixel-textured blocks (8x8 'pixels' per block) with ink outlines.
// Original textures made in code - grass, dirt, stone, log, leaves, planks, cobble, wool bed, door, torch.
const BS = 110;                                   // block size in pixels
const PAL = {
  grass: ['#5fbf3f', '#4fa833', '#72d14f'], dirt: ['#8a5a36', '#7a4c2c', '#9b6a42'], stone: ['#8e9197', '#7c7f86', '#a0a3a9'],
  log: ['#6e4a2a', '#5a3b20', '#80593a'], leaves: ['#3e9c3a', '#2f8030', '#52b049'], planks: ['#c48b4e', '#b07a40', '#d39b5c'],
  cobble: ['#8a8d92', '#6f7277', '#a3a6ab'], wool: ['#d23a3a', '#b82f2f', '#e45050'], night: ['#1c2338', '#161c2e', '#232b45'],
};
const _tiles = {};
function tile(kind, seed = 0) {                   // cached 8x8 pixel texture, upscaled with crisp pixels
  const key = kind + seed;
  if (_tiles[key]) return _tiles[key];
  const c = document.createElement('canvas'); c.width = c.height = 8; const g = c.getContext('2d');
  const p = PAL[kind] || PAL.stone;
  for (let y = 0; y < 8; y++) for (let x = 0; x < 8; x++) {
    let col = p[0];
    const h = hash(x * 13.1 + y * 7.7 + seed * 31 + kind.length * 3);
    if (h < 0.22) col = p[1]; else if (h > 0.84) col = p[2];
    if (kind === 'grass' && y > 1 + (hash(x + seed) > 0.6 ? 1 : 0)) { const d = PAL.dirt; col = h < 0.25 ? d[1] : h > 0.85 ? d[2] : d[0]; }
    if (kind === 'log' && (x === 2 || x === 5)) col = p[1];
    if (kind === 'planks' && (y === 3 || y === 7)) col = p[1];
    if (kind === 'cobble' && ((x + y * 3) % 5 === 0)) col = p[1];
    g.fillStyle = col; g.fillRect(x, y, 1, 1);
  }
  _tiles[key] = c; return c;
}
function block(ctx, kind, x, y, s = 1, o = {}) {
  const w = BS * s;
  ctx.save(); ctx.imageSmoothingEnabled = false;
  ctx.globalAlpha = o.alpha ?? 1;
  ctx.drawImage(tile(kind, o.seed ?? Math.round(x * 0.01 + y * 0.013)), x, y, w, w);
  if (o.crack) {                                   // crack stages 0..1
    ctx.strokeStyle = 'rgba(20,15,25,0.85)'; ctx.lineWidth = 4 * s; ctx.lineCap = 'round';
    const n = Math.ceil(o.crack * 6);
    for (let i = 0; i < n; i++) { const a = hash(i * 3.3) * Math.PI * 2, r = w * (0.2 + 0.3 * hash(i)); ctx.beginPath(); ctx.moveTo(x + w / 2, y + w / 2); ctx.lineTo(x + w / 2 + Math.cos(a) * r, y + w / 2 + Math.sin(a) * r); ctx.stroke(); }
  }
  if (o.shade) { ctx.fillStyle = `rgba(10,10,30,${o.shade})`; ctx.fillRect(x, y, w, w); }
  ctx.globalAlpha = 1;
  if (o.outline !== false) { ctx.lineWidth = 4 * s; ctx.strokeStyle = INK; ctx.strokeRect(x, y, w, w); }
  ctx.restore();
}
// a small dropped item block (spins and bobs)
function miniBlock(ctx, kind, cx, cy, size, t, spin = 1) {
  ctx.save(); ctx.translate(cx, cy + Math.sin(t * 4) * 6); ctx.rotate(Math.sin(t * 3 * spin) * 0.25);
  block(ctx, kind, -size / 2, -size / 2, size / BS); ctx.restore();
}
// ground: a row of grass on top, dirt below, starting at gy, from x0 to x1
function ground(ctx, gy, x0 = -1400, x1 = 2600, kind = 'grass', under = 'dirt', shade = 0) {
  for (let x = Math.floor(x0 / BS) * BS; x < x1; x += BS) {
    block(ctx, kind, x, gy, 1, { shade });
    for (let k = 1; k < 9; k++) block(ctx, k > 3 ? 'stone' : under, x, gy + k * BS, 1, { shade });
  }
}
function tree(ctx, bx, gy, logs, o = {}) {        // bx = left of trunk; logs = number of trunk blocks left (from the bottom)
  const H = 4, top = gy - H * BS;
  const leafY = top - BS * 2 + (o.leafDy || 0);
  for (let i = 0; i < H; i++) if (i >= H - logs) block(ctx, 'log', bx, gy - (H - i) * BS, 1, { crack: o.crackRow === i ? o.crack : 0, seed: i });
  for (const [dx, dy] of [[-2, 1], [-1, 1], [0, 1], [1, 1], [2, 1], [-1, 0], [0, 0], [1, 0], [0, -1], [-2, 2], [-1, 2], [1, 2], [2, 2]])
    block(ctx, 'leaves', bx + dx * BS, leafY + dy * BS, 1, { seed: dx * 3 + dy });
}
function skyGrad(ctx, top, bot) { const g = ctx.createLinearGradient(0, -1200, 0, 2200); g.addColorStop(0, top); g.addColorStop(1, bot); ctx.fillStyle = g; ctx.fillRect(-1400, -1400, 4000, 4000); }
function squareSun(ctx, x, y, s, col = '#ffe14d') {
  glow(ctx, x, y, 260 * s, 'rgba(255,240,170,A)', 0.5);
  rrect(ctx, x - 80 * s, y - 80 * s, 160 * s, 160 * s, 6); fs(ctx, col, 8);
  rrect(ctx, x - 50 * s, y - 50 * s, 100 * s, 100 * s, 4); ctx.fillStyle = 'rgba(255,255,255,0.35)'; ctx.fill();
}
function squareMoon(ctx, x, y, s) { rrect(ctx, x - 70 * s, y - 70 * s, 140 * s, 140 * s, 6); fs(ctx, '#eef0f6', 8); for (const [dx, dy] of [[-25, -20], [20, 15]]) { rrect(ctx, x + dx * s - 12 * s, y + dy * s - 12 * s, 24 * s, 24 * s, 3); ctx.fillStyle = '#c9ccd6'; ctx.fill(); } }
function blockCloud(ctx, x, y, s, a = 1) {
  ctx.save(); ctx.globalAlpha = a;
  for (const [dx, dy, w, h] of [[0, 0, 4, 1], [1, -1, 2, 1]]) { rrect(ctx, x + dx * 70 * s, y + dy * 50 * s, w * 70 * s, h * 50 * s, 4); fs(ctx, '#ffffff', 6); }
  ctx.restore();
}
function torch(ctx, x, y, t, s = 1) {
  glow(ctx, x, y - 70 * s, 420 * s, 'rgba(255,190,90,A)', 0.45 + 0.08 * Math.sin(t * 13) * Math.sin(t * 7));
  rrect(ctx, x - 9 * s, y - 70 * s, 18 * s, 80 * s, 3); fs(ctx, '#8a5a36', 5);
  const fl = 1 + 0.15 * Math.sin(t * 17);
  ctx.beginPath(); ctx.moveTo(x - 14 * s, y - 70 * s); ctx.quadraticCurveTo(x, y - (125 * fl) * s, x + 14 * s, y - 70 * s); ctx.closePath(); fs(ctx, '#ffb02e', 5);
  ctx.beginPath(); ctx.moveTo(x - 7 * s, y - 72 * s); ctx.quadraticCurveTo(x, y - (100 * fl) * s, x + 7 * s, y - 72 * s); ctx.closePath(); ctx.fillStyle = '#fff1a8'; ctx.fill();
}
function door(ctx, x, y, s = 1, open = 0) {      // two blocks tall
  const w = BS * s * (1 - open * 0.75);
  rrect(ctx, x, y, w, BS * 2 * s, 3); fs(ctx, '#a8733e', 6 * s);
  for (const yy of [0.5, 1.5]) { rrect(ctx, x + w * 0.18, y + BS * s * (yy - 0.32), w * 0.64, BS * s * 0.5, 3); fs(ctx, '#8a5a32', 4 * s); }
  circ(ctx, x + w * 0.8, y + BS * s * 1.05, 7 * s); fs(ctx, '#ffd23f', 3 * s);
}
function bed(ctx, x, y, s = 1) {                  // two blocks wide, half a block tall
  rrect(ctx, x, y, BS * 2 * s, BS * 0.55 * s, 6); fs(ctx, '#e8e2d6', 6);
  ctx.save(); ctx.imageSmoothingEnabled = false; ctx.drawImage(tile('wool', 2), x + BS * 0.55 * s, y, BS * 1.45 * s, BS * 0.42 * s); ctx.restore();
  ctx.lineWidth = 6 * Math.min(s, 1.5); ctx.strokeStyle = INK; ctx.strokeRect(x + BS * 0.55 * s, y, BS * 1.45 * s, BS * 0.42 * s);
  rrect(ctx, x + 8 * s, y + 6 * s, BS * 0.42 * s, BS * 0.3 * s, 8); fs(ctx, '#ffffff', 5);
  for (const dx of [0.05, 1.85]) { rrect(ctx, x + BS * dx * s, y + BS * 0.5 * s, 18 * s, 34 * s, 3); fs(ctx, '#8a5a32', 5); }
}
// a little "item slot" counter (generic UI)
function slot(ctx, x, y, kind, count, s = 1, pop = 1) {
  ctx.save(); ctx.translate(x, y); ctx.scale(pop * s, pop * s);
  rrect(ctx, -70, -70, 140, 140, 14); fs(ctx, 'rgba(40,40,50,0.82)', 8);
  block(ctx, kind, -45, -45, 90 / BS);
  ctx.font = '700 64px Poppins'; ctx.textAlign = 'right'; ctx.textBaseline = 'alphabetic';
  ctx.lineWidth = 12; ctx.strokeStyle = INK; ctx.strokeText(String(count), 62, 62); ctx.fillStyle = '#fff'; ctx.fillText(String(count), 62, 62);
  ctx.restore();
}
