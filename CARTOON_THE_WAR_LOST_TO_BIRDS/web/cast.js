// The cast, drawn on a 600 x 1000 design canvas (soles at y = 975), flat colours with plum outlines.
// Humans: bean-head soldiers, the major and the farmer. Emus: side view with a run cycle, peck, chew and a hat.
// Every draw function takes a pose object; the caller rounds pose values so canvases only redraw on visible change.

export const PLUM = '#4b2142';
const LW = 9;

function outline(g, w = LW) { g.lineWidth = w; g.strokeStyle = PLUM; g.lineJoin = 'round'; g.lineCap = 'round'; g.stroke(); }
function fillOut(g, col, w = LW) { g.fillStyle = col; g.fill(); outline(g, w); }
function ell(g, x, y, rx, ry, rot = 0) { g.beginPath(); g.ellipse(x, y, Math.abs(rx), Math.abs(ry), rot, 0, Math.PI * 2); }
function rrect(g, x, y, w, h, r) { g.beginPath(); g.roundRect(x, y, w, h, r); }
function limb(g, pts, width, col) {
  // a thick rounded limb: plum stroke, then the colour stroke on top
  g.lineCap = 'round'; g.lineJoin = 'round';
  g.beginPath(); g.moveTo(pts[0][0], pts[0][1]);
  if (pts.length === 3) g.quadraticCurveTo(pts[1][0], pts[1][1], pts[2][0], pts[2][1]);
  else for (const p of pts.slice(1)) g.lineTo(p[0], p[1]);
  g.strokeStyle = PLUM; g.lineWidth = width + LW * 2; g.stroke();
  g.strokeStyle = col; g.lineWidth = width; g.stroke();
}

export const OUTFITS = {
  soldier: { skin: '#f1c7a1', shirt: '#b49a62', shirt2: '#9c8450', pants: '#8f7a4c', boots: '#5a3a22', hat: 'slouch', hatCol: '#a68d5c', band: '#6b5a3a', belt: '#6a5235', hair: '#6b3f22' },
  soldier2: { skin: '#e6b38a', shirt: '#ad945d', shirt2: '#937b49', pants: '#8a744a', boots: '#4e3320', hat: 'slouch', hatCol: '#9d8556', band: '#5f4f32', belt: '#6a5235', hair: '#2d1c12' },
  major: { skin: '#f3c9a5', shirt: '#9f8a57', shirt2: '#86733f', pants: '#857244', boots: '#3c2617', hat: 'peaked', hatCol: '#8f7a48', band: '#b3262d', belt: '#5a3b1f', hair: '#c9c3b8', moustache: '#ece6dc', stick: true },
  farmer: { skin: '#eab48b', shirt: '#6f8fb6', shirt2: '#587599', pants: '#7b5a3a', boots: '#4a2f1c', hat: 'slouch', hatCol: '#8c7350', band: '#5b4630', belt: null, braces: '#b9472f', hair: '#7a5232', medals: true, moustache: '#8a6544' },
};

// ---------- faces ----------
function eyes(g, cx, cy, p) {
  const look = p.look || 0, lookY = p.lookY || 0;
  const open = p.blink ? 0.08 : (p.face === 'squint' ? 0.45 : p.face === 'shock' ? 1.25 : 1);
  for (const s of [-1, 1]) {
    const ex = cx + s * 52, ey = cy;
    ell(g, ex, ey, 30, 36 * open); fillOut(g, '#ffffff', 6);
    if (open > 0.2) {
      const pr = p.face === 'shock' ? 9 : 13;
      ell(g, ex + look * 12, ey + 4 + lookY * 10, pr, pr * Math.min(1, open)); g.fillStyle = '#2a1428'; g.fill();
      ell(g, ex + look * 12 - 4, ey - 2 + lookY * 10, 4, 4); g.fillStyle = '#ffffff'; g.fill();
    }
    // lids for moods
    if (!p.blink && (p.face === 'smug' || p.face === 'determined' || p.face === 'angry' || p.face === 'tired')) {
      g.save(); ell(g, ex, ey, 31, 37 * open); g.clip();
      g.fillStyle = p.skin || '#f1c7a1';
      const tilt = p.face === 'angry' ? s * 0.35 : p.face === 'smug' ? -s * 0.15 : 0;
      g.translate(ex, ey); g.rotate(tilt);
      g.fillRect(-40, -60, 80, p.face === 'tired' ? 62 : 48);
      g.restore();
      g.beginPath(); g.moveTo(ex - 30, ey - (p.face === 'tired' ? 2 : 10) - s * (p.face === 'angry' ? 10 : 0));
      g.lineTo(ex + 30, ey - (p.face === 'tired' ? 2 : 10) + s * (p.face === 'angry' ? 10 : 0)); outline(g, 6);
    }
  }
}
function brows(g, cx, cy, p, col) {
  const f = p.face;
  for (const s of [-1, 1]) {
    let y0 = cy - 52, y1 = cy - 58;
    if (f === 'angry' || f === 'determined') { y0 = cy - 62; y1 = cy - 44; }
    if (f === 'shock' || f === 'happy') { y0 = cy - 70; y1 = cy - 74; }
    if (f === 'sad' || f === 'worried') { y0 = cy - 46; y1 = cy - 66; }
    g.beginPath(); g.moveTo(cx + s * 24, y1); g.lineTo(cx + s * 78, y0);
    g.lineWidth = 12; g.strokeStyle = col; g.lineCap = 'round'; g.stroke();
  }
}
function mouth(g, cx, cy, p) {
  const f = p.face, o = p.talk || 0;
  g.lineWidth = 7; g.strokeStyle = PLUM;
  if (f === 'shock' || o > 0.3) {
    ell(g, cx, cy + 6, 20 + o * 6, 16 + (f === 'shock' ? 18 : o * 14)); fillOut(g, '#7a2638', 6);
    ell(g, cx, cy + 16 + o * 6, 10, 5); g.fillStyle = '#e8737d'; g.fill();
  } else if (f === 'happy' || f === 'smug') {
    g.beginPath(); g.moveTo(cx - 34, cy - 2); g.quadraticCurveTo(cx + (f === 'smug' ? 14 : 0), cy + 30, cx + 34, cy - (f === 'smug' ? 10 : 2)); g.stroke();
  } else if (f === 'angry' || f === 'determined') {
    g.beginPath(); g.moveTo(cx - 26, cy + 10); g.quadraticCurveTo(cx, cy - 4, cx + 26, cy + 10); g.stroke();
  } else if (f === 'sad' || f === 'worried' || f === 'tired') {
    g.beginPath(); g.moveTo(cx - 24, cy + 14); g.quadraticCurveTo(cx, cy - 2, cx + 24, cy + 14); g.stroke();
  } else {
    g.beginPath(); g.moveTo(cx - 22, cy + 6); g.quadraticCurveTo(cx, cy + 14, cx + 22, cy + 4); g.stroke();
  }
}

// ---------- hats ----------
function slouchHat(g, cx, top, col, band) {
  // Australian slouch hat: wide brim, left side pinned up, dented crown with a band
  g.beginPath(); g.moveTo(cx - 190, top + 120); g.quadraticCurveTo(cx, top + 165, cx + 200, top + 112);
  g.quadraticCurveTo(cx + 170, top + 92, cx + 40, top + 96); g.lineTo(cx - 120, top + 98); g.closePath(); fillOut(g, col);
  g.beginPath(); g.moveTo(cx - 118, top + 104); g.quadraticCurveTo(cx - 128, top + 24, cx - 70, top + 10);
  g.quadraticCurveTo(cx, top - 4, cx + 70, top + 8); g.quadraticCurveTo(cx + 122, top + 30, cx + 118, top + 104);
  g.closePath(); fillOut(g, col);
  g.beginPath(); g.moveTo(cx - 20, top + 6); g.quadraticCurveTo(cx - 6, top + 40, cx + 8, top + 8); outline(g, 6);
  rrect(g, cx - 120, top + 70, 240, 34, 8); fillOut(g, band, 7);
  // pinned-up side brim (left of the face as drawn)
  g.beginPath(); g.moveTo(cx - 122, top + 104); g.quadraticCurveTo(cx - 190, top + 60, cx - 168, top - 10);
  g.quadraticCurveTo(cx - 130, top + 30, cx - 112, top + 70); g.closePath(); fillOut(g, col);
  ell(g, cx - 140, top + 40, 14, 14); fillOut(g, '#d8b54a', 5);           // rising-sun badge
}
function peakedCap(g, cx, top, col, band) {
  g.beginPath(); g.moveTo(cx - 132, top + 80); g.quadraticCurveTo(cx - 150, top + 8, cx, top - 6);
  g.quadraticCurveTo(cx + 150, top + 8, cx + 132, top + 80); g.closePath(); fillOut(g, col);
  rrect(g, cx - 122, top + 62, 244, 34, 10); fillOut(g, band, 7);
  g.beginPath(); g.moveTo(cx - 110, top + 96); g.quadraticCurveTo(cx + 20, top + 150, cx + 160, top + 100);
  g.quadraticCurveTo(cx + 40, top + 108, cx - 110, top + 96); fillOut(g, '#3b2a1a', 7);
  ell(g, cx, top + 42, 18, 16); fillOut(g, '#e0be55', 5);
}

// ---------- arms ----------
// returns [shoulder, elbow, hand] for one side (s = -1 left of image, +1 right) and an arm pose
function armPts(s, pose, f) {
  const sx = 300 + s * 112, sy = 470;
  const P = {
    hang: [[sx + s * 30, sy + 130], [sx + s * 26, sy + 250]],
    hip: [[sx + s * 80, sy + 90], [sx + s * 20, sy + 170]],
    point: [[sx + s * 110, sy - 20], [sx + s * 220, sy - 50]],
    up: [[sx + s * 60, sy - 110], [sx + s * 70, sy - 230]],
    fist: [[sx + s * 70, sy - 80], [sx + s * 40, sy - 200 + Math.sin(f * 0.9) * 30]],
    salute: [[sx + s * 110, sy - 40], [sx + s * 10, sy - 180]],
    hold: [[sx + s * 50, sy + 100], [sx + s * 0 - s * 70, sy + 130]],
    letter: [[sx + s * 60, sy + 90], [sx - s * 40, sy + 60]],
    grip: [[sx + s * 70, sy + 80], [sx + s * 140, sy + 60]],
    pencil: [[sx + s * 70, sy + 90], [sx - s * 50, sy + 40]],
    flail: [[sx + s * 120, sy - 60 + Math.sin(f * 1.7 + s) * 40], [sx + s * 200, sy - 180 + Math.cos(f * 1.3 + s) * 60]],
    cross: [[sx + s * 40, sy + 120], [sx - s * 110, sy + 110]],
    wave: [[sx + s * 90, sy - 60], [sx + s * 120 + Math.sin(f * 0.8) * 30, sy - 200]],
  }[pose] || [[sx + s * 30, sy + 130], [sx + s * 26, sy + 250]];
  return [[sx, sy], P[0], P[1]];
}
function arm(g, s, pose, f, o) {
  const [a, b, c] = armPts(s, pose, f);
  limb(g, [a, b, c], 54, o.shirt);
  // cuff and hand
  ell(g, c[0], c[1], 30, 30); fillOut(g, o.skin);
  return c;
}

// ---------- human ----------
export function drawHuman(g, outfitKey, p) {
  const o = OUTFITS[outfitKey], f = p.f || 0;
  g.save();
  g.translate(300, 975); g.scale(p.sx || 1, p.sy || 1); g.translate(-300, -975);
  // legs
  const ph = p.run != null ? p.run * Math.PI * 2 : null;
  for (const s of [-1, 1]) {
    let hip = [300 + s * 55, 720], knee, foot;
    if (ph != null) {
      const a = Math.sin(ph + (s > 0 ? Math.PI : 0));
      knee = [hip[0] + a * 60, 840 - Math.max(0, a) * 30]; foot = [hip[0] + a * 110, 960 - Math.max(0, -a) * 50];
    } else if (p.legs === 'sit') {
      knee = [hip[0] + 110, 760]; foot = [hip[0] + 120, 960];
    } else if (p.legs === 'wide') {
      knee = [hip[0] + s * 40, 845]; foot = [hip[0] + s * 70, 960];
    } else { knee = [hip[0] + s * 8, 845]; foot = [hip[0] + s * 6, 960]; }
    limb(g, [hip, knee, foot], 70, o.pants);
    ell(g, foot[0] + 22, foot[1] + 2, 56, 26); fillOut(g, o.boots);
  }
  // back arm (drawn before the torso)
  const backPose = p.armsBack || p.armL || 'hang';
  arm(g, -1, backPose, f, o);
  // torso
  g.beginPath(); g.moveTo(190, 470); g.quadraticCurveTo(300, 420, 410, 470);
  g.quadraticCurveTo(440, 600, 412, 740); g.quadraticCurveTo(300, 770, 188, 740); g.quadraticCurveTo(160, 600, 190, 470);
  fillOut(g, o.shirt);
  // pockets and buttons
  g.fillStyle = o.shirt2;
  rrect(g, 215, 520, 62, 56, 8); g.fill(); outline(g, 5); rrect(g, 323, 520, 62, 56, 8); g.fill(); outline(g, 5);
  for (let y = 500; y < 720; y += 52) { ell(g, 300, y, 7, 7); g.fillStyle = '#5a4528'; g.fill(); }
  if (o.belt) { rrect(g, 182, 668, 236, 34, 6); fillOut(g, o.belt, 6); rrect(g, 282, 664, 36, 42, 6); fillOut(g, '#d7b452', 5); }
  if (o.braces) { for (const x of [238, 362]) { rrect(g, x - 12, 470, 24, 260, 6); fillOut(g, o.braces, 5); } }
  if (o.medals) {
    for (const [x, c] of [[226, '#c0392b'], [256, '#2e6fb0'], [286, '#e3b23c']]) {
      rrect(g, x - 10, 540, 20, 30, 3); fillOut(g, c, 4); ell(g, x, 586, 12, 12); fillOut(g, '#e0be55', 4);
    }
  }
  // neck and head
  rrect(g, 262, 400, 76, 60, 20); fillOut(g, o.skin);
  const hy = 270 + (p.headBob || 0);
  const hx = 300 + (p.headX || 0);
  g.save(); g.translate(hx, hy); g.rotate(p.headTilt || 0); g.translate(-hx, -hy);
  // ears
  for (const s of [-1, 1]) { ell(g, hx + s * 128, hy + 18, 26, 34); fillOut(g, o.skin); }
  // bean head
  g.beginPath(); g.moveTo(hx - 125, hy - 30);
  g.bezierCurveTo(hx - 130, hy - 150, hx + 130, hy - 160, hx + 128, hy - 30);
  g.bezierCurveTo(hx + 132, hy + 90, hx + 70, hy + 140, hx, hy + 140);
  g.bezierCurveTo(hx - 80, hy + 140, hx - 122, hy + 80, hx - 125, hy - 30); fillOut(g, o.skin);
  if (o.beard) { g.beginPath(); g.moveTo(hx - 110, hy + 30); g.quadraticCurveTo(hx, hy + 190, hx + 110, hy + 30);
    g.quadraticCurveTo(hx, hy + 100, hx - 110, hy + 30); fillOut(g, o.beard, 6); }
  // cheeks
  for (const s of [-1, 1]) { ell(g, hx + s * 82, hy + 52, 22, 13); g.fillStyle = 'rgba(232,110,110,0.35)'; g.fill(); }
  const fp = Object.assign({ skin: o.skin }, p);
  eyes(g, hx + (p.look || 0) * 6, hy - 6, fp);
  brows(g, hx, hy - 6, fp, o.hair);
  // nose
  ell(g, hx + 8 + (p.look || 0) * 10, hy + 40, 20, 16); fillOut(g, o.skin, 6);
  if (o.moustache) { g.beginPath(); g.moveTo(hx - 70, hy + 74); g.quadraticCurveTo(hx - 30, hy + 44, hx, hy + 62);
    g.quadraticCurveTo(hx + 30, hy + 44, hx + 70, hy + 74); g.quadraticCurveTo(hx, hy + 84, hx - 70, hy + 74); fillOut(g, o.moustache, 6); }
  mouth(g, hx, hy + 92, fp);
  if (p.soot) { for (let i = 0; i < 7; i++) { ell(g, hx - 80 + i * 26, hy + 10 + (i % 3) * 24, 18, 12); g.fillStyle = 'rgba(40,30,30,0.55)'; g.fill(); } }
  // hat
  if (p.hat !== false) {
    const top = hy - 200 + (p.hatLift || 0);
    if (o.hat === 'slouch') slouchHat(g, hx, top, o.hatCol, o.band);
    else if (o.hat === 'peaked') peakedCap(g, hx, top + 20, o.hatCol, o.band);
  } else { g.beginPath(); g.moveTo(hx - 120, hy - 50); g.bezierCurveTo(hx - 110, hy - 150, hx + 110, hy - 150, hx + 120, hy - 50);
    g.quadraticCurveTo(hx, hy - 100, hx - 120, hy - 50); fillOut(g, o.hair, 6); }
  g.restore();
  // front arm + props
  const hand = arm(g, 1, p.armR || 'hang', f, o);
  if (p.prop === 'letter' || p.prop === 'notepad') {
    const [x, y] = hand;
    g.save(); g.translate(x - 40, y - 70); g.rotate(-0.12);
    rrect(g, -70, -60, 150, 190, 6); fillOut(g, '#f7f1e1', 6);
    g.strokeStyle = 'rgba(60,40,60,0.6)'; g.lineWidth = 5;
    for (let k = 0; k < 6; k++) { g.beginPath(); g.moveTo(-50, -30 + k * 26); g.lineTo(50 - (k % 2) * 30, -30 + k * 26); g.stroke(); }
    g.restore();
    ell(g, x, y, 30, 30); fillOut(g, o.skin);
  }
  if (p.prop === 'pencil') {
    const [x, y] = hand;
    g.save(); g.translate(x, y); g.rotate(-0.9 + Math.sin(f * 0.6) * 0.15);
    rrect(g, -8, -90, 16, 90, 4); fillOut(g, '#e8b33a', 5); g.restore();
    ell(g, x, y, 30, 30); fillOut(g, o.skin);
  }
  if (o.stick && (p.armR === 'point' || p.prop === 'stick')) {
    const [x, y] = hand; const a = p.armR === 'point' ? -0.3 : -1.2;
    g.save(); g.translate(x, y); g.rotate(a); rrect(g, 0, -8, 170, 16, 6); fillOut(g, '#5b3920', 5);
    ell(g, 170, 0, 12, 12); fillOut(g, '#d7b452', 4); g.restore();
    ell(g, x, y, 30, 30); fillOut(g, o.skin);
  }
  g.restore();
}

// ---------- emu ----------
const EMU = { body: '#6e5c4c', dark: '#4a3b31', light: '#93806b', neck: '#8d9cb4', skin: '#7a8bb0', beak: '#3d3a3a', leg: '#7b7b80' };
export function drawEmu(g, p) {
  const f = p.f || 0, ph = (p.run != null ? p.run : null);
  g.save();
  g.translate(300, 975); g.scale(p.sx || 1, p.sy || 1); g.translate(-300, -975);
  const runA = ph != null ? ph * Math.PI * 2 : 0;
  const bob = ph != null ? Math.abs(Math.sin(runA)) * -26 : 0;
  const by = 500 + bob + (p.crouch || 0);
  // legs: thigh hidden in feathers, backwards knee, long shin, three toes
  for (const s of [0, 1]) {
    const a = ph != null ? Math.sin(runA + s * Math.PI) : (s ? 0.12 : -0.12);
    const hip = [290 + s * 30, by + 120];
    const knee = [hip[0] - 30 + a * 70, by + 250 - Math.max(0, a) * 40];
    const ankle = ph != null ? [knee[0] + 40 + a * 110, 900 - Math.max(0, -a) * 90] : [knee[0] + 30, 905];
    limb(g, [hip, knee, ankle], 26, s ? EMU.leg : '#6c6c72');
    // foot
    const fx = ankle[0], fy = Math.min(965, ankle[1] + 50);
    g.beginPath(); g.moveTo(fx - 30, fy); g.lineTo(fx + 60, fy); g.moveTo(fx, fy); g.lineTo(fx + 40, fy - 6);
    g.moveTo(fx, ankle[1]); g.lineTo(fx, fy);
    g.lineWidth = 16 + LW * 2; g.strokeStyle = PLUM; g.stroke(); g.lineWidth = 16; g.strokeStyle = s ? EMU.leg : '#6c6c72'; g.stroke();
  }
  // body: shaggy oval
  g.beginPath();
  const cx = 290, rx = 200, ry = 150;
  for (let i = 0; i <= 48; i++) {
    const t = i / 48 * Math.PI * 2, shag = (i % 2 ? 1 : 0.9) * (Math.sin(t) > 0.2 ? 1.06 : 1);
    const x = cx + Math.cos(t) * rx * shag, y = by + Math.sin(t) * ry * shag;
    i ? g.lineTo(x, y) : g.moveTo(x, y);
  }
  g.closePath(); fillOut(g, EMU.body);
  // feather strokes
  g.strokeStyle = EMU.dark; g.lineWidth = 7; g.lineCap = 'round';
  for (let i = 0; i < 26; i++) {
    const t = (i * 0.37) % 1, u = ((i * 0.61) % 1);
    const x = cx - rx * 0.8 + t * rx * 1.5, y = by - ry * 0.5 + u * ry * 1.2;
    g.beginPath(); g.moveTo(x, y); g.quadraticCurveTo(x - 18, y + 22, x - 30, y + 46 + (i % 3) * 8); g.stroke();
  }
  g.strokeStyle = EMU.light; g.lineWidth = 5;
  for (let i = 0; i < 10; i++) { const x = cx - 120 + i * 26, y = by - 90 + (i % 3) * 18; g.beginPath(); g.moveTo(x, y); g.quadraticCurveTo(x - 12, y + 16, x - 18, y + 34); g.stroke(); }
  // neck: S-curve from the chest to the head; peck lowers it to the ground, look turns the head
  const peck = p.peck || 0;
  const base = [cx + 150, by - 70];
  const head = [cx + 190 + peck * 70 + (p.headX || 0), by - 360 + peck * 720 + (p.headY || 0) + (ph != null ? Math.sin(runA * 2) * 10 : 0)];
  const mid = [cx + 215 + peck * 70, (base[1] + head[1]) / 2 + 20 - peck * 40];
  g.lineCap = 'round';
  g.beginPath(); g.moveTo(base[0], base[1]); g.quadraticCurveTo(mid[0], mid[1], head[0], head[1]);
  g.strokeStyle = PLUM; g.lineWidth = 74 + LW * 2; g.stroke();
  g.strokeStyle = EMU.body; g.lineWidth = 74; g.stroke();
  // upper neck: bluish skin
  g.beginPath(); const nt = 0.45;
  const qx = (1 - nt) * (1 - nt) * base[0] + 2 * (1 - nt) * nt * mid[0] + nt * nt * head[0];
  const qy = (1 - nt) * (1 - nt) * base[1] + 2 * (1 - nt) * nt * mid[1] + nt * nt * head[1];
  g.moveTo(qx, qy); g.quadraticCurveTo((mid[0] + head[0]) / 2, (mid[1] + head[1]) / 2, head[0], head[1]);
  g.strokeStyle = EMU.neck; g.lineWidth = 50; g.stroke();
  // head
  const hx = head[0], hy = head[1];
  g.save(); g.translate(hx, hy); g.rotate((p.headTilt || 0) + peck * 0.9);
  // beak (chewing opens it)
  const chew = p.chew ? Math.max(0, Math.sin(f * 0.9)) * 0.22 : (p.beakOpen || 0);
  g.save(); g.rotate(-chew * 0.5);
  g.beginPath(); g.moveTo(40, -16); g.quadraticCurveTo(120, -14, 138, 2); g.lineTo(40, 6); g.closePath(); fillOut(g, EMU.beak, 7);
  g.restore();
  g.save(); g.rotate(chew * 0.6);
  g.beginPath(); g.moveTo(40, 4); g.quadraticCurveTo(110, 8, 128, 12); g.lineTo(40, 20); g.closePath(); fillOut(g, '#55504f', 7);
  if (p.wheat) { g.strokeStyle = '#e8b84a'; g.lineWidth = 6; g.beginPath(); g.moveTo(110, 10); g.lineTo(170, 30); g.moveTo(120, 12); g.lineTo(160, 0); g.stroke(); }
  g.restore();
  ell(g, 0, 0, 62, 52); fillOut(g, EMU.skin);
  g.strokeStyle = EMU.dark; g.lineWidth = 6;
  for (let i = 0; i < 5; i++) { g.beginPath(); g.moveTo(-50 + i * 10, -40); g.lineTo(-58 + i * 9, -62); g.stroke(); }  // head fuzz
  // eye: big, with expression lids
  const open = p.blink ? 0.08 : (p.face === 'alarm' ? 1.2 : 1);
  ell(g, 14, -8, 27, 30 * open); fillOut(g, '#fff6e0', 6);
  if (open > 0.2) {
    ell(g, 20 + (p.look || 0) * 8, -6 + (p.lookY || 0) * 8, p.face === 'alarm' ? 7 : 11, (p.face === 'alarm' ? 7 : 12) * Math.min(1, open));
    g.fillStyle = '#1e1016'; g.fill();
    ell(g, 16 + (p.look || 0) * 8, -11, 4, 4); g.fillStyle = '#fff'; g.fill();
  }
  if (!p.blink && (p.face === 'smug' || p.face === 'determined')) {
    g.save(); ell(g, 14, -8, 28, 31); g.clip(); g.fillStyle = EMU.skin; g.fillRect(-20, -50, 70, p.face === 'smug' ? 40 : 34); g.restore();
    g.beginPath(); g.moveTo(-12, p.face === 'smug' ? -10 : -16); g.lineTo(42, p.face === 'smug' ? -12 : -22); outline(g, 6);
  }
  // the soldier's lost slouch hat
  if (p.hat) {
    g.save(); g.translate(-6, -58); g.scale(0.62, 0.62); slouchHat(g, 0, -150, OUTFITS.soldier.hatCol, OUTFITS.soldier.band); g.restore();
  }
  g.restore();
  // tail fluff
  g.beginPath(); g.moveTo(cx - 180, by - 30); g.quadraticCurveTo(cx - 260, by + 30, cx - 230, by + 120);
  g.quadraticCurveTo(cx - 190, by + 60, cx - 160, by + 40); fillOut(g, EMU.dark);
  g.restore();
}

// ---------- small cards ----------
export function drawHat(g, p) {               // the soldier's slouch hat on its own (it flies off and is lost)
  g.save(); g.translate(300, 700); g.rotate(p.spin || 0); g.scale(1.25, 1.25);
  slouchHat(g, 0, -80, OUTFITS.soldier.hatCol, OUTFITS.soldier.band); g.restore();
}
export function drawPuff(g, p) {              // smoke / dust puff: a cluster of soft circles that grows and thins
  const t = p.t || 0, col = p.col || '#e9dcc4';
  const blobs = [[300, 760, 130], [200, 800, 95], [400, 800, 100], [250, 690, 90], [360, 680, 85], [300, 610, 70]];
  g.globalAlpha = Math.max(0, 1 - t * t);
  for (const [x, y, r] of blobs) {
    const s = 0.5 + t * 0.9;
    ell(g, 300 + (x - 300) * s, 975 - (975 - y) * s - t * 120, r * s, r * s);
    g.fillStyle = col; g.fill(); g.lineWidth = 6; g.strokeStyle = 'rgba(75,33,66,0.35)'; g.stroke();
  }
  g.globalAlpha = 1;
}
export const DRAW = {
  emu: (g, o, p) => drawEmu(g, p),
  human: (g, o, p) => drawHuman(g, o, p),
  hat: (g, o, p) => drawHat(g, p),
  puff: (g, o, p) => drawPuff(g, p),
};
