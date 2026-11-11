// Stick people with big white heads and expressive faces, plus the creatures: Cyclops, giants, ghosts, pigs,
// the sacred cow, Sirens. Angles are radians from straight down (0 = hanging, + = toward screen right).
const SKIN = '#ffffff';
const ACC = { bronze: '#e0a63a', bronzeD: '#a8711c', crest: '#e2403b', beard: '#5a3a22', cloak: '#8a6a4c', laurel: '#4fae55',
  circe: '#8b4bd6', calypso: '#29b3a6', penelope: '#c0533a', gold: '#ffd23f' };

function polar(x, y, a, len) { return [x + Math.sin(a) * len, y + Math.cos(a) * len]; }

// face on a head centred at (0,0) of radius R
function face(ctx, R, f) {
  const lx = (f.look || 0) * R * 0.18, ly = (f.lookY || 0) * R * 0.14;
  const mood = f.mood || 'flat';
  const eyeY = -R * 0.08 + ly, ex = R * 0.32;
  // eyes
  if (mood === 'dizzy') {
    for (const s of [-1, 1]) {
      ctx.beginPath();
      for (let i = 0; i < 40; i++) { const a = i * 0.45 + (f.t || 0) * 8, r = i * 0.45; ctx.lineTo(s * ex + lx + Math.cos(a) * r, eyeY + Math.sin(a) * r); }
      ctx.lineWidth = 4; ctx.strokeStyle = INK; ctx.stroke();
    }
  } else if (f.blink) {
    for (const s of [-1, 1]) line(ctx, [[s * ex + lx - R * 0.1, eyeY], [s * ex + lx + R * 0.1, eyeY]], 6);
  } else {
    const big = mood === 'scared' || mood === 'shock' || mood === 'o';
    const er = R * (big ? 0.17 : 0.12);
    for (const s of [-1, 1]) {
      if (big) { ell(ctx, s * ex + lx, eyeY, er, er * 1.15); fs(ctx, '#fff', 5); ell(ctx, s * ex + lx * 1.4, eyeY + 2, er * 0.45, er * 0.5); ctx.fillStyle = INK; ctx.fill(); }
      else { ell(ctx, s * ex + lx, eyeY, er * 0.75, er); ctx.fillStyle = INK; ctx.fill(); ell(ctx, s * ex + lx - er * 0.25, eyeY - er * 0.35, er * 0.25, er * 0.25); ctx.fillStyle = '#fff'; ctx.fill(); }
      // lids
      if (mood === 'smug' || mood === 'sleepy' || mood === 'evil') {
        ctx.save(); ell(ctx, s * ex + lx, eyeY, er * 0.9, er * 1.1); ctx.clip();
        ctx.fillStyle = SKIN; ctx.fillRect(s * ex + lx - er, eyeY - er * 1.3, er * 2, er * (mood === 'sleepy' ? 1.3 : 1.0)); ctx.restore();
        line(ctx, [[s * ex + lx - er, eyeY - er * (mood === 'sleepy' ? 0 : 0.25)], [s * ex + lx + er, eyeY - er * (mood === 'sleepy' ? 0 : 0.25)]], 5);
      }
    }
  }
  // brows
  const by = eyeY - R * 0.3;
  const bt = { angry: 0.45, evil: 0.5, determined: 0.3, sad: -0.4, scared: -0.35, worried: -0.35, shock: -0.1, o: -0.1, smug: 0.15 }[mood] || 0;
  if (mood !== 'dizzy') for (const s of [-1, 1]) {
    const x0 = s * ex + lx - R * 0.15, x1 = s * ex + lx + R * 0.15;
    const yIn = by + bt * R * 0.18 * 1, yOut = by - bt * R * 0.18;
    const inner = s < 0 ? x1 : x0, outer = s < 0 ? x0 : x1;
    line(ctx, [[outer, yOut - (big(mood) ? R * 0.08 : 0)], [inner, yIn - (big(mood) ? R * 0.08 : 0)]], R * 0.09);
  }
  // mouth
  const my = R * 0.42, mx = lx * 0.6;
  ctx.lineWidth = R * 0.08; ctx.strokeStyle = INK; ctx.lineCap = 'round';
  if (mood === 'smile' || mood === 'happy') { ctx.beginPath(); ctx.arc(mx, my - R * 0.12, R * 0.26, 0.2, Math.PI - 0.2); ctx.stroke(); }
  else if (mood === 'grin' || mood === 'evil') {
    ctx.beginPath(); ctx.moveTo(mx - R * 0.3, my - R * 0.06); ctx.quadraticCurveTo(mx, my + R * 0.32, mx + R * 0.3, my - R * 0.06); ctx.closePath(); fs(ctx, '#fff', R * 0.07);
  }
  else if (mood === 'smug') { ctx.beginPath(); ctx.moveTo(mx - R * 0.22, my); ctx.quadraticCurveTo(mx + R * 0.05, my + R * 0.12, mx + R * 0.28, my - R * 0.1); ctx.stroke(); }
  else if (mood === 'o' || mood === 'shock' || mood === 'scared' || mood === 'yell') {
    const open = (f.talk ?? 1) * (mood === 'yell' ? 1.3 : 1);
    ell(ctx, mx, my, R * 0.14 * (mood === 'yell' ? 1.6 : 1), R * 0.17 * open); fs(ctx, '#5a1f2c', R * 0.07);
  }
  else if (mood === 'sad' || mood === 'worried' || mood === 'angry') { ctx.beginPath(); ctx.arc(mx, my + R * 0.18, R * 0.22, Math.PI + 0.35, -0.35); ctx.stroke(); }
  else if (mood === 'chew') { const o = Math.abs(Math.sin((f.t || 0) * 14)); ell(ctx, mx, my, R * 0.16, R * 0.05 + o * R * 0.1); fs(ctx, '#5a1f2c', R * 0.06); }
  else if (mood === 'sleepy' || mood === 'dizzy') { ctx.beginPath(); ctx.arc(mx, my - R * 0.05, R * 0.14, 0.3, Math.PI - 0.3); ctx.stroke(); }
  else { line(ctx, [[mx - R * 0.18, my], [mx + R * 0.18, my]], R * 0.08); }
  function big(m) { return m === 'scared' || m === 'shock' || m === 'o'; }
}

// headwear and hair drawn around the head (radius R, centred at 0,0)
function headgear(ctx, R, o, under) {
  const g = o.gear || {};
  if (under) {                                  // behind the head: long hair
    if (g.hair) { ctx.beginPath(); ctx.moveTo(-R * 1.0, -R * 0.2); ctx.quadraticCurveTo(-R * 1.25, R * 1.4, -R * 0.6, R * 1.9); ctx.lineTo(R * 0.6, R * 1.9);
      ctx.quadraticCurveTo(R * 1.25, R * 1.4, R * 1.0, -R * 0.2); ctx.closePath(); fs(ctx, g.hair, 8); }
    if (g.cloak) { ctx.beginPath(); ctx.arc(0, 0, R * 1.22, Math.PI * 0.95, Math.PI * 2.05); ctx.lineTo(R * 1.2, R * 0.9); ctx.lineTo(-R * 1.2, R * 0.9); ctx.closePath(); fs(ctx, ACC.cloak, 8); }
    return;
  }
  if (g.beard) { ctx.beginPath(); ctx.moveTo(-R * 0.93, R * 0.1); ctx.quadraticCurveTo(-R * 0.75, R * 1.25, 0, R * 1.3); ctx.quadraticCurveTo(R * 0.75, R * 1.25, R * 0.93, R * 0.1);
    ctx.quadraticCurveTo(R * 0.55, R * 0.62, 0, R * 0.62); ctx.quadraticCurveTo(-R * 0.55, R * 0.62, -R * 0.93, R * 0.1); ctx.closePath(); fs(ctx, g.beardCol || ACC.beard, 7);
    if (g.longBeard) { ctx.beginPath(); ctx.moveTo(-R * 0.6, R * 0.9); ctx.quadraticCurveTo(0, R * (1.3 + g.longBeard * 1.6), R * 0.6, R * 0.9); ctx.closePath(); fs(ctx, g.beardCol || ACC.beard, 7); }
  }
  if (g.helmet) {
    // bronze dome, cheek guards, tall red crest
    ctx.beginPath(); ctx.arc(0, 0, R * 1.06, Math.PI * 1.02, Math.PI * 1.98); ctx.lineTo(R * 1.04, R * 0.05); ctx.lineTo(R * 0.72, R * 0.1);
    ctx.lineTo(R * 0.62, -R * 0.3); ctx.lineTo(-R * 0.62, -R * 0.3); ctx.lineTo(-R * 0.72, R * 0.1); ctx.lineTo(-R * 1.04, R * 0.05); ctx.closePath(); fs(ctx, ACC.bronze, 8);
    line(ctx, [[-R * 0.95, -R * 0.32], [R * 0.95, -R * 0.32]], 6, ACC.bronzeD);
    ctx.beginPath(); ctx.moveTo(-R * 0.95, -R * 0.7); ctx.quadraticCurveTo(-R * 0.6, -R * 1.85, R * 0.2, -R * 1.75); ctx.quadraticCurveTo(R * 1.05, -R * 1.55, R * 1.05, -R * 0.75);
    ctx.quadraticCurveTo(0, -R * 1.25, -R * 0.95, -R * 0.7); fs(ctx, ACC.crest, 8);
    for (let i = 0; i < 7; i++) { const a = -2.6 + i * 0.32; line(ctx, [[Math.cos(a) * R * 1.2, -R * 0.3 + Math.sin(a) * R * 1.15], [Math.cos(a) * R * 1.45, -R * 0.3 + Math.sin(a) * R * 1.4]], 4, '#a92a28'); }
  }
  if (g.cap) { ctx.beginPath(); ctx.arc(0, 0, R * 1.04, Math.PI * 1.05, Math.PI * 1.95); ctx.closePath(); fs(ctx, g.cap, 7); }
  if (g.laurel) { for (const s of [-1, 1]) for (let i = 0; i < 5; i++) { const a = -Math.PI / 2 + s * (0.35 + i * 0.28); ell(ctx, Math.cos(a) * R * 1.02, Math.sin(a) * R * 1.02, R * 0.16, R * 0.08, a + s * 0.9); fs(ctx, ACC.laurel, 4); } }
  if (g.crown) { poly(ctx, [[-R * 0.6, -R * 0.75], [-R * 0.6, -R * 1.25], [-R * 0.3, -R * 1.0], [0, -R * 1.35], [R * 0.3, -R * 1.0], [R * 0.6, -R * 1.25], [R * 0.6, -R * 0.75]]); fs(ctx, ACC.gold, 7); }
  if (g.flowers) { for (let i = 0; i < 6; i++) { const a = -Math.PI * 0.9 + i * 0.36; circ(ctx, Math.cos(a) * R * 1.0, Math.sin(a) * R * 1.0, R * 0.14); fs(ctx, ['#ff6fa8', '#ffd23f', '#ffffff'][i % 3], 4); } }
  if (g.bun) { circ(ctx, 0, -R * 1.12, R * 0.38); fs(ctx, g.bun, 7); ctx.beginPath(); ctx.arc(0, 0, R * 1.03, Math.PI * 1.1, Math.PI * 1.9); ctx.closePath(); fs(ctx, g.bun, 7); }
  if (g.hairTop) { ctx.beginPath(); ctx.arc(0, 0, R * 1.04, Math.PI * 1.0, Math.PI * 2.0); ctx.quadraticCurveTo(R * 0.4, -R * 0.35, 0, -R * 0.45); ctx.quadraticCurveTo(-R * 0.4, -R * 0.35, -R * 1.04, 0); ctx.closePath(); fs(ctx, g.hairTop, 7); }
  if (g.hood) { ctx.beginPath(); ctx.arc(0, 0, R * 1.22, Math.PI * 0.92, Math.PI * 2.08); ctx.quadraticCurveTo(R * 1.05, -R * 0.2, R * 0.95, 0); ctx.arc(0, 0, R * 0.95, 0, Math.PI, true);
    ctx.quadraticCurveTo(-R * 1.05, -R * 0.2, -R * 1.22 * Math.cos(Math.PI * 0.08), R * 1.22 * Math.sin(Math.PI * 0.08)); fs(ctx, ACC.cloak, 8); }
}

// a prop in a hand at (x,y) pointing along angle a (screen radians, 0 = right)
function prop(ctx, kind, x, y, a, s, t) {
  withT(ctx, x, y, a, s, () => {
    if (kind === 'sword') { rrect(ctx, -10, -9, 30, 18, 4); fs(ctx, ACC.bronzeD, 5); poly(ctx, [[20, -10], [150, -6], [175, 0], [150, 6], [20, 10]]); fs(ctx, '#dfe6ee', 6); line(ctx, [[18, -24], [18, 24]], 10, ACC.bronze); }
    else if (kind === 'stake') { rrect(ctx, -40, -10, 230, 20, 8); fs(ctx, '#9a6a3c', 6); for (let i = 0; i < 4; i++) { const fl = Math.sin(t * 30 + i) * 8; ctx.beginPath(); ctx.moveTo(185, -12 + i * 6); ctx.quadraticCurveTo(230 + fl, -40 + i * 12, 250 + fl, -10 + i * 6); ctx.quadraticCurveTo(225, 10, 185, 6); fs(ctx, i % 2 ? '#ffb02e' : '#ff5a2e', 4); } }
    else if (kind === 'wand') { line(ctx, [[0, 0], [150, 0]], 12, '#5b3a22'); circ(ctx, 158, 0, 16); fs(ctx, '#c9a6ff', 5); }
    else if (kind === 'goblet') { poly(ctx, [[-30, -60], [30, -60], [14, -10], [-14, -10]]); fs(ctx, ACC.gold, 6); line(ctx, [[0, -10], [0, 20]], 10, ACC.gold); line(ctx, [[-20, 22], [20, 22]], 10, ACC.gold); }
    else if (kind === 'lotus') { for (let i = 0; i < 7; i++) { const aa = -Math.PI / 2 + (i - 3) * 0.38; ell(ctx, Math.cos(aa) * 26, -20 + Math.sin(aa) * 26, 14, 30, aa + Math.PI / 2); fs(ctx, i % 2 ? '#ff8fc8' : '#ffc1e3', 4); } circ(ctx, 0, -18, 12); fs(ctx, '#ffe14d', 4); }
    else if (kind === 'fork') { line(ctx, [[0, 0], [150, 0]], 10, '#bfc7cf'); for (const dy of [-14, 0, 14]) line(ctx, [[150, dy], [190, dy]], 7, '#bfc7cf'); line(ctx, [[150, -14], [150, 14]], 7, '#bfc7cf'); }
    else if (kind === 'bow') { ctx.beginPath(); ctx.arc(-40, 0, 170, -1.05, 1.05); ctx.lineWidth = 18; ctx.strokeStyle = INK; ctx.stroke(); ctx.lineWidth = 10; ctx.strokeStyle = '#a0682f'; ctx.stroke();
      const sx = -40 + Math.cos(1.05) * 170, sy = Math.sin(1.05) * 170, pull = (t || 0) * 120;
      line(ctx, [[sx, -sy], [-40 + 80 - pull, 0], [sx, sy]], 4, '#f4f0e6'); }
    else if (kind === 'boulder') { ctx.beginPath(); for (let i = 0; i < 10; i++) { const aa = i / 10 * Math.PI * 2, r = 70 + hash(i * 3) * 20; i ? ctx.lineTo(Math.cos(aa) * r, Math.sin(aa) * r) : ctx.moveTo(Math.cos(aa) * r, Math.sin(aa) * r); } ctx.closePath(); fs(ctx, '#9b958c', 8); }
  });
}

// the stick rig. o: {x, y (feet), s, mood, look, lean, arms:[[sh,el],[sh,el]] (left, right), legs:[[hip,knee],[hip,knee]],
// gear:{...}, props:{l:'sword', r:'...'}, dress: colour, blink, t, sit}
function stick(ctx, o) {
  const s = o.s || 1, x = o.x, y = o.y, t = o.t || 0;
  const lw = 14 * s, R = 64 * s;
  const lean = o.lean || 0;
  const legs = o.legs || [[-0.18, 0.05], [0.18, -0.05]];
  const hipY = y - 182 * s;
  const hip = [x, hipY];
  const neck = [x + Math.sin(lean) * 150 * s, hipY - Math.cos(lean) * 150 * s];
  if (o.shadow !== false) shadow(ctx, x, y + 6, 80 * s);
  // legs
  const legPts = legs.map(([a, k]) => { const kn = polar(hip[0], hip[1], a, 92 * s); const ft = polar(kn[0], kn[1], a + k, 92 * s); return [hip, kn, ft]; });
  if (o.dress) {
    poly(ctx, [[neck[0] - 30 * s, neck[1] + 40 * s], [neck[0] + 30 * s, neck[1] + 40 * s], [x + 95 * s, y - 40 * s], [x - 95 * s, y - 40 * s]]); fs(ctx, o.dress, 9 * s);
    for (const p of legPts) line(ctx, [[p[2][0], y - 40 * s], p[2]], lw);
  } else for (const p of legPts) line(ctx, p, lw);
  // torso
  line(ctx, [hip, neck], lw);
  if (o.cloakBody) { poly(ctx, [[neck[0], neck[1] - 10 * s], [x + 85 * s, y - 30 * s], [x - 85 * s, y - 30 * s]]); fs(ctx, ACC.cloak, 9 * s); }
  if (o.tunic) { poly(ctx, [[neck[0] - 26 * s, neck[1] + 20 * s], [neck[0] + 26 * s, neck[1] + 20 * s], [hip[0] + 40 * s, hip[1] + 30 * s], [hip[0] - 40 * s, hip[1] + 30 * s]]); fs(ctx, o.tunic, 8 * s); }
  // arms
  const sh = [neck[0] + Math.sin(lean) * -20 * s, neck[1] + 28 * s];
  const arms = o.arms || [[-0.35, -0.2], [0.35, 0.2]];
  const hands = arms.map(([a, e]) => { const el = polar(sh[0], sh[1], a, 78 * s); const hd = polar(el[0], el[1], a + e, 78 * s); line(ctx, [sh, el, hd], lw); return [hd, a + e]; });
  // props in hands: angle along the forearm
  const P = o.props || {};
  ['l', 'r'].forEach((k, i) => { if (P[k]) { const [hd, a] = hands[i]; prop(ctx, P[k], hd[0], hd[1], Math.PI / 2 - a + (P[k + 'Rot'] || 0), s, P[k + 'T'] ?? t); } });
  for (const [hd] of hands) { circ(ctx, hd[0], hd[1], 11 * s); fs(ctx, '#fff', 6 * s); }
  // head
  const hc = [neck[0] + Math.sin(lean) * R * 0.9, neck[1] - R * 0.92];
  withT(ctx, hc[0], hc[1], (o.headTilt || 0) + lean * 0.5, 1, () => {
    headgear(ctx, R, o, true);
    circ(ctx, 0, 0, R); fs(ctx, SKIN, 9 * s);
    face(ctx, R, { mood: o.mood, look: o.look, lookY: o.lookY, blink: o.blink, t, talk: o.talk });
    headgear(ctx, R, o, false);
  });
  return { head: hc, hands: hands.map(h => h[0]), R };
}

// ---- creatures ----
function cyclopsEye(ctx, x, y, r, t, o = {}) {        // a giant one-eyed face, close up
  circ(ctx, x, y, r); fs(ctx, '#b7c79a', 14);
  const open = o.blink ? 0.08 : (o.open ?? 1);
  ell(ctx, x, y - r * 0.05, r * 0.42, r * 0.34 * open); fs(ctx, '#fff', 12);
  if (open > 0.2) { circ(ctx, x + (o.look || 0) * r * 0.12, y - r * 0.05, r * 0.16); fs(ctx, '#d4402e', 8); circ(ctx, x + (o.look || 0) * r * 0.12, y - r * 0.05, r * 0.08); ctx.fillStyle = INK; ctx.fill(); }
  line(ctx, [[x - r * 0.5, y - r * 0.5 + (o.angry ? r * 0.1 : 0)], [x + r * 0.5, y - r * 0.5 - (o.angry ? 0 : r * 0.05)]], r * 0.07);
  if (o.mouth) { ctx.beginPath(); ctx.moveTo(x - r * 0.4, y + r * 0.45); ctx.quadraticCurveTo(x, y + r * (0.45 + o.mouth * 0.35), x + r * 0.4, y + r * 0.45); ctx.closePath(); fs(ctx, '#5a1f2c', 10);
    for (let i = 0; i < 5; i++) { const tx = x - r * 0.3 + i * r * 0.15; poly(ctx, [[tx - r * 0.05, y + r * 0.46], [tx + r * 0.05, y + r * 0.46], [tx, y + r * 0.56]]); fs(ctx, '#fff', 4); } }
}
function ghost(ctx, x, y, s, t, seed = 0) {
  ctx.save(); ctx.globalAlpha = 0.85;
  const wob = Math.sin(t * 4 + seed) * 10 * s;
  ctx.beginPath(); ctx.moveTo(x - 60 * s, y); ctx.arc(x, y - 10 * s, 60 * s, Math.PI, 0);
  ctx.lineTo(x + 60 * s, y + 80 * s);
  for (let i = 0; i < 4; i++) ctx.quadraticCurveTo(x + (45 - i * 30) * s + wob, y + (110 - (i % 2) * 40) * s, x + (30 - i * 30) * s, y + 80 * s);
  ctx.closePath(); fs(ctx, '#eef4ff', 7 * s);
  for (const dx of [-20, 20]) { ell(ctx, x + dx * s, y - 10 * s, 9 * s, 14 * s); ctx.fillStyle = INK; ctx.fill(); }
  ell(ctx, x, y + 25 * s, 12 * s, 16 * s); ctx.fillStyle = INK; ctx.fill();
  ctx.restore();
}
function pig(ctx, x, y, s, t, o = {}) {
  shadow(ctx, x, y + 4, 90 * s);
  const b = Math.abs(Math.sin(t * 9 + (o.seed || 0))) * 8 * s;
  for (const dx of [-50, -20, 25, 55]) line(ctx, [[x + dx * s, y - 40 * s - b], [x + dx * s, y]], 14 * s, INK);
  ell(ctx, x, y - 75 * s - b, 95 * s, 60 * s); fs(ctx, '#ff9ec4', 9 * s);
  const hx = x + 85 * s, hy = y - 100 * s - b;
  circ(ctx, hx, hy, 48 * s); fs(ctx, '#ff9ec4', 9 * s);
  ell(ctx, hx + 38 * s, hy + 8 * s, 18 * s, 14 * s); fs(ctx, '#ff7fb0', 6 * s);
  for (const dy of [-4, 4]) { circ(ctx, hx + 38 * s, hy + 8 * s + dy * s, 3 * s); ctx.fillStyle = INK; ctx.fill(); }
  circ(ctx, hx + 10 * s, hy - 12 * s, 7 * s); ctx.fillStyle = INK; ctx.fill();
  poly(ctx, [[hx - 25 * s, hy - 38 * s], [hx - 10 * s, hy - 70 * s], [hx + 5 * s, hy - 40 * s]]); fs(ctx, '#ff9ec4', 6 * s);
  ctx.beginPath(); ctx.arc(x - 100 * s, y - 85 * s - b, 14 * s, 0, Math.PI * 1.6); ctx.lineWidth = 6 * s; ctx.strokeStyle = INK; ctx.stroke();
  if (o.helmet) withT(ctx, hx - 5 * s, hy - 10 * s, -0.2, 0.62 * s, () => headgear(ctx, 64, { gear: { helmet: true } }, false));
}
function cow(ctx, x, y, s, t, o = {}) {
  shadow(ctx, x, y + 4, 120 * s);
  for (const dx of [-70, -35, 40, 75]) line(ctx, [[x + dx * s, y - 60 * s], [x + dx * s, y]], 16 * s);
  ell(ctx, x, y - 110 * s, 125 * s, 75 * s); fs(ctx, '#ffffff', 10 * s);
  for (const [dx, dy, r] of [[-50, -20, 30], [20, 15, 24], [60, -30, 20]]) { ell(ctx, x + dx * s, y - 110 * s + dy * s, r * s, r * 0.8 * s); ctx.fillStyle = INK; ctx.fill(); }
  const hx = x + 125 * s, hy = y - 150 * s;
  ell(ctx, hx, hy, 55 * s, 48 * s); fs(ctx, '#ffffff', 9 * s);
  ell(ctx, hx + 30 * s, hy + 25 * s, 34 * s, 22 * s); fs(ctx, '#ffb3c6', 7 * s);
  for (const dx of [-15, 15]) { ctx.beginPath(); ctx.moveTo(hx + dx * s, hy - 40 * s); ctx.quadraticCurveTo(hx + dx * 3 * s, hy - 80 * s, hx + dx * 2.2 * s, hy - 95 * s); ctx.lineWidth = 12 * s; ctx.strokeStyle = INK; ctx.stroke(); }
  const scared = o.scared ? 1.3 : 1;
  for (const dx of [-14, 16]) { circ(ctx, hx + dx * s, hy - 8 * s, 10 * scared * s); fs(ctx, '#fff', 4 * s); circ(ctx, hx + dx * s + 2 * s, hy - 8 * s, 5 * s); ctx.fillStyle = INK; ctx.fill(); }
  if (o.halo) { ell(ctx, hx, hy - 105 * s, 55 * s, 14 * s); ctx.lineWidth = 12 * s; ctx.strokeStyle = ACC.gold; ctx.stroke(); }
  if (o.sweat) { ell(ctx, hx - 50 * s, hy - 30 * s, 9 * s, 14 * s); fs(ctx, '#8fd3ff', 4 * s); }
}
function siren(ctx, x, y, s, t, seed = 0) {
  const r = stick(ctx, { x, y, s, mood: 'smile', look: -0.4, t, dress: '#3ec7c0', gear: { hair: ['#ffd23f', '#ff7a59', '#b46bff'][seed % 3] },
    arms: [[-1.9 + Math.sin(t * 3 + seed) * 0.2, -0.3], [1.9 - Math.sin(t * 3 + seed) * 0.2, 0.3]], headTilt: Math.sin(t * 2 + seed) * 0.1, shadow: false });
  // music notes drifting out
  for (let i = 0; i < 3; i++) {
    const u = ((t * 0.7 + i / 3 + seed * 0.13) % 1);
    const nx = r.head[0] - 60 * s - u * 260 * s, ny = r.head[1] - 40 * s - u * 120 * s + Math.sin(u * 9) * 20 * s;
    ctx.save(); ctx.globalAlpha = 1 - u;
    ell(ctx, nx, ny, 16 * s, 12 * s, -0.4); ctx.fillStyle = INK; ctx.fill(); line(ctx, [[nx + 14 * s, ny], [nx + 14 * s, ny - 50 * s], [nx + 34 * s, ny - 40 * s]], 6 * s);
    ctx.restore();
  }
}
