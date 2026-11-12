// Seven long shots timed to the narration (seconds; word times in work/words.json). Every change is eased: moods
// switch inside a blink, things appear with squash-and-pop, actions have anticipation -> move -> overshoot -> settle.
const SHOTS = [];
const S = (start, end, tr, cam, draw, extra = {}) => SHOTS.push(Object.assign({ start, end, tr, cam, draw }, extra));
const GY = 1450;                                        // top of the ground row (feet level)
const HERO = { gear: { hairTop: '#6a3a22', cowlick: true }, tunic: '#f2b632' };
const HERO_S = 1.1;
const STEP = 330;                                        // stride length (two steps) at s = 1.1, so feet stay planted

// walking with planted feet: position, leg/arm phase and bob all come from the distance travelled
function walker(t, t0, t1, x0, x1, s = HERO_S) {
  const u = ease(ramp(t, t0, t1)), x = lerp(x0, x1, u);
  const ph = (x - x0) / (STEP * s / HERO_S) * Math.PI * 2;
  const moving = t > t0 && t < t1;
  const v = (lerp(x0, x1, ease(ramp(t + 0.02, t0, t1))) - x) / 0.02;
  return { x, legs: moving ? walkLegs(ph, 0.42) : [[-0.12, 0.02], [0.12, -0.02]], arms: moving ? walkArms(ph, 0.45) : null,
           bob: moving ? -Math.abs(Math.sin(ph)) * 10 : 0, v };
}
const walkLegs = (ph, amp = 0.45) => [[Math.sin(ph) * amp, Math.max(0, -Math.sin(ph)) * 0.55], [-Math.sin(ph) * amp, Math.max(0, Math.sin(ph)) * 0.55]];
const walkArms = (ph, amp = 0.5) => [[-Math.sin(ph) * amp - 0.25, -0.25], [Math.sin(ph) * amp + 0.25, 0.25]];
// a blink window around every mood change, so expressions never snap
function moodAt(t, keys) { let m = keys[0][1]; for (const [k, v] of keys) if (t >= k) m = v; return m; }
function blinkNear(t, keys, w = 0.06) { for (const [k] of keys) if (k > 0 && Math.abs(t - k) < w) return true; return ((t * 60 + 13) % 230) < 6; }
// springy follow-through for the cowlick: driven by velocity and by impulses (punch, landing, scare)
function sway(v, t, kicks = []) { let s = clamp(-v * 0.0012, -0.6, 0.6); for (const k of kicks) if (t > k) s += Math.sin((t - k) * 22) * Math.exp(-(t - k) * 6) * 0.5; return s + Math.sin(t * 2.3) * 0.05; }
function pop(t, at, len = 0.28) { return t < at ? 0 : eBack(ramp(t, at, at + len), 2.4); }
function pickaxe(c, x, y, a, s = 1) {
  withT(c, x, y, a, s, () => {
    rrect(c, -8, -10, 150, 20, 8); fs(c, '#8a5a36', 7);
    c.beginPath(); c.moveTo(120, -70); c.quadraticCurveTo(175, 0, 120, 70); c.lineTo(140, 70); c.quadraticCurveTo(200, 0, 140, -70); c.closePath(); fs(c, '#9aa0a8', 7);
  });
}
function stars(c, x, y, t, n = 3) { for (let i = 0; i < n; i++) { const a = t * 6 + i / n * Math.PI * 2; withT(c, x + Math.cos(a) * 60, y + Math.sin(a) * 22, a, 1, () => { poly(c, [[0, -16], [5, -5], [16, -4], [7, 3], [10, 15], [0, 8], [-10, 15], [-7, 3], [-16, -4], [-5, -5]]); fs(c, '#ffe14d', 4); }); } }
function sweat(c, x, y, a) { if (a <= 0) return; c.save(); c.globalAlpha = a; c.beginPath(); c.moveTo(x, y - 26); c.quadraticCurveTo(x + 20, y, x, y + 12); c.quadraticCurveTo(x - 20, y, x, y - 26); fs(c, '#8fd3ff', 5); c.restore(); }
function notes(c, x, y, t) { for (let i = 0; i < 3; i++) { const u = (t * 0.8 + i / 3) % 1; c.save(); c.globalAlpha = 1 - u; const nx = x + u * 120 + Math.sin(u * 8) * 15, ny = y - u * 160; ell(c, nx, ny, 14, 10, -0.4); c.fillStyle = INK; c.fill(); line(c, [[nx + 12, ny], [nx + 12, ny - 42]], 5); c.restore(); } }
function hero(c, o) { return stick(c, Object.assign({ ...HERO, s: HERO_S }, o)); }

// ---------------- A. 0.00-13.50 wake up, no tools, no food, the clock; walk to the tree, punch it, floating top ----
S(0.0, 13.50, 'whip', [
  [0, [430, 1080, 1.35, 0]], [2.3, [430, 1040, 1.15, 0]], [4.3, [470, 1000, 1.05, 0]], [5.3, [600, 700, 1.0, 0]], [6.4, [620, 760, 1.0, 0]],
  [7.0, [700, 1000, 1.05, 0]], [8.2, [720, 1030, 1.08, 0]], [8.9, [690, 1050, 1.32, 0]], [9.6, [700, 1020, 1.12, 0]], [10.8, [700, 960, 1.0, 0]], [11.9, [760, 760, 0.95, 0]], [13.5, [740, 800, 0.95, 0]]
], (c, t) => {
  const T = t;
  // sky dims a touch as the ten-minute clock runs
  skyGrad(c, '#55b8ff', '#c9ecff');
  blockCloud(c, 120 + T * 8, 330, 1.2); blockCloud(c, 760 + T * 5, 460, 0.9);
  // the sun with a draining clock wedge
  const clockOn = ease(ramp(T, 4.45, 4.9));
  squareSun(c, 640, 330, 1.0);
  if (clockOn > 0) { c.save(); c.globalAlpha = clockOn; const frac = 1 - ramp(T, 4.8, 13.4) * 0.35;
    circ(c, 640, 330, 125); c.lineWidth = 16; c.strokeStyle = INK; c.stroke();
    c.beginPath(); c.arc(640, 330, 125, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * frac); c.lineWidth = 10; c.strokeStyle = '#ffffff'; c.stroke(); c.restore(); }
  ground(c, GY);
  // the tree: logs pop out one at a time (bottom first); leaves stay floating
  const pops = [9.70, 10.12, 10.38, 10.62];
  const logsLeft = 4 - pops.filter(p => T >= p).length;
  const crack = T >= 7.2 && T < 9.7 ? ramp(T, 7.2, 9.6) : 0;
  tree(c, 840, GY, logsLeft, { crackRow: 4 - logsLeft, crack: logsLeft === 4 ? crack : 0.6, leafDy: Math.sin(T * 1.5) * (logsLeft === 0 ? 4 : 0) });
  // popped logs: hop out, bounce, then zip into his pocket
  pops.forEach((p, i) => {
    if (T < p) return;
    const u = T - p, row = 3 - i, sx = 840 + 55, sy = GY - (4 - row) * BS + 55;
    if (u < 0.55) { const x = sx - u * 160, y = sy - Math.sin(Math.min(1, u / 0.55) * Math.PI) * 120 + u * 140; miniBlock(c, 'log', x, Math.min(y, GY - 30), 50, T, 1); }
    else if (u < 0.85) { const v = ease((u - 0.55) / 0.3); miniBlock(c, 'log', lerp(sx - 88, 690, v), lerp(GY - 30, GY - 230, v), 50 * (1 - v * 0.8), T); }
  });
  // hero: wakes lying down, gets up, pats pockets, tummy rumbles, looks at the sun, walks to the tree, punches
  const W1 = walker(T, 6.55, 7.05, 330, 700);
  const moodKeys = [[0, 'sleepy'], [0.62, 'shock'], [2.55, 'worried'], [3.5, 'sad'], [4.5, 'scared'], [6.55, 'determined'], [8.27, 'yell'], [9.72, 'grin'], [11.05, 'o'], [12.55, 'flat']];
  const mood = moodAt(T, moodKeys);
  const wake = eBack(ramp(T, 0.25, 0.9), 1.6);
  const rot = lerp(1.57, 0, wake);
  let arms = W1.arms, look = 0, lookY = 0, lean = 0;
  if (T < 2.4) { look = T > 1.0 ? Math.sin((T - 1.0) * 4) : 0; arms = [[-0.4, -0.2], [0.4, 0.2]]; }
  else if (T < 3.4) { arms = [[-0.55, 1.4], [0.55, -1.4]]; look = -0.3; lookY = 0.6; }             // patting empty pockets
  else if (T < 4.4) { arms = [[-0.15, 1.6], [0.15, -1.6]]; lookY = 0.7; }                           // hugging the rumbling tummy
  else if (T < 6.5) { look = 0.6; lookY = -1; arms = [[-0.4, -0.3], [0.4, 0.3]]; }                  // the sun / clock
  if (T >= 7.05 && T < 10.8) {                                                                       // punching
    const k = (T - 7.12) / 0.26, ph = k - Math.floor(k);
    const ext = T < 7.12 ? -ease(ramp(T, 7.0, 7.12)) * 0.4 : (ph < 0.35 ? eOut(ph / 0.35) : 1 - ease((ph - 0.35) / 0.65));
    arms = [[-0.3, -0.4], [lerp(0.6, 1.62, ext), lerp(0.9, -0.05, ext)]]; look = 1; lean = 0.08 * ext;
  }
  if (T >= 10.8) { look = T < 12.5 ? 0.5 : 0; lookY = T < 12.5 ? -1 : 0; arms = T > 12.6 ? [[-1.2 - pop(T, 12.6) * 0.3, -1.4], [1.2 + pop(T, 12.6) * 0.3, 1.4]] : [[-0.4, -0.2], [0.4, 0.2]]; }
  const W3 = walker(T, 10.75, 11.3, 700, 470);
  const hx = T < 6.55 ? 330 : (T < 10.75 ? W1.x : W3.x);
  const kicks = [0.9, 7.25, 7.51, 7.77, 8.03, 8.29, 8.55, 8.81, 9.07, 9.33, 9.7, 12.6];
  withT(c, hx, GY, rot, 1, () => {
    hero(c, { x: 0, y: T < 10.75 ? W1.bob : W3.bob, t: T, mood, look, lookY, lean, arms: (T > 10.75 && T < 11.3) ? W3.arms : arms, legs: T < 0.9 ? [[-0.1, 0], [0.1, 0]] : (T < 10.75 ? W1.legs : W3.legs), blink: blinkNear(T, moodKeys) || T < 0.2, sway: sway(W1.v, T, kicks), shadow: rot > -0.2 });
  });
  // tummy rumble lines and empty-pocket flaps
  if (T > 3.55 && T < 4.4) for (let i = 0; i < 3; i++) { const a = (T * 9 + i) % 1; c.save(); c.globalAlpha = 1 - a; c.beginPath(); c.arc(hx, GY - 230, 60 + a * 50, -0.6 + i, 0.2 + i); c.lineWidth = 6; c.strokeStyle = INK; c.stroke(); c.restore(); }
  if (T > 2.6 && T < 3.6) { const p = pop(T, 2.6); for (const s of [-1, 1]) withT(c, hx + s * 62, GY - 235, s * 0.3, p, () => { rrect(c, -20, 0, 40, 46, 8); fs(c, '#ffffff', 6); }); }
  // "bare-handed": stars around the fist
  if (T > 8.3 && T < 9.6) stars(c, hx + 170, GY - 300, T, 3);
}, { motion: 1 });

// ---------------- B. 13.50-22.60 craft a pickaxe, mine the mountain, 64 blocks, 150 tonnes, skip away ----------------
S(13.50, 22.60, 'whip', [
  [0, [420, 1020, 1.25, 0]], [0.9, [450, 1000, 1.18, 0]], [1.9, [960, 1000, 0.92, 0]], [4.4, [960, 1000, 0.95, 0]],
  [5.2, [820, 900, 0.88, 0]], [7.4, [840, 900, 0.88, 0]], [9.1, [980, 960, 0.95, 0]]
], (c, lt, t) => {
  const T = t;
  skyGrad(c, '#55b8ff', '#c9ecff'); blockCloud(c, 300 + T * 6, 360, 1.1); squareSun(c, 160, 300, 0.8);
  // the mountain: a stepped heap of stone; mined blocks disappear in order (a tunnel into its side)
  const mtn = [];
  for (let row = 0; row < 5; row++) for (let col = 0; col < 6 - row; col++) mtn.push([900 + (col + row * 0.5) * BS, GY - (row + 1) * BS, row, col]);
  const mineStart = 15.0, mineEnd = 17.85, rate = 64 / (mineEnd - mineStart);
  const mined = Math.floor(clamp((T - mineStart) * rate, 0, 64));
  const order = mtn.map((b, i) => [b, Math.abs(b[2] - 1.2) * 3 + b[3]]).sort((a, b) => a[1] - b[1]).map(e => e[0]);
  const gone = new Set(order.slice(0, Math.min(mined * 0.2 | 0, order.length - 6)));
  ground(c, GY);
  for (const b of mtn) if (!gone.has(b)) block(c, b[2] === 4 ? 'grass' : 'stone', b[0], b[1], 1, { seed: b[2] * 9 + b[3] });
  // crafting: four planks fly together and become a pickaxe
  const craft = ramp(T, 13.55, 13.95), hasPick = T >= 13.95;
  const hx0 = 420;
  if (!hasPick) for (let i = 0; i < 4; i++) { const a = i / 4 * Math.PI * 2 + T * 6; miniBlock(c, 'planks', hx0 + 120 + Math.cos(a) * 140 * (1 - craft), GY - 480 + Math.sin(a) * 90 * (1 - craft), 46, T); }
  if (T > 13.9 && T < 14.25) burst(c, hx0 + 120, GY - 480, 160, ramp(T, 13.9, 14.25), '#ffffff');
  // hero walks to the mountain then swings
  const W1 = walker(T, 14.35, 15.0, hx0, 760);
  const mining = T >= 15.0 && T < 18.1;
  const k = (T - 15.0) / 0.3, ph = k - Math.floor(k);
  const swing = mining ? (ph < 0.25 ? -ease(ph / 0.25) * 0.5 : ph < 0.45 ? lerp(-0.5, 1, eOut((ph - 0.25) / 0.2)) : 1 - ease((ph - 0.45) / 0.55)) : 0;
  const W2 = walker(T, 21.05, 22.6, 760, 1300);
  const skipping = T >= 21.05;
  const hx = skipping ? W2.x : W1.x;
  const moodKeys = [[0, 'o'], [13.98, 'grin'], [15.0, 'determined'], [18.2, 'flat'], [19.4, 'o'], [20.0, 'flat'], [21.1, 'happy']];
  let arms = W1.arms || [[-0.4, -0.3], [0.4, 0.3]];
  if (T < 14.35) arms = [[-1.6 + craft * 0.5, -0.6], [1.6 - craft * 0.5, 0.6]];
  if (mining) arms = [[-0.4, -0.3], [lerp(2.6, 1.0, (swing + 0.5) / 1.5), lerp(0.4, -0.2, (swing + 0.5) / 1.5)]];
  if (skipping) arms = [[-0.6, -0.3], [2.6, 0.9]];
  const r = hero(c, { x: hx, y: GY + (skipping ? W2.bob * 2.2 : W1.bob), t: T, mood: moodAt(T, moodKeys), look: T > 19.3 && T < 20.1 ? 1 : (skipping ? 0.6 : 1), lookY: T > 19.3 && T < 20.1 ? -0.4 : 0,
    arms, legs: skipping ? W2.legs : W1.legs, blink: blinkNear(T, moodKeys), sway: sway(skipping ? W2.v : W1.v, T, [13.95, 19.35]) });
  if (hasPick) { const hand = r.hands[1]; const pa = mining ? lerp(-2.4, 0.3, (swing + 0.5) / 1.5) : (skipping ? -2.2 : -0.6); pickaxe(c, hand[0], hand[1], pa, pop(T, 13.95)); }
  // mined blocks pop out and zip into his pocket
  if (mining) for (let j = 0; j < 3; j++) { const u = ((T - 15.0) / 0.3 + j / 3) % 1; const sx = 900, sy = GY - 2 * BS + 40; miniBlock(c, 'stone', lerp(sx, hx + 40, ease(u)), lerp(sy, GY - 240, ease(u)) - Math.sin(u * Math.PI) * 140, 46 * (1 - u * 0.7), T); }
  if (mining && ph > 0.42 && ph < 0.6) burst(c, 905, GY - 160, 90, (ph - 0.42) / 0.18, '#d8dade');
  // the item counter
  const cnt = Math.min(64, Math.max(1, Math.round((T - mineStart) * rate)));
  if (T > 15.05 && T < 21.0) slot(c, 980, 260, 'stone', cnt, 1.05, pop(T, 15.05) * (T > 15.8 && T < 16.0 ? 1.12 : 1));
  // 150 tonnes: a giant weight drops beside him, the ground shakes; he doesn't notice
  if (T > 18.6) {
    const fall = ramp(T, 18.6, 19.25), wy = lerp(-600, GY, eIn(fall)), sq = T > 19.25 ? 1 - Math.sin(ramp(T, 19.25, 19.5) * Math.PI) * 0.15 : 1;
    withT(c, 560, wy, 0, 1, () => { c.scale(1 / sq, sq);
      poly(c, [[-210, 0], [210, 0], [160, -320], [-160, -320]]); fs(c, '#3d4250', 10);
      rrect(c, -70, -400, 140, 100, 40); c.lineWidth = 34; c.strokeStyle = INK; c.stroke(); c.lineWidth = 20; c.strokeStyle = '#3d4250'; c.stroke();
      c.font = '700 110px Poppins'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillStyle = '#ffffff'; c.fillText('150 t', 0, -190); });
    if (T > 19.25) { burst(c, 560, GY - 10, 260, ramp(T, 19.25, 19.7), '#e8d2aa'); }
  }
  if (skipping) notes(c, hx + 60, GY - 520, T);
}, { motion: 1, shakes: [[19.25, 22]] });

// ---------------- C. 22.60-30.45 sunset; slap together a house; four walls, a door, no windows; scared, slam -------
S(22.60, 30.45, 'cut', [[0, [560, 900, 1.0, 0]], [1.4, [560, 960, 1.0, 0]], [5.5, [560, 1000, 1.08, 0]], [7.85, [560, 1060, 1.18, 0]]], (c, lt, t) => {
  const T = t;
  const dusk = ease(ramp(T, 22.7, 25.0)), night = ease(ramp(T, 26.0, 30.0));
  const top = night > 0 ? mixHex('#ff8a4c', '#26204a', night) : mixHex('#55b8ff', '#ff8a4c', dusk);
  const bot = night > 0 ? mixHex('#ffd08a', '#5a3a6a', night) : mixHex('#c9ecff', '#ffd08a', dusk);
  skyGrad(c, top, bot);
  squareSun(c, 820, lerp(320, 1300, ease(ramp(T, 22.65, 25.5))), 1.0, '#ffb347');
  if (night > 0.3) { c.save(); c.globalAlpha = ease(ramp(night, 0.3, 1)); squareMoon(c, 220, 320, 0.9); for (let i = 0; i < 20; i++) { rrect(c, hash(i) * 1080, hash(i * 3) * 700 + 80, 8, 8, 1); c.fillStyle = '#fff'; c.fill(); } c.restore(); }
  ground(c, GY, -1400, 2600, 'grass', 'dirt', night * 0.45);
  // the house: 5 wide, 4 tall walls (door gap in the middle, bottom two rows), cobble frame, plank fill; a roof row
  const cells = [];
  for (let row = 0; row < 4; row++) for (let col = 0; col < 5; col++) { if (col === 2 && row < 2) continue; cells.push([col, row]); }
  for (let col = -1; col < 6; col++) cells.push([col, 4]);
  const bx = 285, t0 = 24.08, t1 = 25.6;
  cells.forEach(([col, row], i) => {
    const land = t0 + (t1 - t0) * i / cells.length;
    if (T < land - 0.18) return;
    const u = ramp(T, land - 0.18, land), sq = T > land ? 1 + Math.sin(ramp(T, land, land + 0.15) * Math.PI) * 0.12 : 1;
    const x = bx + col * BS, y = lerp(GY - 1400, GY - (row + 1) * BS, eIn(u));
    const kind = row === 4 ? 'cobble' : (col === 0 || col === 4 || row === 3 ? 'cobble' : 'planks');
    c.save(); c.translate(x + BS / 2, y + BS); c.scale(1 / sq, sq); block(c, kind, -BS / 2, -BS, 1, { shade: night * 0.4, seed: i }); c.restore();
  });
  // the door pops in
  const dp = pop(T, 26.45, 0.3), shut = T > 29.55 ? 0 : (T > 29.2 ? 1 - ease(ramp(T, 29.2, 29.55)) : 0);
  if (dp > 0) withT(c, bx + 2 * BS, GY - 2 * BS, 0, 1, () => { c.translate(0, 2 * BS); c.scale(1, dp); c.translate(0, -2 * BS); door(c, 0, 0, 1, shut); });
  // the hero: building (arms pumping), then proud, then nervous, then dashes in and slams the door
  const moodKeys = [[0, 'worried'], [24.1, 'determined'], [25.65, 'happy'], [27.2, 'smug'], [28.3, 'worried'], [28.9, 'scared']];
  const building = T > 24.0 && T < 25.7;
  const W1 = walker(T, 29.15, 29.5, 120, bx + 2.5 * BS);
  const inside = T > 29.5;
  let arms = [[-0.4, -0.3], [0.4, 0.3]], look = 0;
  if (building) { const b = Math.sin(T * 26); arms = [[-1.8 + b * 0.5, -0.4], [1.8 - b * 0.5, 0.4]]; }
  else if (T > 27.2 && T < 28.3) arms = [[0.9, -1.9], [-0.9, 1.9]];
  else if (T > 28.3) look = Math.sin((T - 28.3) * 8);
  if (!inside) hero(c, { x: T < 29.15 ? 120 : W1.x, y: GY + W1.bob, t: T, mood: moodAt(T, moodKeys), look, lookY: T > 22.7 && T < 23.6 ? -0.8 : 0, arms, legs: W1.legs,
    blink: blinkNear(T, moodKeys), sway: sway(W1.v, T, [25.65, 28.9]) });
  sweat(c, 210, GY - 520, ramp(T, 28.9, 29.1));
  if (T > 29.55 && T < 30.0) { burst(c, bx + 2.5 * BS, GY - 120, 170, ramp(T, 29.55, 29.95), '#ffffff'); }
}, { motion: 1, shakes: [[29.55, 14]] });

// ---------------- D. 30.45-38.35 inside: made it, into bed; push to the one gap; two white eyes ---------------------
S(30.45, 38.35, 'cut', [[0, [540, 1020, 1.05, 0]], [1.9, [560, 1040, 1.1, 0]], [2.5, [600, 1000, 1.12, 0]], [4.6, [735, 935, 1.75, 0]],
  [6.85, [745, 925, 2.05, 0]], [7.1, [480, 1060, 1.1, 0]], [7.9, [480, 1060, 1.12, 0]]], (c, lt, t) => {
  const T = t;
  ctx_interior(c, T);
  // the gap: one missing block in the back wall, high on the right
  const gx = 680, gy = GY - 5 * BS;
  rrect(c, gx, gy, BS, BS, 2); fs(c, '#0b0e1c', 6);
  const eyes = ease(ramp(T, 35.6, 36.3));
  if (eyes > 0) { c.save(); c.beginPath(); c.rect(gx, gy, BS, BS); c.clip();
    circ(c, gx + 55, gy + 70, 70); c.fillStyle = '#20232e'; c.fill();
    for (const sx of [-1, 1]) { glow(c, gx + 55 + sx * 22, gy + 62, 60, 'rgba(255,255,255,A)', 0.7 * eyes); ell(c, gx + 55 + sx * 22, gy + 62, 12, 8 * (T > 37.0 && T < 37.08 ? 0.15 : 1)); c.fillStyle = `rgba(255,255,255,${eyes})`; c.fill(); }
    c.restore(); }
  // bed and the hero
  bed(c, 170, GY - 0.55 * BS * 2.3, 2.3);
  const moodKeys = [[0, 'flat'], [30.5, 'happy'], [32.1, 'sleepy'], [37.35, 'scared']];
  const climb = ease(ramp(T, 31.6, 32.3));
  if (T < 31.6) {
    const j = pop(T, 30.55, 0.3);
    hero(c, { x: 480, y: GY - Math.sin(ramp(T, 30.5, 30.85) * Math.PI) * 60, t: T, mood: moodAt(T, moodKeys), arms: [[-2.6 * j - 0.3, -0.3], [2.6 * j + 0.3, 0.3]], blink: blinkNear(T, moodKeys), sway: sway(0, T, [30.85]) });
  } else {
    // lying in bed (rotated), blanket over the body
    const lie = climb;
    withT(c, lerp(480, 690, lie), lerp(GY, GY - 1.05 * BS, lie), lerp(0, -1.5708, lie), 1, () =>
      hero(c, { x: 0, y: 0, t: T, mood: moodAt(T, moodKeys), lookY: T > 37.35 ? -0.6 : 0, look: T > 37.35 ? 0.7 : 0, blink: T > 32.4 && T < 37.3 || blinkNear(T, moodKeys), shadow: false, arms: [[-0.3, -0.2], [0.3, 0.2]], sway: sway(0, T, [37.35]) }));
    if (lie > 0.6) { c.save(); c.globalAlpha = ease(ramp(lie, 0.6, 1)); rrect(c, 330, GY - 1.45 * BS, 3.3 * BS, 0.62 * BS, 14); fs(c, '#d23a3a', 7); c.restore(); }
    if (T > 32.4 && T < 35.3) { c.save(); c.globalAlpha = 0.8; c.font = '700 54px Poppins'; c.fillStyle = '#ffffff'; c.strokeStyle = INK; c.lineWidth = 8;
      for (let i = 0; i < 3; i++) { const u = (T * 0.6 + i / 3) % 1; c.globalAlpha = 0.8 * (1 - u); c.strokeText('z', 260 + u * 90 + i * 10, GY - 330 - u * 160); c.fillText('z', 260 + u * 90 + i * 10, GY - 330 - u * 160); } c.restore(); }
    if (T > 37.4) { sweat(c, 250, GY - 300, ramp(T, 37.4, 37.6)); }
  }
}, { motion: 1, musicCut: 35.6 });
function ctx_interior(c, T) {
  // back wall of planks, a cobble floor line, torch light
  for (let row = 0; row < 12; row++) for (let col = -3; col < 12; col++) block(c, 'planks', col * BS, GY - (row + 1) * BS, 1, { shade: 0.35, seed: row * 7 + col });
  for (let col = -3; col < 12; col++) { block(c, 'cobble', col * BS, GY, 1, { shade: 0.2 }); for (let k = 1; k < 6; k++) block(c, 'stone', col * BS, GY + k * BS, 1, { shade: 0.5 }); }
  torch(c, 160, GY - 3.2 * BS, T, 1.1);
  const g = c.createRadialGradient(160, GY - 3.6 * BS, 50, 160, GY - 3.6 * BS, 1300); g.addColorStop(0, 'rgba(255,170,80,0.18)'); g.addColorStop(1, 'rgba(10,10,30,0.45)');
  c.fillStyle = g; c.fillRect(-400, -400, 2000, 2600);
}

// ---------------- E. 38.35-39.70 "Herobrine." ------------------------------------------------------------------
S(38.35, 39.70, 'cut', [[0, [540, 880, 2.6, 0]], [1.35, [540, 870, 3.0, 0.02]]], (c, lt, t) => {
  const T = t;
  skyGrad(c, '#05060d', '#14182a');
  for (let i = 0; i < 30; i++) { rrect(c, hash(i) * 1080, hash(i * 3) * 900, 6, 6, 1); c.fillStyle = 'rgba(255,255,255,0.6)'; c.fill(); }
  ground(c, GY, -1400, 2600, 'grass', 'dirt', 0.75);
  stick(c, { x: 540, y: GY, s: 1.1, t: T, headCol: '#262a36', glowEyes: 0.7 + 0.3 * ease(ramp(T, 38.4, 38.6)), headTilt: 0.05 * ease(ramp(T, 38.9, 39.6)), tunic: '#2d6a8a', arms: [[-0.2, -0.1], [0.2, 0.1]], shadow: false });
}, { motion: 1, sat: 0.6 });

// ---------------- F. 39.70-42.05 "The guy the game swears it removed." -------------------------------------------
S(39.70, 42.20, 'cut', [[0, [560, 1020, 1.25, 0]], [2.3, [560, 1000, 1.38, 0]]], (c, lt, t) => {
  const T = t;
  skyGrad(c, '#0b0e1c', '#23284a');
  squareMoon(c, 860, 360, 0.9);
  ground(c, GY, -1400, 2600, 'grass', 'dirt', 0.55);
  for (let row = 0; row < 4; row++) for (let col = 0; col < 3; col++) block(c, 'cobble', 820 + col * BS, GY - (row + 1) * BS, 1, { shade: 0.5 });
  const tear = ease(ramp(T, 41.3, 41.55));
  const r = stick(c, { x: 470, y: GY, s: 1.1, t: T, headCol: '#262a36', glowEyes: 1, headTilt: 0.12 * ease(ramp(T, 41.55, 41.9)), tunic: '#2d6a8a',
    arms: [[1.2 - tear * 0.6, -1.0 - tear * 0.4], [-1.2 + tear * 0.6, 1.0 + tear * 0.4]], shadow: true });
  // the notice he holds up (then tears in half on "removed")
  const px = 470, py = GY - 190;
  const halves = tear > 0 ? [-1, 1] : [0];
  for (const h of halves) withT(c, px + h * (20 + tear * 160), py + tear * Math.abs(h) * 200, h * tear * 0.6, 1, () => {
    c.save(); if (h) { c.beginPath(); c.rect(h < 0 ? -220 : 0, -200, 220, 400); c.clip(); }
    rrect(c, -195, -120, 390, 250, 10); fs(c, '#f6f1e3', 8);
    c.font = '700 40px Poppins'; c.textAlign = 'center'; c.fillStyle = '#2b2233'; c.fillText('UPDATE NOTES', 0, -65);
    c.font = '700 30px Poppins'; c.textAlign = 'left'; c.fillStyle = '#4a4458'; c.fillText('- fixed some bugs', -165, -10); c.fillText('- more blocks', -165, 30);
    c.fillStyle = '#c0392b'; c.fillText('- removed Herobrine', -165, 72);
    c.restore();
  });
}, { motion: 1, blackAt: 41.95 });

function mixHex(a, b, t) {
  const pa = [1, 3, 5].map(i => parseInt(a.slice(i, i + 2), 16)), pb = [1, 3, 5].map(i => parseInt(b.slice(i, i + 2), 16));
  return 'rgb(' + pa.map((v, i) => Math.round(lerp(v, pb[i], clamp(t)))).join(',') + ')';
}
