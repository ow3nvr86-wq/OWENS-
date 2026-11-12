// "What if you were trapped in Minecraft?" - six shots in narration seconds (60 fps: t = f / 60). Every action sits
// on the same beat as the sound design (audio.py): punches, log pops, mining hits, the weight, block thunks, the door,
// the eyes, the rip. Changes are eased (blinks hide mood switches, pops overshoot), walks are planted.
import { camFromKeys, smooth, smoother, easeOut, easeIn, back, ramp, clamp, lerp, idle, blinkAt, hash, noise1 } from './motion.js';
import { Z } from './world.js';

export const FPS = 60;
export const FRAMES = 2522;
const SH = [
  { name: 'tree', a: 0, b: 13.5 }, { name: 'mine', a: 13.5, b: 22.6 }, { name: 'house', a: 22.6, b: 30.45 },
  { name: 'bed', a: 30.45, b: 38.35 }, { name: 'hb', a: 38.35, b: 39.7 }, { name: 'notes', a: 39.7, b: 99 },
];
export const shotAt = t => SH.find(s => t >= s.a && t < s.b) || SH[SH.length - 1];

let CAM = { pos: [0, 0, 10], look: [0, 0, 0] };
function faceFlip(dir) { const fx = CAM.look[0] - CAM.pos[0], fz = CAM.look[2] - CAM.pos[2]; return dir[0] * -fz + dir[1] * fx > 0; }
function setCard(c, pos, pose, opt = {}) {
  c.visible = true; c.pos = pos; c.pose = pose; c.flip = !!opt.flip; c.lean = opt.lean || 0; c.ground = opt.ground ?? 0;
  c.blobOn = opt.blob ?? true; c.scale = opt.scale || 1; c.tint = opt.tint ?? 1; c.noTint = !!opt.noTint;
}
// camera keys in seconds -> the frame-based helper (30-unit clock keeps the creep/kick speeds it was tuned for)
function cam(keys, t, opt = {}) { return camFromKeys(keys.map(k => ({ ...k, f: k.t * 30 })), t * 30, { ...opt, kicks: (opt.kicks || []).map(k => ({ f: k.t * 30, amp: k.amp })) }); }
const pop = (t, at, len = 0.28) => t < at ? 0 : back(ramp(t, at, at + len), 2.2);
function moodAt(t, keys) { let m = keys[0][1]; for (const [k, v] of keys) if (t >= k) m = v; return m; }
function blinkNear(t, keys, seed = 0) { for (const [k] of keys) if (k > 0 && Math.abs(t - k) < 0.05) return true; return blinkAt(t * 30, seed); }
function life(t, seed) { const i = idle(t * 30, seed); return { sx: i.sx, sy: i.sy }; }
// planted walk: x(t) eased; the leg phase comes from distance (stride 1.3 m per cycle)
function walk(t, t0, t1, a, b) {
  const u = smoother(ramp(t, t0, t1)), x = a + (b - a) * u, d = Math.abs(x - a);
  const moving = t > t0 && t < t1;
  return { x, run: moving ? (d / 1.3) % 1 : null, bob: moving ? Math.abs(Math.sin(d / 1.3 * Math.PI * 2)) * 0.05 : 0, dir: Math.sign(b - a) };
}
function hideAll(W) {
  for (const c of W.cards) c.visible = false;
  W.weight.position.y = -50; for (const m of W.minis) m.position.y = -50;
  W.noteL.position.y = W.noteR.position.y = -50; W.blanket.position.y = -50;
  W.moon.position.y = -500; W.sunDisc.position.y = -500; for (const s of W.stars) s.position.y = -500;
  W.torchLight.intensity = 0;
  W.logs.forEach(l => { l.visible = true; }); W.mineable.forEach(m => { m.visible = true; });
  W.houseBlocks.forEach(b => { b.m.visible = true; b.m.position.copy(b.home); b.m.scale.set(1, 1, 1); });
  W.doorPivot.visible = true; W.doorPivot.rotation.y = 0; W.doorPivot.scale.set(1, 1, 1);
}
function mini(W, i, kind, pos, s = 1) { const m = W.minis[i]; m.material = W.miniMats[kind]; m.position.set(...pos); m.scale.setScalar(s); m.rotation.set(pos[0] * 3, pos[1] * 2, 0); }
function sunAt(W, el, az, dist = 600) {     // a square sun disc in the sky in the light's direction
  const a = az * Math.PI / 180, e = el * Math.PI / 180;
  W.sunDisc.position.set(CAM.pos[0] + Math.sin(a) * Math.cos(e) * dist, CAM.pos[1] + Math.sin(e) * dist, CAM.pos[2] + Math.cos(a) * Math.cos(e) * dist);
  W.sunDisc.lookAt(...CAM.pos);
}
function nightSky(W, a) {
  if (a <= 0) return;
  W.moon.position.set(CAM.pos[0] - 200, CAM.pos[1] + 260, CAM.pos[2] - 520); W.moon.lookAt(...CAM.pos);
  W.stars.forEach((s, i) => { const u = hash(i) * 2 - 1, v = hash(i * 3); s.position.set(CAM.pos[0] + u * 600, CAM.pos[1] + 120 + v * 500, CAM.pos[2] - 600); s.lookAt(...CAM.pos); s.material.opacity = a * (0.5 + 0.5 * hash(i * 7)); });
}

// ---------------- A. wake up, no tools, no food, ten minutes; the tree; the floating top ----------------
function shotTree(W, t, out) {
  W.houseBlocks.forEach(b => { b.m.visible = false; }); W.doorPivot.visible = false;
  const [tx, , tz] = Z.tree;
  const pops = [9.70, 10.12, 10.38, 10.62];
  pops.forEach((p, i) => { if (t >= p) W.logs[i].visible = false; });
  // popped logs hop out then zip to his pocket
  const W1 = walk(t, 6.55, 7.05, 0, 2.15), W2 = walk(t, 10.75, 11.3, 2.15, 0.9);
  const hx = t < 10.75 ? W1.x : W2.x;
  pops.forEach((p, i) => {
    if (t < p || t > p + 0.85) return;
    const u = t - p, sx = tx + 0.5, sy = i + 0.5, sz = tz + 0.9;
    if (u < 0.55) mini(W, i, 'log', [sx - u * 0.9, sy + Math.sin(Math.min(1, u / 0.55) * Math.PI) * 0.7 - u * 0.6, sz + u * 0.4], 0.9);
    else { const v = smooth((u - 0.55) / 0.3); mini(W, i, 'log', [lerp(sx - 0.5, hx, v), lerp(0.4, 0.95, v), lerp(sz + 0.2, 0.2, v)], 0.9 * (1 - v * 0.8)); }
  });
  const moods = [[0, 'tired'], [0.62, 'shock'], [2.55, 'worried'], [3.5, 'sad'], [4.5, 'shock'], [6.55, 'determined'], [8.27, 'angry'], [9.72, 'happy'], [11.05, 'shock'], [12.55, 'neutral']];
  let armR = 'hang', armL = 'hang', lookY = 0, look = 0;
  if (t > 2.55 && t < 3.45) { armR = armL = 'hip'; lookY = 0.6; }
  else if (t > 3.45 && t < 4.45) { armR = armL = 'tummy'; lookY = 0.7; }
  else if (t > 4.45 && t < 6.5) { lookY = -1; look = 0.5; }
  if (t > 7.05 && t < 9.65) { const k = (t - 7.12) / 0.26, ph = k - Math.floor(k); armR = t < 7.12 ? 'windup' : (ph < 0.38 ? 'punch' : 'windup'); look = 1; }
  if (t > 10.8 && t < 12.55) { lookY = -1; look = 0.4; }
  if (t > 12.6) { armR = armL = 'shrug'; }
  const wake = back(ramp(t, 0.25, 0.9), 1.4);
  const lying = 1 - clamp(wake);
  const run = t < 10.75 ? W1.run : W2.run, dir = t < 10.75 ? 1 : -1;
  const lf = life(t, 1);
  setCard(W.hero, [hx + lying * 0.9, lying * 0.45 + (t < 10.75 ? W1.bob : W2.bob), 0.3],
    { face: moodAt(t, moods), armR, armL, hat: false, look, lookY, run, f: Math.round(t * 30), blink: blinkNear(t, moods, 1) || t < 0.25, sx: lf.sx, sy: lf.sy },
    { flip: run != null ? faceFlip([dir, 0]) : faceFlip([1, 0]), lean: lying * 1.5708 });
  if (t > 8.3 && t < 9.5) {                       // "bare-handed": a little puff of bark dust at each punch
    const k = (t - 7.12) / 0.26; setCard(W.puffs[0], [tx + 0.1, 1.0, tz + 1.1], { t: Math.round((k % 1) * 16) / 16, col: '#c9a47a' }, { blob: false, scale: 0.35 });
  }
  CAM = out.cam = cam([
    { t: 0, pos: [1.2, 0.55, 3.4], look: [0.0, 0.45, 0.2], fov: 40 },
    { t: 2.3, pos: [0.9, 1.2, 4.6], look: [0.2, 1.05, 0.2], fov: 40 },
    { t: 4.4, pos: [1.1, 1.3, 5.2], look: [0.6, 1.4, 0.0], fov: 40 },
    { t: 5.3, pos: [1.4, 1.1, 5.8], look: [-3.5, 10.5, -6.0], fov: 48 },
    { t: 6.4, pos: [1.6, 1.2, 6.0], look: [-3.0, 9.5, -6.0], fov: 48 },
    { t: 7.1, pos: [2.0, 1.45, 4.6], look: [2.6, 1.25, -1.2], fov: 40 },
    { t: 8.2, pos: [2.2, 1.45, 4.2], look: [2.7, 1.3, -1.4], fov: 40 },
    { t: 8.9, pos: [2.25, 1.45, 3.0], look: [2.75, 1.35, -1.4], fov: 38 },
    { t: 9.65, pos: [2.0, 1.5, 4.8], look: [2.6, 1.3, -1.4], fov: 40 },
    { t: 10.8, pos: [1.6, 1.4, 6.2], look: [2.4, 1.6, -1.6], fov: 42 },
    { t: 11.9, pos: [1.2, 1.3, 9.2], look: [2.4, 2.9, -2.0], fov: 48 },
    { t: 13.5, pos: [1.1, 1.3, 9.4], look: [2.3, 2.8, -2.0], fov: 48 },
  ], t, { creep: 0.03, kicks: [{ t: 9.70, amp: 0.04 }] });
  out.light = 'day'; out.shadow = { center: [1.5, 0, -1], radius: 10 };
  { // the sun sits where he looks up, a little above the frame centre
    const d = [-4.9, 9.4, -11.8], n = Math.hypot(...d);
    W.sunDisc.position.set(CAM.pos[0] + d[0] / n * 600, CAM.pos[1] + d[1] / n * 600 + 40, CAM.pos[2] + d[2] / n * 600); W.sunDisc.lookAt(...CAM.pos); }
  out.dof = { focus: Math.hypot(CAM.pos[0] - hx, CAM.pos[2] - 0.3), cInf: t > 4.6 && t < 6.6 ? 0 : 7 };
}

// ---------------- B. craft a pickaxe, mine the mountain, 64 blocks, 150 tonnes, skip away ----------------
function shotMine(W, t, out) {
  W.houseBlocks.forEach(b => { b.m.visible = false; }); W.doorPivot.visible = false;
  const craft = ramp(t, 13.55, 13.95), hasPick = t >= 13.95;
  const W1 = walk(t, 14.35, 15.0, 7.0, 9.7), W2 = walk(t, 21.05, 22.6, 9.7, 6.4);
  const skipping = t >= 21.05;
  const hx = skipping ? W2.x : W1.x;
  if (!hasPick) for (let i = 0; i < 4; i++) { const a = i / 4 * Math.PI * 2 + t * 6, r = 0.6 * (1 - craft); mini(W, i, 'planks', [7.0 + Math.cos(a) * r, 2.25 + Math.sin(a) * r * 0.5, 0.4], 0.8); }
  if (t > 13.9 && t < 14.3) setCard(W.puffs[0], [7.0, 1.75, 0.45], { t: Math.round(ramp(t, 13.9, 14.3) * 16) / 16, col: '#ffffff' }, { blob: false, scale: 0.5 });
  // mining: a hit every 0.3 s; each hit removes the next block and sends a mini block to his pocket
  const mining = t >= 15.0 && t < 18.1;
  const k = (t - 15.0) / 0.3, ph = k - Math.floor(k), hits = mining ? Math.floor(k + 0.55) : (t >= 18.1 ? 11 : 0);
  for (let j = 0; j < Math.min(hits, W.mineable.length); j++) W.mineable[j].visible = false;
  if (mining) for (let j = 0; j < 3; j++) { const u = (k + j / 3) % 1; const b = W.mineable[Math.min(W.mineable.length - 1, Math.floor(k))].position;
    mini(W, 4 + j, 'stone', [lerp(b.x, hx + 0.1, smooth(u)), lerp(b.y, 0.95, smooth(u)) + Math.sin(u * Math.PI) * 0.6, lerp(b.z, 0.35, smooth(u))], 0.9 * (1 - u * 0.7)); }
  // the weight drops on 'hundred'
  if (t > 18.6) {
    const fall = ramp(t, 18.6, 19.25), y = lerp(22, 0, easeIn(fall)), sq = t > 19.25 ? 1 - Math.sin(ramp(t, 19.25, 19.5) * Math.PI) * 0.12 : 1;
    W.weight.position.set(7.4, y, 1.1); W.weight.scale.set(1 / sq, sq, 1 / sq);
    if (t > 19.25) for (let i = 0; i < 2; i++) setCard(W.puffs[1 + i], [7.4 + (i ? 1.3 : -1.3), 0, 1.2], { t: Math.round(ramp(t, 19.25, 19.9) * 16) / 16, col: '#e8d2aa' }, { blob: false, scale: 1.1 });
  }
  const moods = [[0, 'shock'], [13.98, 'happy'], [15.0, 'determined'], [18.2, 'neutral'], [19.3, 'squint'], [20.0, 'neutral'], [21.1, 'happy']];
  let armR = W1.run != null ? 'hang' : 'hang', armL = 'hang', look = 1;
  if (t < 14.35) { armR = armL = 'up'; }
  if (mining) armR = ph < 0.45 ? 'swingUp' : 'swingDown';
  if (skipping) { armL = 'wave'; look = -1; }
  const pickA = mining ? (ph < 0.45 ? -0.9 : 0.9) : (skipping ? -0.5 : 0.2);
  const lf = life(t, 2);
  setCard(W.hero, [hx, (skipping ? W2.bob * 2.4 : W1.bob), 0.3],
    { face: moodAt(t, moods), armR, armL, hat: false, look, run: skipping ? W2.run : W1.run, prop: hasPick ? 'pickaxe' : undefined, pickA, f: Math.round(t * 30), blink: blinkNear(t, moods, 2), sx: lf.sx, sy: lf.sy },
    { flip: faceFlip([skipping ? -1 : 1, 0]) });
  CAM = out.cam = cam([
    { t: 13.5, pos: [7.4, 1.6, 4.0], look: [7.0, 1.5, 0.2], fov: 40 },
    { t: 14.4, pos: [7.6, 1.6, 4.4], look: [7.3, 1.5, 0.2], fov: 40 },
    { t: 15.2, pos: [9.2, 2.0, 7.6], look: [10.6, 1.3, -0.6], fov: 42 },
    { t: 17.9, pos: [9.4, 2.0, 7.2], look: [10.6, 1.3, -0.6], fov: 42 },
    { t: 18.7, pos: [8.6, 3.0, 12.0], look: [8.8, 2.2, 0.0], fov: 46 },
    { t: 21.0, pos: [8.6, 3.0, 12.4], look: [8.8, 1.8, 0.0], fov: 46 },
    { t: 22.6, pos: [7.4, 2.0, 7.8], look: [7.2, 1.4, 0.0], fov: 42 },
  ], t, { creep: 0.03, kicks: [{ t: 19.25, amp: 0.35 }] });
  out.light = 'day'; out.shadow = { center: [9, 0, 0], radius: 12 };
  sunAt(W, 52, 150);
  out.dof = { focus: Math.hypot(CAM.pos[0] - hx, CAM.pos[2] - 0.3), cInf: 6 };
  out.fx.flash = t < 13.6 ? 1 - ramp(t, 13.5, 13.6) : 0;
}

// ---------------- C. sunset; the house slapped together; four walls, a door, no windows; scared; slam ----------------
function shotHouse(W, t, out) {
  const [hx, , hz] = Z.house;
  const dusk = ramp(t, 22.7, 25.0), night = ramp(t, 26.0, 30.0);
  out.lightMix = night > 0 ? ['golden', 'night', smooth(night)] : ['day', 'golden', smooth(dusk)];
  const N = W.houseBlocks.length, t0 = 24.08, t1 = 25.6;
  W.houseBlocks.forEach((b, i) => {
    const land = t0 + (t1 - t0) * i / N;
    if (t < land - 0.2) { b.m.visible = false; return; }
    const u = ramp(t, land - 0.2, land), sq = t > land ? 1 - Math.sin(ramp(t, land, land + 0.14) * Math.PI) * 0.15 : 1;
    b.m.position.set(b.home.x, b.home.y + (1 - easeIn(u)) * 7, b.home.z); b.m.scale.set(1 / sq, sq, 1 / sq);
  });
  const dp = pop(t, 26.45, 0.3);
  W.doorPivot.scale.set(1, Math.max(0.001, dp), 1);
  const open = t > 29.05 && t < 29.55 ? smooth(ramp(t, 29.05, 29.2)) : 0;
  W.doorPivot.rotation.y = -1.7 * open + (t > 29.55 ? Math.sin(ramp(t, 29.55, 29.8) * Math.PI * 3) * 0.05 * (1 - ramp(t, 29.55, 29.8)) : 0);
  const moods = [[0, 'worried'], [24.1, 'determined'], [25.65, 'happy'], [27.2, 'happy'], [28.3, 'worried'], [28.9, 'shock']];
  const Wk = walk(t, 29.15, 29.5, hx + 1.7, hx + 0.5);
  const building = t > 24.0 && t < 25.7;
  let armR = 'hang', armL = 'hang', look = 0;
  if (building) { const b = Math.floor(t * 9) % 2; armR = b ? 'up' : 'point'; armL = b ? 'point' : 'up'; }
  else if (t > 25.65 && t < 26.4) { armR = armL = 'up'; }
  else if (t > 27.2 && t < 28.3) { armR = armL = 'cross'; }
  else if (t > 28.3 && t < 29.15) look = Math.sin((t - 28.3) * 8);
  const lf = life(t, 3);
  if (t < 29.5) setCard(W.hero, [Wk.x, Wk.bob, hz + 2.2],
    { face: moodAt(t, moods), armR, armL, hat: false, look, lookY: t < 23.6 && t > 22.7 ? -0.8 : 0, run: Wk.run, f: Math.round(t * 30), blink: blinkNear(t, moods, 3), sx: lf.sx, sy: lf.sy },
    { flip: faceFlip([-1, 0]) });
  if (t > 29.55 && t < 29.95) setCard(W.puffs[0], [hx + 0.5, 0, hz + 1.4], { t: Math.round(ramp(t, 29.55, 29.95) * 16) / 16, col: '#e8d2aa' }, { blob: false, scale: 0.9 });
  CAM = out.cam = cam([
    { t: 22.6, pos: [hx + 1.0, 1.6, hz + 9.5], look: [hx + 0.6, 1.8, hz - 1.0], fov: 44 },
    { t: 24.0, pos: [hx + 1.0, 2.2, hz + 11.0], look: [hx + 0.3, 2.2, hz - 1.0], fov: 46 },
    { t: 26.4, pos: [hx + 1.2, 2.0, hz + 10.0], look: [hx + 0.4, 1.8, hz - 1.0], fov: 44 },
    { t: 29.0, pos: [hx + 1.6, 1.6, hz + 7.2], look: [hx + 1.0, 1.4, hz + 0.5], fov: 42 },
    { t: 30.45, pos: [hx + 1.4, 1.6, hz + 6.6], look: [hx + 0.6, 1.4, hz + 0.5], fov: 42 },
  ], t, { creep: 0.03, kicks: [{ t: 29.55, amp: 0.12 }] });
  out.shadow = { center: [hx, 0, hz], radius: 12 };
  sunAt(W, lerp(30, -4, ramp(t, 22.6, 25.8)), 230);
  nightSky(W, smooth(ramp(t, 27.0, 30.0)));
  out.dof = { focus: Math.hypot(CAM.pos[0] - (hx + 1), CAM.pos[2] - (hz + 1)), cInf: 5 };
}

// ---------------- D. inside: you made it; into bed; push to the one gap; two white eyes ----------------
function shotBed(W, t, out) {
  const [rx, , rz] = Z.room;
  W.torchLight.intensity = 9 + Math.sin(t * 13) * 0.8 + Math.sin(t * 7.3) * 0.6;
  W.flame.scale.set(1, 1 + 0.15 * Math.sin(t * 17), 1);
  const moods = [[0, 'neutral'], [30.5, 'happy'], [32.1, 'tired'], [37.35, 'shock']];
  const lf = life(t, 4);
  const climb = smoother(ramp(t, 31.6, 32.3));
  if (t < 31.6) {
    const j = pop(t, 30.55, 0.3);
    setCard(W.hero, [rx - 0.4, Math.sin(ramp(t, 30.5, 30.85) * Math.PI) * 0.35, rz - 0.2],
      { face: moodAt(t, moods), armR: j > 0.3 ? 'up' : 'hang', armL: j > 0.3 ? 'up' : 'hang', hat: false, f: Math.round(t * 30), blink: blinkNear(t, moods, 4), sx: lf.sx, sy: lf.sy }, {});
  } else {
    const bx = W.bed.position.x, bz = W.bed.position.z;
    setCard(W.hero, [lerp(rx - 0.4, bx + 1.0, climb), lerp(0, 0.95, climb), lerp(rz - 0.2, bz + 0.05, climb)],
      { face: moodAt(t, moods), armR: 'hang', armL: 'hang', hat: false, lookY: t > 37.35 ? -0.5 : 0, look: t > 37.35 ? 0.7 : 0, f: Math.round(t * 30),
        blink: (t > 32.4 && t < 37.3) || blinkNear(t, moods, 4) }, { lean: climb * 1.5708, blob: false });
    if (climb > 0.7) { W.blanket.position.set(bx + 0.45, 0.85, bz + 0.05); W.blanket.scale.set(1, 1, 1); }
  }
  // the eyes in the gap: Herobrine stands outside, lit only by his own eyes
  const eyes = smooth(ramp(t, 35.6, 36.3));
  if (eyes > 0) setCard(W.hb, [W.gap[0] + 0.5, W.gap[1] + 0.5 - 1.28, W.gap[2] - 0.6], { face: 'determined', hat: false, glowEyes: true, f: Math.round(t * 30), blink: t > 37.0 && t < 37.07 }, { noTint: true, tint: eyes, blob: false });
  CAM = out.cam = cam([
    { t: 30.45, pos: [rx + 0.4, 1.8, rz + 3.2], look: [rx - 0.6, 1.4, rz - 1.5], fov: 46 },
    { t: 32.3, pos: [rx + 0.2, 2.0, rz + 3.0], look: [rx - 1.2, 1.2, rz - 1.6], fov: 46 },
    { t: 32.95, pos: [rx + 0.4, 2.2, rz + 2.8], look: [rx - 0.6, 1.8, rz - 2.0], fov: 46 },
    { t: 35.1, pos: [rx + 2.3, 3.3, rz + 0.2], look: [W.gap[0] + 0.5, W.gap[1] + 0.5, rz - 3], fov: 40 },
    { t: 36.9, pos: [rx + 2.4, 3.4, rz - 0.6], look: [W.gap[0] + 0.5, W.gap[1] + 0.5, rz - 3], fov: 38 },
    { t: 37.25, pos: [rx + 0.6, 2.0, rz + 3.4], look: [rx - 1.4, 1.3, rz - 1.6], fov: 48, ease: easeOut },
    { t: 38.35, pos: [rx + 0.6, 2.0, rz + 3.2], look: [rx - 1.4, 1.3, rz - 1.6], fov: 48 },
  ], t, { creep: 0.015 });
  out.light = 'room'; out.shadow = { center: [rx, 0, rz], radius: 8 };
  out.dof = t > 33.5 && t < 37.2 ? { focus: Math.hypot(CAM.pos[0] - (W.gap[0] + 0.5), CAM.pos[2] - (rz - 3)), cInf: 9 } : { focus: 4, cInf: 6 };
}

// ---------------- E. "Herobrine." ----------------
function shotHb(W, t, out) {
  const [hx, , hz] = Z.house;
  W.doorPivot.rotation.y = 0;
  setCard(W.hb, [hx - 0.4, 0, hz + 2.6], { face: 'determined', hat: false, glowEyes: true, f: Math.round(t * 30) }, { noTint: true, tint: 0.85, lean: 0.04 * smooth(ramp(t, 38.9, 39.6)) });
  CAM = out.cam = cam([{ t: 38.35, pos: [hx - 0.38, 1.36, hz + 4.3], look: [hx - 0.4, 1.3, hz + 2.6], fov: 34 }, { t: 39.7, pos: [hx - 0.38, 1.36, hz + 4.05], look: [hx - 0.4, 1.3, hz + 2.6], fov: 32 }], t, { creep: 0.01 });
  out.light = 'dark'; out.shadow = { center: [hx, 0, hz], radius: 8 };
  nightSky(W, 1);
  out.dof = { focus: 1.3, cInf: 10 };
  out.fx.flash = t < 38.45 ? 1 - ramp(t, 38.35, 38.45) : 0;
}

// ---------------- F. "The guy the game swears it removed." - he tears up the update notes ----------------
function shotNotes(W, t, out) {
  const [hx, , hz] = Z.house;
  const tear = smooth(ramp(t, 41.3, 41.55));
  setCard(W.hb, [hx - 0.4, 0, hz + 2.6], { face: 'determined', hat: false, glowEyes: true, armR: 'paper', armL: 'paper', f: Math.round(t * 30) }, { noTint: true, tint: 0.85, lean: -0.1 * smooth(ramp(t, 41.55, 41.9)) });
  const nx = hx - 0.4, ny = 0.82, nz = hz + 2.95;
  W.noteL.position.set(nx - tear * 0.35, ny - tear * 0.25, nz); W.noteL.rotation.set(0, 0, tear * 0.5);
  W.noteR.position.set(nx + tear * 0.35, ny - tear * 0.25, nz); W.noteR.rotation.set(0, 0, -tear * 0.5);
  CAM = out.cam = cam([{ t: 39.7, pos: [hx - 0.2, 1.2, hz + 6.0], look: [hx - 0.4, 1.05, hz + 2.6], fov: 42 }, { t: 41.95, pos: [hx - 0.25, 1.2, hz + 5.6], look: [hx - 0.4, 1.08, hz + 2.6], fov: 40 }], t, { creep: 0.01 });
  out.light = 'dark'; out.shadow = { center: [hx, 0, hz], radius: 8 };
  nightSky(W, 1);
  out.dof = { focus: 2.9, cInf: 8 };
  out.fx.fade = t >= 41.95 ? 1 : 0;
}

const BY = { tree: shotTree, mine: shotMine, house: shotHouse, bed: shotBed, hb: shotHb, notes: shotNotes };
export function applyFrame(f, W) {
  const t = f / FPS, s = shotAt(t);
  for (let pass = 0; pass < 2; pass++) {             // pass 1 finds the camera; pass 2 faces the cards with it
    hideAll(W);
    const out = { cam: null, light: 'day', fx: {}, dof: { cInf: 0 } };
    BY[s.name](W, t, out);
    if (pass === 1) return out;
  }
}
