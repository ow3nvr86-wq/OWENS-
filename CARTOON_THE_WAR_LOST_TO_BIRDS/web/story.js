// The story: 13 shots timed to the narration (frame numbers from work/words.json). applyFrame(f, W) sets every
// object, card, light and effect for frame f and returns the camera, light, depth of field and post effects.
import { camFromKeys, smooth, smoother, easeOut, easeIn, back, spring, ramp, pulse, clamp, lerp, idle, blinkAt, hash, noise1 } from './motion.js';
import { ZONE } from './world.js';

export const FRAMES = 1256;
export const SHOTS = [
  { id: 1, a: 0, b: 127, name: 'chase' }, { id: 2, a: 128, b: 182, name: 'winning' },
  { id: 3, a: 183, b: 364, name: 'farm' }, { id: 4, a: 365, b: 490, name: 'farmer' },
  { id: 5, a: 491, b: 618, name: 'arrive' }, { id: 6, a: 619, b: 705, name: 'map' },
  { id: 7, a: 706, b: 752, name: 'scatter' }, { id: 8, a: 753, b: 793, name: 'jam' },
  { id: 9, a: 794, b: 862, name: 'bumpy' }, { id: 10, a: 863, b: 989, name: 'weeks' },
  { id: 11, a: 990, b: 1094, name: 'tally' }, { id: 12, a: 1095, b: 1207, name: 'no' },
  { id: 13, a: 1208, b: 1255, name: 'won' },
];
export const shotAt = f => SHOTS.find(s => f >= s.a && f <= s.b) || SHOTS[SHOTS.length - 1];

const CH = ZONE.chase;
const GUN = [67, 0, -20];                 // gun line (guns face -x, toward the field)
const PILE = [70.5, 0, -16.5];

// ---------- helpers ----------
let CAM = null;
function setCard(c, pos, pose, opt = {}) {
  c.visible = true; c.pos = pos; c.pose = pose; c.flip = !!opt.flip; c.lean = opt.lean || 0;
  c.ground = opt.ground ?? 0; c.blobOn = opt.blob ?? true; c.scale = opt.scale || 1; c.tint = opt.tint ?? 1;
}
// does a character moving along dir (x, z) read as facing left on screen? (drawings face right)
function faceFlip(dir) {
  const fx = CAM.look[0] - CAM.pos[0], fz = CAM.look[2] - CAM.pos[2];
  const rx = -fz, rz = fx;                 // camera right on the ground plane (y up)
  return dir[0] * rx + dir[1] * rz > 0;
}
function life(f, seed, amt = 1) { const i = idle(f, seed, amt); return { sx: i.sx, sy: i.sy, lean: i.tilt, bob: i.bob }; }
function hideAll(W) {
  for (const c of W.cards) c.visible = false;
  W.letter.position.y = -50; W.pad.position.y = -50;
  W.truckCargo.visible = false; W.truckGun.visible = true;
  W.truck.visible = false;
  W.stamp.position.y = 1.4;
  W.pile.visible = false;
}
function placeTruck(W, x, z, yaw, f, bump = 0.06, extraBounce = 0, wheelSpin = 0) {
  W.truck.visible = true;
  W.truck.position.set(x, 0, z); W.truck.rotation.set(0, yaw, 0);
  const b = Math.abs(Math.sin(f * 0.9)) * bump + Math.abs(Math.sin(f * 0.37 + 1)) * bump * 0.8 + extraBounce;
  W.truckBody.position.y = b;
  W.truckBody.rotation.set(Math.sin(f * 0.55) * bump * 0.5, 0, Math.sin(f * 0.41 + 2) * bump * 0.6);
  for (const w of W.wheels) w.rotation.x = wheelSpin;
  return b;
}
// local truck point -> world (truck yaw only; body bounce added to y)
function truckPt(W, lx, ly, lz) {
  const t = W.truck, a = t.rotation.y, c = Math.cos(a), s = Math.sin(a);
  return [t.position.x + lx * c + lz * s, ly + W.truckBody.position.y, t.position.z - lx * s + lz * c];
}
function puff(W, i, pos, t, scale = 1, col) {
  if (t < 0 || t > 1) return;
  setCard(W.puffs[i], pos, { t: Math.round(t * 16) / 16, col }, { blob: false, scale });
}

// ---------- canvases: map, letters, notepad ----------
let mapKey = '', letterKey = '', padKey = '', letter2Key = '';
function drawMap(W, prog, tap) {
  const key = Math.round(prog * 40) + '|' + tap;
  if (key === mapKey) return; mapKey = key;
  const g = W.mapCanvas.getContext('2d'), w = 1024, h = 1536;
  g.fillStyle = '#efe2bf'; g.fillRect(0, 0, w, h);
  g.fillStyle = 'rgba(150,110,60,0.18)'; for (let i = 0; i < 400; i++) g.fillRect(hash(i) * w, hash(i * 3) * h, 3, 3);
  g.strokeStyle = '#7a5a3a'; g.lineWidth = 10; g.strokeRect(30, 30, w - 60, h - 60);
  g.font = '100px "Covered By Your Grace"'; g.fillStyle = '#4a2b1a'; g.textAlign = 'center';
  g.fillText('THE PLAN', w / 2, 150);
  // the wheat field (top) with emus
  g.fillStyle = 'rgba(222,178,80,0.55)'; g.fillRect(110, 220, 804, 620);
  g.strokeStyle = '#8a6a30'; g.lineWidth = 6; g.setLineDash([18, 12]); g.strokeRect(110, 220, 804, 620); g.setLineDash([]);
  g.font = '64px "Covered By Your Grace"'; g.fillStyle = '#6a4a20'; g.textAlign = 'left'; g.fillText('WHEAT', 140, 300);
  for (let i = 0; i < 22; i++) {
    const x = 190 + hash(i * 3.3) * 640, y = 360 + hash(i * 5.1) * 420;
    g.fillStyle = '#4a3b31'; g.beginPath(); g.ellipse(x, y, 22, 15, 0, 0, 7); g.fill();
    g.strokeStyle = '#4a3b31'; g.lineWidth = 5; g.beginPath(); g.moveTo(x + 15, y - 6); g.lineTo(x + 24, y - 34); g.stroke();
    g.beginPath(); g.arc(x + 26, y - 36, 6, 0, 7); g.fill();
  }
  g.font = '62px "Covered By Your Grace"'; g.fillStyle = '#4a2b1a'; g.fillText('EMUS', 640, 810);
  // the guns (bottom)
  const guns = [[340, 1300], [690, 1300]];
  guns.forEach(([x, y], k) => {
    g.strokeStyle = '#a3262a'; g.lineWidth = 12;
    g.beginPath(); g.moveTo(x - 40, y - 40); g.lineTo(x + 40, y + 40); g.moveTo(x + 40, y - 40); g.lineTo(x - 40, y + 40); g.stroke();
    if (tap === k + 1) { g.beginPath(); g.arc(x, y, 72, 0, 7); g.lineWidth = 8; g.stroke(); }
  });
  g.fillStyle = '#a3262a'; g.font = '66px "Covered By Your Grace"'; g.textAlign = 'center'; g.fillText('GUNS', w / 2, 1440);
  // arrows: herd the birds toward the guns
  g.strokeStyle = '#a3262a'; g.fillStyle = '#a3262a'; g.lineWidth = 12; g.lineCap = 'round';
  const arrows = [[[250, 760], [260, 1000], [330, 1220]], [[780, 760], [770, 1000], [700, 1220]]];
  arrows.forEach((pts, k) => {
    const p = clamp(prog * 1.3 - k * 0.15);
    if (p <= 0) return;
    g.beginPath(); const n = 40; let lx = pts[0][0], ly = pts[0][1], px = lx, py = ly;
    g.moveTo(lx, ly);
    for (let i = 1; i <= n * p; i++) {
      const t = i / n, x = (1 - t) * (1 - t) * pts[0][0] + 2 * (1 - t) * t * pts[1][0] + t * t * pts[2][0];
      const y = (1 - t) * (1 - t) * pts[0][1] + 2 * (1 - t) * t * pts[1][1] + t * t * pts[2][1];
      px = lx; py = ly; g.lineTo(x, y); lx = x; ly = y;
    }
    g.stroke();
    if (p > 0.97) {
      const a = Math.atan2(ly - py, lx - px);
      g.beginPath(); g.moveTo(lx + Math.cos(a) * 14, ly + Math.sin(a) * 14);
      g.lineTo(lx + Math.cos(a + 2.5) * 50, ly + Math.sin(a + 2.5) * 50); g.lineTo(lx + Math.cos(a - 2.5) * 50, ly + Math.sin(a - 2.5) * 50); g.closePath(); g.fill();
    }
  });
  W.mapTex.needsUpdate = true;
}
function paper(g, w, h, tint = '#f7f0dc') {
  g.fillStyle = tint; g.fillRect(0, 0, w, h);
  g.fillStyle = 'rgba(150,120,70,0.10)'; for (let i = 0; i < 300; i++) g.fillRect(hash(i * 1.1) * w, hash(i * 2.3) * h, 4, 4);
  g.strokeStyle = 'rgba(80,110,170,0.35)'; g.lineWidth = 3;
  for (let y = 180; y < h - 60; y += 74) { g.beginPath(); g.moveTo(40, y); g.lineTo(w - 40, y); g.stroke(); }
}
function drawLetter(W) {
  if (letterKey) return; letterKey = '1';
  const g = W.letterCanvas.getContext('2d'), w = 768, h = 1024;
  paper(g, w, h);
  g.fillStyle = '#2b2a5a'; g.textAlign = 'left'; g.font = '74px "Covered By Your Grace"';
  g.fillText('To the Army,', 60, 160);
  g.font = '110px "Covered By Your Grace"'; g.fillStyle = '#20204a';
  g.fillText('PLEASE', 80, 380); g.fillText('SEND', 80, 520); g.fillText('MACHINE', 80, 660); g.fillText('GUNS!', 80, 800);
  g.font = '64px "Covered By Your Grace"'; g.fillStyle = '#2b2a5a'; g.fillText('- the farmers', 330, 940);
  W.letterTex.needsUpdate = true;
}
function drawLetter2(W, stamped) {
  const key = stamped ? 's' : 'u';
  if (key === letter2Key) return; letter2Key = key;
  const g = W.letter2Canvas.getContext('2d'), w = 768, h = 1024;
  paper(g, w, h);
  g.fillStyle = '#2b2a5a'; g.textAlign = 'left'; g.font = '70px "Covered By Your Grace"';
  g.fillText('To the Army,', 60, 160);
  g.font = '100px "Covered By Your Grace"'; g.fillStyle = '#20204a';
  g.fillText('PLEASE', 80, 340); g.fillText('SEND THE', 80, 470); g.fillText('ARMY', 80, 600); g.fillText('AGAIN!', 80, 730);
  g.font = '60px "Covered By Your Grace"'; g.fillText('- the farmers', 330, 900);
  if (stamped) {
    g.save(); g.translate(400, 560); g.rotate(-0.2);
    g.strokeStyle = 'rgba(190,30,35,0.92)'; g.lineWidth = 26; g.strokeRect(-250, -150, 500, 300);
    g.fillStyle = 'rgba(190,30,35,0.92)'; g.font = '260px Anton'; g.textAlign = 'center'; g.textBaseline = 'middle';
    g.fillText('NO', 0, 14);
    g.restore();
  }
  W.letter2Tex.needsUpdate = true;
}
function drawPad(W, prog) {
  const key = String(Math.round(prog * 30));
  if (key === padKey) return; padKey = key;
  const g = W.padCanvas.getContext('2d'), w = 768, h = 1024;
  paper(g, w, h, '#fbf6e6');
  g.fillStyle = '#7a1f22'; g.fillRect(0, 0, w, 70);
  g.textAlign = 'left'; g.fillStyle = '#1f1f3a';
  const lines = [['TALLY', 110, 130], ['ROUNDS FIRED:', 70, 300], ['9,860', 110, 420], ['EMUS:', 70, 560], ['986', 110, 680], ['= ABOUT 10 EACH', 70, 860]];
  const total = lines.reduce((s, l) => s + l[0].length, 0);
  let left = Math.round(prog * total);
  for (const [txt, size, y] of lines) {
    if (left <= 0) break;
    const s = txt.slice(0, left); left -= txt.length;
    g.font = `${size}px "Covered By Your Grace"`; g.fillText(s, 60, y);
  }
  if (prog > 0.98) { g.strokeStyle = '#a3262a'; g.lineWidth = 8; g.beginPath(); g.ellipse(390, 840, 340, 80, -0.03, 0, 7); g.stroke(); }
  W.padTex.needsUpdate = true;
}

// ---------- emu packs ----------
const PACK = [[1.6, 2.7, 10.6], [3.0, 2.0, 10.9], [6.0, -3.5, 11.2], [-4.0, -3.2, 10.4], [1.0, -5.6, 10.8], [8.5, 1.0, 11.4], [-7, 1.5, 10.2]];
function chasePack(W, f, truckX, t0, cnt = 7, lookFn = null) {
  for (let i = 0; i < cnt; i++) {
    const [dx, dz, sp] = PACK[i];
    const x = truckX + dx + (sp - 9) * (f - t0) / 30, z = CH[2] + dz;
    const run = ((x / 3.6) + i * 0.37) % 1;
    const pose = { run, f, face: i === 0 ? 'determined' : 'neutral', blink: blinkAt(f, i) };
    if (lookFn) Object.assign(pose, lookFn(i, f));
    setCard(W.emus[i], [x, 0, z], pose, { flip: faceFlip([1, 0]), lean: 0.06 });
  }
}
function fieldEmus(W, f, n, opt = {}) {
  for (let i = 0; i < n; i++) {
    const c = W.emus[i];
    const p = W.patches[i % W.patches.length];
    const x = p[0] + (hash(i * 7.7) - 0.5) * 2, z = p[1] + (hash(i * 3.3) - 0.5) * 2;
    const ph = f * 0.11 + i * 1.7;
    const peck = Math.pow(Math.max(0, Math.sin(ph)), 6);
    const wander = noise1(f / 60, i) * 0.6;
    const dir = hash(i * 5.5) > 0.5 ? [1, 0] : [-1, 0];
    setCard(c, [x + wander, 0, z], { peck: Math.round(peck * 8) / 8, f: Math.round(f / 3) * 3, blink: blinkAt(f, i), chew: peck < 0.1 && i % 3 === 0 },
      { flip: faceFlip(dir), lean: 0 });
  }
}

// ---------- shots ----------
function shotChase(W, f, out) {
  // 0-182: the truck bounces across the paddock; the emus run beside it and pull ahead
  const sp = 9;
  const tx = CH[0] + sp * f / 30, tz = CH[2];
  const bump = placeTruck(W, tx, tz, Math.PI / 2, f, 0.09, 0, -f * 0.6);
  // gunner on the flatbed behind the gun, bouncing higher than the truck
  const hop = Math.abs(Math.sin(f * 0.45)) * 0.32 + pulse(f, 40, 10) * 0.4 + pulse(f, 86, 12) * 0.5;
  const gp = truckPt(W, 0, 1.07 + hop, -2.95);
  setCard(W.gunner, gp, { face: 'shock', armR: 'grip', armL: f % 20 < 10 ? 'flail' : 'up', f, blink: false, sx: 1, sy: 1 - hop * 0.15 },
    { flip: faceFlip([1, 0]), blob: false, lean: Math.sin(f * 0.3) * 0.08 });
  W.truckGun.rotation.set(0, Math.PI / 2 + Math.sin(f * 0.5) * 0.4, Math.sin(f * 0.7) * 0.2);
  chasePack(W, f, tx, 0, 7, (i, ff) => i === 0 && ff > 145 ? { face: 'smug', look: -1 } : {});
  // dust puffs behind the rear wheels
  for (let k = 0; k < 6; k++) {
    const age = ((f + k * 5) % 30) / 30, born = f - age * 30;
    puff(W, 4 + k, [CH[0] + sp * born / 30 - 3.2, 0, tz + (k % 2 ? 1.1 : -1.1)], age, 1.1 + age * 1.2, '#e3c79a');
  }
  const lead = W.emus[0].pos;
  out.cam = chaseCam(f, tx, tz, lead, sp);
  out.light = 'day'; out.shadow = { center: [tx + 3, 0, tz], radius: 22 };
  out.dof = f > 150 ? { focus: Math.hypot(out.cam.pos[0] - lead[0], out.cam.pos[2] - lead[2]), cInf: 6 * ramp(f, 150, 170) } : { cInf: 0 };
}
function chaseCam(f, tx, tz, lead, sp) {
  // a camera that rides alongside: offsets relative to the moving truck, then glides to the lead emu
  const keys = [
    { f: 0, off: [5.2, 1.5, 4.8], lk: [-2.2, 2.4, 0.3], fov: 38 },
    { f: 64, off: [3.8, 1.3, 7.8], lk: [-1.6, 2.1, 0.0], fov: 40 },
    { f: 120, off: [0.6, 1.6, 8.6], lk: [-2.4, 2.0, 0.0], fov: 38 },
  ];
  let k0 = keys[0], k1 = keys[0];
  for (let i = 0; i < keys.length; i++) if (keys[i].f <= f) { k0 = keys[i]; k1 = keys[Math.min(keys.length - 1, i + 1)]; }
  const e = smoother(clamp((f - k0.f) / Math.max(1, k1.f - k0.f)));
  const L = (a, b) => a.map((v, i) => lerp(v, b[i], e));
  const off = L(k0.off, k1.off), lk = L(k0.lk, k1.lk);
  let pos = [tx + off[0], off[1], tz + off[2]], look = [tx + lk[0], lk[1], tz + lk[2]], fov = lerp(k0.fov, k1.fov, e);
  if (f > 128) {
    const g = smoother(ramp(f, 128, 170));
    const ep = [lead[0] + 6.0, 1.7, lead[2] + 3.6], el = [lead[0] + 0.1, 1.5, lead[2] - 0.3];
    pos = pos.map((v, i) => lerp(v, ep[i], g)); look = look.map((v, i) => lerp(v, el[i], g)); fov = lerp(fov, 36, g);
  }
  pos[1] += Math.sin(f * 0.8) * 0.03 + Math.sin(f * 0.31) * 0.04;      // handheld bounce
  return { pos, look, fov, roll: Math.sin(f * 0.23) * 1.2 };
}

function shotFarm(W, f, out) {
  // 183-364: gate sign close, crane up and back over the field full of emus
  fieldEmus(W, f, 30);
  W.millFan.rotation.z = -f * 0.08;
  out.cam = camFromKeys([
    { f: 183, pos: [0.9, 1.5, 7.4], look: [0, 1.55, 0.1], fov: 36 },
    { f: 255, pos: [0.3, 1.55, 6.3], look: [0, 1.55, 0.1], fov: 36 },
    { f: 318, pos: [7.5, 13.5, 13.5], look: [-2, 0, -26], fov: 42, ease: smoother, path: [[1.5, 4.5, 6.5]] },
    { f: 364, pos: [6.8, 12.6, 11.8], look: [-3, 0, -28], fov: 41 },
  ], f, { creep: 0.04 });
  out.light = 'day'; out.shadow = { center: [0, 0, -24], radius: 45 };
  out.dof = f < 262 ? { focus: 6.6, cInf: 7 } : { cInf: 0 };
  out.fx.flash = f < 189 ? 1 - (f - 183) / 6 : 0;
}

function shotFarmer(W, f, out) {
  // 365-490: the farmer (an ex-soldier) at the fence; then his letter asking for machine guns
  fieldEmus(W, f, 14);
  const fp = [-6, 0, 2.4];
  const salute = f >= 406 && f < 440;
  const pose = {
    face: f < 404 ? 'angry' : f < 440 ? 'determined' : 'happy', f,
    armR: f < 402 ? 'fist' : salute ? 'salute' : 'letter', prop: f >= 436 && f < 441 ? 'letter' : undefined,
    blink: blinkAt(f, 21), talk: 0, ...(f < 404 ? { headTilt: Math.sin(f * 0.9) * 0.05 } : {}),
  };
  const lf = life(f, 21);
  pose.sx = lf.sx * (salute ? 1.02 : 1); pose.sy = lf.sy * (salute ? 1.03 : 1);
  setCard(W.farmer, [fp[0], lf.bob + (salute ? 0.04 : 0), fp[2]], pose, { lean: lf.lean });
  drawLetter(W);
  if (f >= 441) {
    // the letter he holds up, in front of him, facing the camera
    const t = smoother(ramp(f, 441, 456));
    W.letter.position.set(fp[0] + 0.05, 1.36 + t * 0.06, fp[2] + 0.55);
    W.letter.rotation.set(-0.05, 0, -0.06 + Math.sin(f * 0.2) * 0.02);
  }
  out.cam = camFromKeys([
    { f: 365, pos: [-5.0, 1.55, 7.6], look: [-6, 1.45, 2.4], fov: 36 },
    { f: 436, pos: [-5.5, 1.52, 5.6], look: [-6, 1.5, 2.4], fov: 34 },
    { f: 462, pos: [-5.95, 1.44, 4.55], look: [-5.95, 1.42, 2.95], fov: 34, ease: smoother },
    { f: 490, pos: [-5.95, 1.43, 4.35], look: [-5.95, 1.42, 2.95], fov: 34 },
  ], f, { creep: 0.02 });
  out.light = 'day'; out.shadow = { center: fp, radius: 14 };
  out.dof = f < 445 ? { focus: Math.hypot(out.cam.pos[0] - fp[0], out.cam.pos[2] - fp[2]), cInf: 10 } : { focus: 1.45, cInf: 12 };
  out.fx.glint = f >= 408 && f < 420;
}

function shotArrive(W, f, out) {
  // 491-618: the army truck rolls in to the gate; two guns; a tower of ammunition crates
  const t = easeOut(ramp(f, 491, 528));
  const z = lerp(58, 13, t);
  const moving = f < 528;
  placeTruck(W, 0.6, z, Math.PI, f, moving ? 0.05 : 0.012, 0, (58 - z) / 0.5);
  W.truckCargo.visible = true; W.truckGun.visible = false;
  // crate tower wobbles once the truck stops
  const wob = f > 528 ? Math.sin((f - 528) * 0.35) * Math.exp(-(f - 528) / 40) * 0.6 + Math.sin(f * 0.12) * 0.15 : 0.1;
  W.crates.forEach((c, k) => { c.rotation.z = wob * 0.04 * k / 10; c.position.x = wob * 0.03 * k * k / 10; });
  // the major stands in the back, pointing ahead with his swagger stick
  const mp = truckPt(W, -0.3, 1.07, -0.6);
  setCard(W.major, mp, { face: f > 540 ? 'smug' : 'determined', armR: 'point', f, blink: blinkAt(f, 7), ...life(f, 7) },
    { flip: faceFlip([0, -1]), blob: false });
  fieldEmus(W, f, 10);
  if (moving) for (let k = 0; k < 4; k++) { const age = ((f + k * 7) % 28) / 28; puff(W, k, [0.6 + (k % 2 ? 1.2 : -1.2), 0, lerp(58, 13, easeOut(ramp(f - age * 28, 491, 528))) + 3.4], age, 1.4 + age, '#e3c79a'); }
  else puff(W, 0, [0.6, 0, 16.5], ramp(f, 528, 560), 2.6, '#e8d2aa');
  const rear = [0.6, 0, 13 + 2.4];
  out.cam = camFromKeys([
    { f: 491, pos: [4.2, 0.9, 6.0], look: [0.6, 1.9, 30], fov: 40 },
    { f: 528, pos: [4.6, 1.2, 7.2], look: [0.4, 2.1, 13.5], fov: 40 },
    { f: 545, pos: [3.2, 3.4, 13.4], look: [0.6, 1.3, 14.4], fov: 38, ease: smoother, path: [[4.8, 2.2, 10.5]] },
    { f: 600, pos: [3.4, 2.3, 18.8], look: [0.6, 5.0, 15.2], fov: 44, ease: smoother },
    { f: 618, pos: [3.3, 2.35, 19.3], look: [0.6, 5.3, 15.2], fov: 45 },
  ], f, { kicks: [{ f: 528, amp: 0.05 }] });
  out.light = 'day'; out.shadow = { center: [0.6, 0, 14], radius: 16 };
  out.dof = f > 530 && f < 560 ? { focus: 3.3, cInf: 6 } : { cInf: 0 };
}

function shotMap(W, f, out) {
  // 619-705: the plan, drawn on the map; the stick taps the guns
  const prog = ramp(f, 640, 690);
  const tap = f > 688 ? (f < 697 ? 1 : 2) : 0;
  drawMap(W, prog, tap);
  const T = ZONE.table;
  // map uv -> table local: x = (u - 0.5) * 1.4, z = (v - 0.5) * 2.1 (v down the canvas)
  const mp = (u, v) => [(u / 1024 - 0.5) * 1.4, (v / 1536 - 0.5) * 2.1];
  let tip;
  if (f < 640) tip = mp(515, 560);
  else if (f < 690) { const v = lerp(720, 1215, prog); tip = mp(515 + Math.sin(prog * 9) * 30, v); }
  else tip = mp(tap === 1 ? 340 : 690, 1300);
  const lift = f < 690 ? 0.03 + Math.abs(Math.sin(f * 0.5)) * 0.02 : 0.012 + Math.abs(Math.sin((f - 688) * 0.7)) * 0.08;
  W.mapStick.position.set(tip[0], 0.965 + lift, tip[1]);
  W.mapStick.rotation.set(-0.5, 2.6, 0);
  out.cam = camFromKeys([
    { f: 619, pos: [T[0] + 0.05, 4.4, T[2] + 0.85], look: [T[0], 0.96, T[2] - 0.02], fov: 40 },
    { f: 705, pos: [T[0] - 0.05, 4.0, T[2] + 0.75], look: [T[0], 0.96, T[2] + 0.04], fov: 40 },
  ], f, { creep: 0.01 });
  out.light = 'tent'; out.shadow = { center: T, radius: 5 };
  out.dof = { focus: 3.2, cInf: 4 };
}

function shotScatter(W, f, out) {
  // 706-752: the flock walks toward the guns, then bursts in every direction
  const c = [61.0, 0, -20];
  const burst = easeOut(ramp(f, 708, 752));
  for (let i = 0; i < 24; i++) {
    const a = hash(i * 2.2) * Math.PI * 2, r0 = Math.sqrt(hash(i * 4.1)) * 3.4;
    const x0 = c[0] + Math.cos(a) * r0 * 0.7 + (f - 706) * 0.04, z0 = c[2] + Math.sin(a) * r0;
    const ang = a + (hash(i) - 0.5) * 0.4;                 // every direction
    const d = burst * (4 + hash(i * 6) * 6);
    const x = x0 + Math.cos(ang) * d, z = z0 + Math.sin(ang) * d;
    const run = burst > 0.02 ? ((d / 3.2) + i * 0.3) % 1 : ((f * 0.03 + i * 0.4) % 1);
    setCard(W.emus[i], [x, 0, z], { run, f, face: burst > 0 ? 'alarm' : 'neutral', blink: blinkAt(f, i) },
      { flip: faceFlip(burst > 0.02 ? [Math.cos(ang), Math.sin(ang)] : [1, 0]), lean: burst > 0 ? 0.08 : 0 });
  }
  // two soldiers at the guns spin around in confusion
  setCard(W.gunner, [GUN[0] + 0.9, 0, GUN[2] - 2.2], { face: f > 714 ? 'shock' : 'determined', armR: f > 714 ? 'flail' : 'grip', armL: f > 714 ? 'flail' : 'hang', f }, { flip: f > 718 && f % 10 < 5 });
  setCard(W.soldier2, [GUN[0] + 0.9, 0, GUN[2] + 2.2], { face: f > 716 ? 'shock' : 'determined', armR: f > 716 ? 'up' : 'grip', f }, { flip: f > 720 && f % 12 < 6 });
  out.cam = camFromKeys([
    { f: 706, pos: [75.5, 5.0, -10.5], look: [61.5, 0.9, -20], fov: 44 },
    { f: 752, pos: [76.5, 7.8, -9.0], look: [61.0, 0.6, -20], fov: 54, ease: easeOut },
  ], f, { kicks: [{ f: 709, amp: 0.25 }] });
  out.light = 'day'; out.shadow = { center: c, radius: 30 };
  out.dof = { cInf: 0 };
}

function shotJam(W, f, out) {
  // 753-793: one gun jams in a puff of smoke; the gunner's face is covered in soot
  const gunW = [GUN[0] - 0.1, 0.95, GUN[2] - 2.2];
  const sooty = f > 765;
  setCard(W.gunner, [GUN[0] + 0.85, 0, GUN[2] - 2.2], { face: sooty ? 'squint' : 'determined', armR: 'grip', armL: 'grip', soot: sooty, f, blink: sooty && f > 780 && f < 784 },
    { flip: faceFlip([-1, 0]) });
  puff(W, 0, [gunW[0] - 0.7, 0.45, gunW[2]], ramp(f, 760, 790), 0.9, '#6d6668');
  puff(W, 1, [gunW[0] + 0.3, 0.6, gunW[2] - 0.1], ramp(f, 763, 793), 1.3, '#8a8486');
  W.lineGuns[0].rotation.set(f > 760 && f < 770 ? Math.sin(f * 3) * 0.05 : 0, 0, 0);
  out.cam = camFromKeys([
    { f: 753, pos: [GUN[0] - 1.6, 1.25, GUN[2] + 0.3], look: [GUN[0] + 0.4, 1.05, GUN[2] - 2.2], fov: 36 },
    { f: 793, pos: [GUN[0] - 1.1, 1.3, GUN[2] - 0.2], look: [GUN[0] + 0.5, 1.15, GUN[2] - 2.2], fov: 34 },
  ], f, { kicks: [{ f: 762, amp: 0.06 }, { f: 767, amp: 0.04 }] });
  out.light = 'day'; out.shadow = { center: [GUN[0], 0, GUN[2] - 2], radius: 8 };
  out.dof = { focus: 2.9, cInf: 9 };
}

function shotBumpy(W, f, out) {
  // 794-862: back to the chase; a big bump throws the gunner up and his hat flies off
  const sp = 9, ff = f - 794 + 260;
  const tx = CH[0] + sp * ff / 30, tz = CH[2];
  const big = f >= 817 ? Math.max(0, Math.sin(ramp(f, 817, 835) * Math.PI)) * 0.55 : 0;
  placeTruck(W, tx, tz, Math.PI / 2, ff, 0.1, big, -ff * 0.6);
  const fly = f >= 818 ? Math.max(0, Math.sin(ramp(f, 818, 846) * Math.PI)) * 1.9 : Math.abs(Math.sin(f * 0.45)) * 0.25;
  const gp = truckPt(W, 0, 1.07 + fly, -2.95);
  setCard(W.gunner, gp, { face: 'shock', armR: f > 818 ? 'flail' : 'grip', armL: 'flail', hat: f < 824, f },
    { flip: faceFlip([1, 0]), blob: false, lean: f > 818 ? Math.sin(f * 0.5) * 0.25 : 0.05 });
  if (f >= 824) {
    const t = (f - 824) / 30;
    const hp = [gp[0] - t * 7, Math.max(0.05, 3.6 + 1.4 * t - 6 * t * t), tz + 0.4];
    setCard(W.hat, hp, { spin: Math.round(((f - 824) * 0.4) * 8) / 8 }, { blob: false, scale: 0.9 });
  }
  W.truckGun.rotation.set(0, Math.PI / 2 + Math.sin(f * 0.8) * 0.6, Math.sin(f * 0.9) * 0.4);
  chasePack(W, ff, tx, 260, 5);
  for (let k = 0; k < 4; k++) { const age = ((f + k * 6) % 24) / 24; puff(W, 5 + k, [tx - 3.2 - age * 2, 0, tz + (k % 2 ? 1 : -1)], age, 1.2 + age, '#e3c79a'); }
  out.cam = { pos: [tx + 1.6, 1.5 + Math.sin(f * 0.8) * 0.04, tz + 7.6], look: [tx - 1.8, 2.3 + fly * 0.4, tz], fov: 40, roll: Math.sin(f * 0.3) * 1.5 };
  const kick = camFromKeys([{ f: 794, pos: [0, 0, 0], look: [0, 0, 0] }], f, { kicks: [{ f: 818, amp: 0.3 }], creep: 0 });
  out.cam.pos = out.cam.pos.map((v, i) => v + kick.pos[i]); out.cam.roll += kick.roll;
  out.light = 'day'; out.shadow = { center: [tx, 0, tz], radius: 18 };
  out.dof = { cInf: 0 };
}

function shotWeeks(W, f, out) {
  if (f < 938) {
    // 863-937: the truck drives away down the road; flash; it races straight back
    if (f < 903) {
      const t = easeIn(ramp(f, 863, 902));
      placeTruck(W, 0.4, lerp(12, 85, t), 0, f, 0.04, 0, t * 140);
      setCard(W.major, truckPt(W, -0.3, 1.07, -0.6), { face: 'tired', armR: 'hang', f }, { blob: false, flip: faceFlip([0, 1]) });
    } else {
      const t = easeOut(ramp(f, 903, 934));
      placeTruck(W, 0.4, lerp(110, 13, t), Math.PI, f, f < 934 ? 0.06 : 0.01, 0, -t * 190);
      setCard(W.major, truckPt(W, -0.3, 1.07, -0.6), { face: 'determined', armR: 'point', f }, { blob: false, flip: faceFlip([0, -1]) });
      W.truckGun.visible = true;
    }
    for (let k = 0; k < 4; k++) { const age = ((f + k * 6) % 24) / 24; const tz = W.truck.position.z + (f < 903 ? -3.4 : 3.4); puff(W, k, [0.4 + (k % 2 ? 1 : -1), 0, tz], age, 1.5 + age * 1.5, '#e3c79a'); }
    fieldEmus(W, f, 8);
    out.cam = camFromKeys([{ f: 863, pos: [2.6, 2.2, 2.0], look: [0.4, 1.5, 30], fov: 40 }, { f: 937, pos: [2.9, 2.0, 3.0], look: [0.4, 1.6, 26], fov: 40 }], f);
    out.light = 'day'; out.shadow = { center: [0.4, 0, 30], radius: 40 };
    out.fx.flash = f >= 903 && f < 909 ? 1 - (f - 903) / 6 : 0;
    out.dof = { cInf: 0 };
    return;
  }
  // 938-989: weeks of shooting - a time-lapse at the gun line; the casings pile grows
  const t = ramp(f, 938, 989);
  const cyc = t * 2;                                    // two day-night cycles
  const ph = cyc % 1;
  out.lightMix = ph < 0.25 ? ['day', 'golden', ph / 0.25] : ph < 0.5 ? ['golden', 'night', (ph - 0.25) / 0.25] : ph < 0.75 ? ['night', 'golden', (ph - 0.5) / 0.25] : ['golden', 'day', (ph - 0.75) / 0.25];
  const s = lerp(0.4, 1.3, smooth(t));
  W.pile.position.set(...PILE); W.pile.scale.set(s, s * 0.8, s); W.pile.visible = true;
  setCard(W.gunner, [GUN[0] + 0.85, 0, GUN[2] - 2.2], { face: f % 8 < 4 ? 'determined' : 'squint', armR: 'grip', armL: 'grip', f, soot: true }, { flip: faceFlip([-1, 0]) });
  setCard(W.soldier2, [GUN[0] + 0.85, 0, GUN[2] + 2.2], { face: 'determined', armR: 'grip', f }, { flip: faceFlip([-1, 0]) });
  for (let k = 0; k < 2; k++) puff(W, k, [GUN[0] - 1.3, 0.55, GUN[2] + (k ? 2.2 : -2.2)], ((f * 0.25 + k * 0.5) % 1), 0.7, '#d9d0c4');
  const a = lerp(0.3, 2.3, t);
  const cen = [GUN[0] + 2, 1.2, GUN[2]];
  out.cam = { pos: [cen[0] + Math.cos(a) * 11, 4.5, cen[2] + Math.sin(a) * 11], look: cen, fov: 44, roll: 0 };
  out.shadow = { center: cen, radius: 16 };
  out.dof = { cInf: 0 };
}

function shotTally(W, f, out) {
  // 990-1094: the major on a mountain of brass casings; his notepad tally
  const s = 2.6;
  W.pile.position.set(...PILE); W.pile.scale.set(s, s * 0.9, s); W.pile.visible = true;
  const top = [PILE[0], s * 0.9 - 0.15, PILE[2]];
  setCard(W.major, [top[0], top[1] - 0.25, top[2]], { face: 'tired', legs: 'sit', armR: 'pencil', prop: 'pencil', f: Math.round(f / 2) * 2, blink: blinkAt(f, 3), ...life(f, 3) },
    { blob: false, flip: true, ground: top[1] });
  setCard(W.gunner, [GUN[0] + 1.5, 0, GUN[2] - 1], { face: 'tired', armR: 'hang', soot: true, f, ...life(f, 9) }, {});
  if (f >= 1026) {
    drawPad(W, ramp(f, 1030, 1078));
    const cp = [top[0] + 1.6, top[1] + 0.95, top[2] + 1.8];
    W.pad.position.set(top[0] + 0.85, top[1] + 0.8, top[2] + 0.95);
    W.pad.lookAt(cp[0], cp[1], cp[2]);
  }
  out.cam = camFromKeys([
    { f: 990, pos: [PILE[0] + 7.5, 1.6, PILE[2] + 8.5], look: [top[0], top[1] + 0.6, top[2]], fov: 40 },
    { f: 1024, pos: [PILE[0] + 3.4, top[1] + 1.0, PILE[2] + 4.0], look: [top[0], top[1] + 0.8, top[2]], fov: 38 },
    { f: 1040, pos: [top[0] + 1.6, top[1] + 0.95, top[2] + 1.8], look: [top[0] + 0.85, top[1] + 0.8, top[2] + 0.95], fov: 36, ease: smoother },
    { f: 1094, pos: [top[0] + 1.45, top[1] + 0.92, top[2] + 1.62], look: [top[0] + 0.85, top[1] + 0.8, top[2] + 0.95], fov: 36 },
  ], f, { creep: 0.015 });
  out.light = 'golden'; out.shadow = { center: PILE, radius: 12 };
  out.dof = f < 1030 ? { focus: Math.hypot(out.cam.pos[0] - top[0], out.cam.pos[2] - top[2]), cInf: 8 } : { focus: 1.15, cInf: 14 };
}

function shotNo(W, f, out) {
  // 1095-1207: the farmers' new letter slides onto the Defence desk; the stamp comes down: NO
  const D = ZONE.desk;
  const stamped = f >= 1181;
  drawLetter2(W, stamped);
  const slide = easeOut(ramp(f, 1095, 1118));
  W.letter2.position.set(lerp(0.9, 0, slide), 0.945, lerp(0.9, 0.08, slide));
  W.letter2.rotation.set(-Math.PI / 2, 0, lerp(0.5, 0.06, slide));
  let sy = 1.6, sx = 0.0, sz = 0.05;
  if (f >= 1150 && f < 1176) sy = lerp(1.6, 1.35, easeOut(ramp(f, 1150, 1170))) + Math.sin(f * 0.6) * 0.01;      // wind-up
  else if (f >= 1176 && f < 1181) sy = lerp(1.35, 0.95, easeIn(ramp(f, 1176, 1181)));
  else if (f >= 1181 && f < 1186) sy = 0.95;
  else if (f >= 1186) sy = lerp(0.95, 2.4, easeOut(ramp(f, 1186, 1200)));
  W.stamp.position.set(sx, sy - 0.0, sz); W.stamp.rotation.set(0, 0.06, f >= 1181 && f < 1185 ? 0.03 : 0);
  if (f < 1146) W.stamp.position.y = 3;                    // out of shot until it comes in
  if (f >= 1146 && f < 1150) W.stamp.position.y = lerp(3, 1.6, easeOut(ramp(f, 1146, 1150)));
  puff(W, 0, [D[0] - 0.45, D[1] + 0.92, D[2] + 0.15], ramp(f, 1181, 1199), 0.35, '#efe3cf');
  puff(W, 1, [D[0] + 0.45, D[1] + 0.92, D[2] + 0.1], ramp(f, 1182, 1200), 0.3, '#efe3cf');
  out.cam = camFromKeys([
    { f: 1095, pos: [D[0] + 0.25, D[1] + 2.05, D[2] + 1.15], look: [D[0], D[1] + 0.93, D[2] + 0.12], fov: 40 },
    { f: 1178, pos: [D[0] + 0.1, D[1] + 1.85, D[2] + 0.95], look: [D[0], D[1] + 0.93, D[2] + 0.1], fov: 40 },
    { f: 1207, pos: [D[0] + 0.05, D[1] + 1.7, D[2] + 0.82], look: [D[0], D[1] + 0.93, D[2] + 0.1], fov: 40 },
  ], f, { kicks: [{ f: 1181, amp: 0.05 }], creep: 0.006 });
  out.light = 'tent'; out.shadow = { center: [D[0], 0.9, D[2]], radius: 3 };
  out.dof = { focus: 1.25, cInf: 7 };
}

function shotWon(W, f, out) {
  // 1208-1255: sunset; the lead emu wears the soldier's lost hat, chewing wheat. Smug blink on "won".
  fieldEmus(W, f, 16);
  const e = W.emus[30], p = [5.2, 0, 2.2];
  const blink = f >= 1233 && f < 1240;
  setCard(e, p, { face: 'smug', hat: true, chew: true, wheat: true, look: 1, f, blink, headTilt: f > 1236 ? 0.12 * smooth(ramp(f, 1236, 1246)) : 0, ...life(f, 30) },
    { flip: false, lean: 0 });
  out.cam = camFromKeys([
    { f: 1208, pos: [8.6, 1.5, 9.6], look: [5.5, 1.25, 2.2], fov: 38, roll: 0 },
    { f: 1255, pos: [6.4, 1.75, 5.0], look: [5.55, 1.72, 2.2], fov: 34, roll: 4, ease: smoother },
  ], f, { creep: 0.02 });
  out.light = 'golden'; out.shadow = { center: p, radius: 14 };
  out.dof = { focus: Math.hypot(out.cam.pos[0] - p[0], out.cam.pos[2] - p[2]), cInf: 11 };
}

const BY = { chase: shotChase, winning: shotChase, farm: shotFarm, farmer: shotFarmer, arrive: shotArrive, map: shotMap,
  scatter: shotScatter, jam: shotJam, bumpy: shotBumpy, weeks: shotWeeks, tally: shotTally, no: shotNo, won: shotWon };

export function applyFrame(f, W) {
  hideAll(W);
  const s = shotAt(f);
  const out = { cam: null, light: 'day', fx: {}, dof: { cInf: 0 } };
  // a provisional camera so faceFlip works while the shot places its cast; shots set the real one
  CAM = { pos: [0, 0, 10], look: [0, 0, 0] };
  BY[s.name](W, f, out);           // first pass: computes the camera
  CAM = out.cam;
  hideAll(W);
  const out2 = { cam: null, light: 'day', fx: {}, dof: { cInf: 0 } };
  BY[s.name](W, f, out2);          // second pass: faces cards with the real camera
  if (!out2.light) out2.light = 'day';
  if (W.millFan) W.millFan.rotation.z = -f * 0.08;
  // gentle cloud drift
  W.clouds.forEach((c, i) => { c.position.x += 0; c.lookAt(out2.cam.pos[0], c.position.y, out2.cam.pos[2]); });
  return out2;
}
