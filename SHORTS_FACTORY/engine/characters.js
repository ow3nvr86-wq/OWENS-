// Parametric 2D characters (original designs): a big white egg head (~40 % of the height), thick black outlines,
// a tiny flat-colour costume torso with a few details, thin black stick limbs with small round hands, dot eyes,
// thick eyebrows that carry the emotion, a small mouth, optional moustache/beard/hair, and an era hat.
// Every part is its own layer, so poses, brows, blinks and mouth shapes are animated in code.
// Units: the character stands on (0,0) and is ~420 px tall at scale 1 (1080-wide frame).
const OL = 7;                                   // outline width (px at scale 1)
const C = { ink: '#121014', skin: '#ffffff' };

// ---------------- costume library ----------------
const COSTUMES = {
  armor_red:  { body: '#b8322c', trim: '#e8c14a', belt: '#3b2a20', detail: 'lamellar', legs: '#2b2b33' },
  armor_blue: { body: '#2f5d9e', trim: '#d9d2c0', belt: '#3b2a20', detail: 'lamellar', legs: '#2b2b33' },
  coat_green: { body: '#3f7d4f', trim: '#e9dfc4', belt: '#2b2018', detail: 'buttons', legs: '#2b2b33' },
  ashigaru:   { body: '#2b2d38', trim: '#a8322c', belt: '#7a5a34', detail: 'plates', legs: '#2b2b33' },
  samurai:    { body: '#5a2430', trim: '#d8b04a', belt: '#1e1a1a', detail: 'plates', legs: '#1f1f24' },
  peasant:    { body: '#c9b28a', trim: '#8c7350', belt: '#6a4c2c', detail: 'patch', legs: '#3a3026' },
  overalls:   { body: '#3d6fb0', trim: '#f0c040', belt: '#3d6fb0', detail: 'rivets', legs: '#3d6fb0' },
  vest:       { body: '#7a4b2a', trim: '#e9dfc4', belt: '#2b2018', detail: 'buttons', legs: '#2b2b33' },
  tunic:      { body: '#6a4fa3', trim: '#e8c14a', belt: '#2b2018', detail: 'belt', legs: '#2b2b33' },
};
// ---------------- hat library (drawn around a head of radius R, centre 0,0) ----------------
const HATS = {
  plume_helmet(g, R, a) {          // a general's helmet: domed, brim, a tall red plume
    g.beginPath(); g.moveTo(-R * 0.95, -R * 0.35); g.quadraticCurveTo(-R, -R * 1.25, 0, -R * 1.3); g.quadraticCurveTo(R, -R * 1.25, R * 0.95, -R * 0.35); g.closePath(); fo(g, '#3a3a44');
    g.beginPath(); g.ellipse(0, -R * 0.38, R * 1.25, R * 0.18, 0, 0, 7); fo(g, '#2a2a32');
    g.beginPath(); g.ellipse(0, -R * 1.33, R * 0.12, R * 0.12, 0, 0, 7); fo(g, '#e8c14a');
    const sw = Math.sin(a.t * 3) * 0.12 + (a.sway || 0);
    g.save(); g.translate(0, -R * 1.4); g.rotate(sw);
    g.beginPath(); g.moveTo(-R * 0.08, 0); g.quadraticCurveTo(-R * 0.4, -R * 0.7, R * 0.05, -R * 1.05); g.quadraticCurveTo(R * 0.3, -R * 0.5, R * 0.1, 0); g.closePath(); fo(g, '#d8302a');
    g.restore();
  },
  joseon_helmet(g, R) {            // a soldier's rounded iron helmet with a small spike and a red tassel
    g.beginPath(); g.moveTo(-R * 0.97, -R * 0.3); g.quadraticCurveTo(-R * 0.95, -R * 1.2, 0, -R * 1.22); g.quadraticCurveTo(R * 0.95, -R * 1.2, R * 0.97, -R * 0.3); g.closePath(); fo(g, '#4a4f5c');
    g.beginPath(); g.ellipse(0, -R * 0.32, R * 1.12, R * 0.14, 0, 0, 7); fo(g, '#353a45');
    g.beginPath(); g.moveTo(-R * 0.08, -R * 1.2); g.lineTo(0, -R * 1.55); g.lineTo(R * 0.08, -R * 1.2); g.closePath(); fo(g, '#e8c14a');
    g.beginPath(); g.moveTo(0, -R * 1.45); g.quadraticCurveTo(R * 0.25, -R * 1.25, R * 0.18, -R * 1.0); g.lineWidth = R * 0.12; g.strokeStyle = '#d8302a'; g.stroke();
  },
  gat(g, R) {                      // a wide-brimmed black hat
    g.beginPath(); g.ellipse(0, -R * 0.62, R * 1.7, R * 0.22, 0, 0, 7); g.fillStyle = 'rgba(20,18,22,0.85)'; g.fill(); g.lineWidth = OL * 0.7; g.strokeStyle = C.ink; g.stroke();
    g.beginPath(); g.moveTo(-R * 0.5, -R * 0.66); g.lineTo(-R * 0.45, -R * 1.45); g.quadraticCurveTo(0, -R * 1.55, R * 0.45, -R * 1.45); g.lineTo(R * 0.5, -R * 0.66); g.closePath(); fo(g, '#1d1b20');
  },
  jingasa(g, R) {                  // a flat conical foot-soldier hat
    g.beginPath(); g.moveTo(-R * 1.45, -R * 0.45); g.quadraticCurveTo(0, -R * 1.45, R * 1.45, -R * 0.45); g.quadraticCurveTo(0, -R * 0.62, -R * 1.45, -R * 0.45); g.closePath(); fo(g, '#2a2c35');
    g.beginPath(); g.arc(0, -R * 0.98, R * 0.12, 0, 7); fo(g, '#a8322c');
  },
  kabuto(g, R) {                   // an original crested helmet: bowl, neck flaps, a gold crescent crest
    g.beginPath(); g.moveTo(-R * 1.0, -R * 0.25); g.quadraticCurveTo(-R * 1.0, -R * 1.25, 0, -R * 1.27); g.quadraticCurveTo(R * 1.0, -R * 1.25, R * 1.0, -R * 0.25); g.closePath(); fo(g, '#2b2b33');
    for (const s of [-1, 1]) { g.beginPath(); g.moveTo(s * R * 0.9, -R * 0.45); g.lineTo(s * R * 1.35, -R * 0.1); g.lineTo(s * R * 1.25, R * 0.12); g.lineTo(s * R * 0.92, -R * 0.1); g.closePath(); fo(g, '#5a2430'); }
    g.beginPath(); g.moveTo(-R * 0.75, -R * 1.65); g.quadraticCurveTo(0, -R * 0.95, R * 0.75, -R * 1.65); g.quadraticCurveTo(0, -R * 1.15, -R * 0.75, -R * 1.65); g.closePath(); fo(g, '#e2b84a');
  },
  top_hat(g, R) { g.beginPath(); g.ellipse(0, -R * 0.6, R * 1.2, R * 0.16, 0, 0, 7); fo(g, '#1d1b20'); g.beginPath(); g.rect(-R * 0.62, -R * 1.75, R * 1.24, R * 1.12); fo(g, '#1d1b20'); g.beginPath(); g.rect(-R * 0.62, -R * 0.92, R * 1.24, R * 0.18); fo(g, '#a8322c'); },
  flat_cap(g, R) { g.beginPath(); g.moveTo(-R * 1.0, -R * 0.4); g.quadraticCurveTo(-R * 0.9, -R * 1.2, R * 0.2, -R * 1.18); g.quadraticCurveTo(R * 1.1, -R * 1.0, R * 1.5, -R * 0.45); g.quadraticCurveTo(R * 0.4, -R * 0.55, -R * 1.0, -R * 0.4); g.closePath(); fo(g, '#6b5a48'); },
  none() {},
};
function fo(g, fill, w = OL) { g.fillStyle = fill; g.fill(); g.lineWidth = w; g.strokeStyle = C.ink; g.lineJoin = 'round'; g.lineCap = 'round'; g.stroke(); }

// ---------------- eyebrows: the main emotion driver ----------------
// each mood: [inner y, outer y] offsets (in head radii, + = down) and thickness
const BROWS = {
  neutral: [0, 0], happy: [-0.04, 0.02], smug: [0.06, -0.08], angry: [0.16, -0.1], determined: [0.1, -0.04],
  worried: [-0.12, 0.08], shocked: [-0.16, -0.12], sad: [-0.1, 0.12], scared: [-0.14, 0.06],
};
const MOUTH_FOR = { neutral: 'line', happy: 'smile', smug: 'smirk', angry: 'frown', determined: 'line', worried: 'wobble', shocked: 'o', sad: 'frown', scared: 'o' };

function drawFace(g, R, s) {
  const look = s.look || 0, eyY = -R * 0.02;
  // eyes: small black ovals (or blink lines)
  for (const k of [-1, 1]) {
    const ex = k * R * 0.32 + look * R * 0.12;
    if (s.blink) { g.beginPath(); g.moveTo(ex - R * 0.08, eyY); g.lineTo(ex + R * 0.08, eyY); g.lineWidth = R * 0.07; g.strokeStyle = C.ink; g.lineCap = 'round'; g.stroke(); }
    else { g.beginPath(); g.ellipse(ex, eyY, R * 0.075, R * (s.mood === 'shocked' || s.mood === 'scared' ? 0.12 : 0.1), 0, 0, 7); g.fillStyle = C.ink; g.fill(); }
  }
  // brows
  const [bi, bo] = BROWS[s.mood] || BROWS.neutral;
  for (const k of [-1, 1]) {
    const cx = k * R * 0.32 + look * R * 0.12, by = -R * 0.3;
    g.beginPath(); g.moveTo(cx - k * R * 0.16, by + bi * R); g.lineTo(cx + k * R * 0.18, by + bo * R);
    g.lineWidth = R * 0.13; g.strokeStyle = C.ink; g.lineCap = 'round'; g.stroke();
  }
  // mouth: talking overrides with 3 shapes from voice amplitude
  const mx = look * R * 0.08, my = R * 0.38;
  let shape = MOUTH_FOR[s.mood] || 'line';
  if (s.talk != null) shape = s.talk > 0.55 ? 'open' : s.talk > 0.18 ? 'mid' : shape;
  g.lineWidth = R * 0.07; g.strokeStyle = C.ink; g.lineCap = 'round';
  if (shape === 'smile') { g.beginPath(); g.arc(mx, my - R * 0.12, R * 0.2, 0.35, Math.PI - 0.35); g.stroke(); }
  else if (shape === 'smirk') { g.beginPath(); g.moveTo(mx - R * 0.16, my); g.quadraticCurveTo(mx + R * 0.05, my + R * 0.08, mx + R * 0.2, my - R * 0.08); g.stroke(); }
  else if (shape === 'frown') { g.beginPath(); g.arc(mx, my + R * 0.16, R * 0.17, Math.PI + 0.45, -0.45); g.stroke(); }
  else if (shape === 'wobble') { g.beginPath(); g.moveTo(mx - R * 0.16, my); for (let i = 1; i <= 4; i++) g.lineTo(mx - R * 0.16 + i * R * 0.08, my + (i % 2 ? -1 : 1) * R * 0.04); g.stroke(); }
  else if (shape === 'o' || shape === 'open') { g.beginPath(); g.ellipse(mx, my, R * 0.1, R * (shape === 'open' ? 0.13 : 0.11), 0, 0, 7); fo(g, '#4a1a24', R * 0.06); }
  else if (shape === 'mid') { g.beginPath(); g.ellipse(mx, my, R * 0.12, R * 0.055, 0, 0, 7); fo(g, '#4a1a24', R * 0.06); }
  else { g.beginPath(); g.moveTo(mx - R * 0.14, my); g.lineTo(mx + R * 0.14, my); g.stroke(); }
}

function facialHair(g, R, kind) {
  if (!kind) return;
  if (kind.includes('moustache')) { g.beginPath(); g.moveTo(-R * 0.32, R * 0.28); g.quadraticCurveTo(-R * 0.15, R * 0.12, 0, R * 0.24); g.quadraticCurveTo(R * 0.15, R * 0.12, R * 0.32, R * 0.28); g.quadraticCurveTo(0, R * 0.34, -R * 0.32, R * 0.28); fo(g, '#2a2420', R * 0.05); }
  if (kind.includes('goatee')) { g.beginPath(); g.moveTo(-R * 0.1, R * 0.55); g.lineTo(0, R * 0.95); g.lineTo(R * 0.1, R * 0.55); g.closePath(); fo(g, '#2a2420', R * 0.05); }
  if (kind.includes('beard')) { g.beginPath(); g.moveTo(-R * 0.75, R * 0.3); g.quadraticCurveTo(-R * 0.6, R * 1.15, 0, R * 1.15); g.quadraticCurveTo(R * 0.6, R * 1.15, R * 0.75, R * 0.3); g.quadraticCurveTo(0, R * 0.62, -R * 0.75, R * 0.3); fo(g, '#2a2420', R * 0.05); }
}

// pose: limb angles (radians, 0 = straight down, + = toward the character's front/right) and a walk phase
const POSES = {
  idle: (t) => ({ armL: -0.15 + Math.sin(t * 1.6) * 0.05, armR: 0.15 - Math.sin(t * 1.6) * 0.05, elL: 0.1, elR: -0.1 }),
  point: () => ({ armL: -0.15, armR: 1.65, elL: 0.1, elR: 0 }),
  present: () => ({ armL: -0.2, armR: 1.25, elL: 0.1, elR: -0.5 }),
  cheer: (t) => ({ armL: -2.7 + Math.sin(t * 12) * 0.15, armR: 2.7 - Math.sin(t * 12) * 0.15, elL: -0.2, elR: 0.2 }),
  crossed: () => ({ armL: 0.9, armR: -0.9, elL: 1.7, elR: -1.7 }),
  shrug: () => ({ armL: -1.1, armR: 1.1, elL: 1.4, elR: -1.4 }),
  flail: (t) => ({ armL: -2.2 + Math.sin(t * 18) * 0.5, armR: 2.2 + Math.cos(t * 17) * 0.5, elL: 0.3, elR: -0.3 }),
  torch: (t) => ({ armL: -0.15, armR: 1.2 + Math.sin(t * 2) * 0.05, elL: 0.1, elR: -0.9 }),
  march: (t, ph) => ({ armL: Math.sin(ph) * 0.45, armR: -Math.sin(ph) * 0.45, elL: 0.2, elR: -0.2 }),
  run: (t, ph) => ({ armL: Math.sin(ph) * 0.9, armR: -Math.sin(ph) * 0.9, elL: 0.9, elR: -0.9 }),
  talk: (t) => ({ armL: -0.15, armR: 0.5 + Math.sin(t * 5) * 0.25, elL: 0.1, elR: -0.6 }),
};

// draw one character. st: {x, y, scale, flip, t, mood, blink, talk, look, action, phase, lean, prop}
function drawCharacter(g, def, st) {
  const cos = COSTUMES[def.costume] || COSTUMES.tunic;
  const s = st.scale || 1, t = st.t || 0;
  const moving = st.action === 'march' || st.action === 'run' || st.action === 'walk';
  const ph = st.phase || 0;
  const bob = moving ? -Math.abs(Math.sin(ph)) * 10 : Math.sin(t * 2.4 + (def.seed || 0)) * 3;
  g.save(); g.translate(st.x, st.y); g.scale((st.flip ? -1 : 1) * s, s);
  // soft drop shadow (sits the character in the 3D scene)
  const sh = g.createRadialGradient(0, 0, 4, 0, 0, 95); sh.addColorStop(0, 'rgba(10,8,12,0.42)'); sh.addColorStop(1, 'rgba(10,8,12,0)');
  g.save(); g.scale(1, 0.22); g.fillStyle = sh; g.beginPath(); g.arc(0, 0, 95, 0, 7); g.fill(); g.restore();
  g.translate(0, bob); g.rotate(st.lean || 0);
  // legs: thin black sticks
  const hipY = -118, legL = 118;
  const sw = moving ? Math.sin(ph) * (st.action === 'run' ? 0.75 : 0.45) : 0;
  for (const [k, a] of [[-1, sw], [1, -sw]]) {
    const hx = k * 16, kx = hx + Math.sin(a) * legL * 0.5, ky = hipY + Math.cos(a) * legL * 0.5;
    const fa = a + (moving ? Math.max(0, -a) * 0.8 : 0);
    const fx = kx + Math.sin(fa) * legL * 0.5, fy = ky + Math.cos(fa) * legL * 0.5;
    g.beginPath(); g.moveTo(hx, hipY); g.lineTo(kx, ky); g.lineTo(fx, fy); g.lineWidth = 9; g.strokeStyle = C.ink; g.lineCap = 'round'; g.lineJoin = 'round'; g.stroke();
    g.beginPath(); g.ellipse(fx + 9, fy - 2, 17, 8, 0, 0, 7); fo(g, '#1f1b1d', 4);
  }
  // torso: a small costume body
  const top = -232;
  g.beginPath(); g.moveTo(-40, top); g.quadraticCurveTo(0, top - 10, 40, top); g.lineTo(46, hipY + 6); g.quadraticCurveTo(0, hipY + 16, -46, hipY + 6); g.closePath(); fo(g, cos.body);
  if (cos.detail === 'lamellar') { g.strokeStyle = 'rgba(0,0,0,0.28)'; g.lineWidth = 3; for (let y = top + 22; y < hipY; y += 16) { g.beginPath(); g.moveTo(-40, y); g.lineTo(40, y); g.stroke(); } }
  if (cos.detail === 'plates') { for (let y = top + 30; y < hipY - 4; y += 26) { g.beginPath(); g.rect(-40, y, 80, 12); g.fillStyle = cos.trim; g.fill(); } }
  if (cos.detail === 'buttons' || cos.detail === 'rivets') { for (let y = top + 24; y < hipY - 6; y += 22) { g.beginPath(); g.arc(cos.detail === 'rivets' ? -24 : 0, y, 5, 0, 7); fo(g, cos.trim, 3); if (cos.detail === 'rivets') { g.beginPath(); g.arc(24, y, 5, 0, 7); fo(g, cos.trim, 3); } } }
  if (cos.detail === 'patch') { g.beginPath(); g.rect(10, top + 40, 22, 20); fo(g, '#a68a62', 3); }
  g.beginPath(); g.rect(-45, hipY - 22, 90, 16); fo(g, cos.belt, 4);
  g.beginPath(); g.moveTo(-40, top); g.lineTo(0, top + 26); g.lineTo(40, top); g.lineWidth = 6; g.strokeStyle = cos.trim; g.stroke();
  // arms: thin sticks with small round hands
  const P = (POSES[st.action] || POSES.idle)(t, ph);
  const sh_ = [[-38, top + 14, P.armL, P.elL, -1], [38, top + 14, P.armR, P.elR, 1]];
  const hands = [];
  for (const [sx, sy, a, e, k] of sh_) {
    const ex = sx + Math.sin(a) * 52, ey = sy + Math.cos(a) * 52, ha = a + e, hx = ex + Math.sin(ha) * 50, hy = ey + Math.cos(ha) * 50;
    g.beginPath(); g.moveTo(sx, sy); g.lineTo(ex, ey); g.lineTo(hx, hy); g.lineWidth = 8.5; g.strokeStyle = C.ink; g.lineCap = 'round'; g.lineJoin = 'round'; g.stroke();
    hands.push([hx, hy, ha]);
  }
  // prop in the right hand
  if (st.prop === 'torch') { const [hx, hy] = hands[1]; g.beginPath(); g.moveTo(hx, hy + 8); g.lineTo(hx + 6, hy - 70); g.lineWidth = 9; g.strokeStyle = '#6a4424'; g.stroke();
    for (let i = 0; i < 3; i++) { const fl = Math.sin(t * 20 + i) * 6; g.beginPath(); g.moveTo(hx - 10, hy - 66); g.quadraticCurveTo(hx + 6 + fl, hy - 120 + i * 10, hx + 22, hy - 66); g.closePath(); g.fillStyle = ['#ff8a2a', '#ffc340', '#fff1a8'][i]; g.fill(); } }
  if (st.prop === 'spear') { const [hx, hy] = hands[1]; g.beginPath(); g.moveTo(hx, hy + 90); g.lineTo(hx, hy - 170); g.lineWidth = 7; g.strokeStyle = '#6a4424'; g.stroke(); g.beginPath(); g.moveTo(hx - 9, hy - 165); g.lineTo(hx, hy - 205); g.lineTo(hx + 9, hy - 165); g.closePath(); fo(g, '#c9d0d8', 4); }
  for (const [hx, hy] of hands) { g.beginPath(); g.arc(hx, hy, 11, 0, 7); fo(g, C.skin, 5); }
  // head: a big white egg (~40 % of the height)
  const R = 82, hcY = top - R * 0.95;
  g.save(); g.translate(0, hcY); g.rotate(st.headTilt || 0);
  if (def.hair) { g.beginPath(); g.arc(0, -R * 0.15, R * 1.04, Math.PI * 1.05, Math.PI * 1.95); g.closePath(); fo(g, def.hair); }
  g.beginPath(); g.ellipse(0, 0, R * 0.92, R * 1.08, 0, 0, 7); fo(g, C.skin);
  drawFace(g, R, { mood: st.mood || def.mood || 'neutral', blink: st.blink, talk: st.talk, look: st.look });
  facialHair(g, R, def.facial);
  (HATS[def.hat] || HATS.none)(g, R, { t, sway: st.hatSway || 0 });
  g.restore();
  g.restore();
  return { headY: st.y + (hcY + bob) * s };
}
