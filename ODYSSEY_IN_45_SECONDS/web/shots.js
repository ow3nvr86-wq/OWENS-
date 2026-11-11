// The shot list, in seconds of the narration (word times from work/words.json). Each shot: start, end, tr (transition
// out: 'whip' or 'cut'), cam keyframes [[lt, [cx, cy, zoom, rot]], ...] and draw(ctx, lt, t).
const SHOTS = [];
const S = (start, end, tr, cam, draw, extra = {}) => SHOTS.push(Object.assign({ start, end, tr, cam, draw }, extra));
const ODY = { gear: { helmet: true, beard: true }, tunic: '#3a7bd5' };
const CREW = [{ gear: { cap: ACC.bronze }, tunic: '#e2403b' }, { gear: { cap: ACC.bronze }, tunic: '#3fbf5a' }, { gear: { cap: ACC.bronze }, tunic: '#f0a030' }];
const walkLegs = (ph, amp = 0.45) => [[Math.sin(ph) * amp, Math.max(0, -Math.sin(ph)) * 0.6], [-Math.sin(ph) * amp, Math.max(0, Math.sin(ph)) * 0.6]];
const walkArms = (ph, amp = 0.5) => [[-Math.sin(ph) * amp, -0.3], [Math.sin(ph) * amp, 0.3]];
const blink = (t, seed = 0) => ((t * 30 + seed * 37) % 97) < 3;
const D = 0.05;   // visuals land a couple of frames before their word

// 1. "He beat a Cyclops," - frame 1 is the lunge with the burning stake
S(0.0, 1.42 - D, 'whip', [[0, [540, 900, 1.18, -0.03]], [1.4, [560, 960, 1.0, 0.0]]], (c, lt) => {
  cave(c, lt);
  const hit = lt >= 0.5;
  const shake = hit ? decay(lt, 0.5, 5) * 18 : 0;
  cyclopsEye(c, 870 + Math.sin(lt * 50) * shake, 640, 430, lt, { blink: hit && lt < 1.2, mouth: hit ? 1 : 0.2, angry: true, look: -0.6 });
  if (hit) { burst(c, 680, 620, 260, ramp(lt, 0.5, 0.95)); }
  const px = lerp(150, 330, eOut(ramp(lt, 0, 0.5))) - (hit ? eOut(ramp(lt, 0.5, 0.8)) * 40 : 0);
  stick(c, { ...ODY, x: px, y: 1560, s: 1.3, t: lt, mood: hit ? 'grin' : 'yell', look: 1, lean: hit ? 0.15 : 0.32,
    legs: [[-0.55, 0.2], [0.55, -0.1]], arms: [[1.85, 0.15], [2.05, 0.05]], props: { r: 'stake' } });
});
// 2. "a witch" - a green bolt flies over him as he ducks
S(1.42 - D, 2.12 - D, 'whip', [[0, [540, 980, 1.05, 0.02]], [0.7, [540, 960, 1.0, 0]]], (c, lt) => {
  sky(c, '#5b2a8a', '#ff8fc8'); grassBeach(c, 1580, '#7a4fb0');
  for (const x of [120, 960]) { rrect(c, x - 45, 500, 90, 1080, 6); fs(c, '#efe0ff', 9); }
  const r = stick(c, { x: 820, y: 1560, s: 1.15, t: lt, mood: 'evil', look: -1, dress: ACC.circe, gear: { hair: ACC.circe, crown: true },
    arms: [[-1.9, -0.2], [0.4, 0.2]], props: { l: 'wand' } });
  const tip = [r.hands[0][0] - 150, r.hands[0][1] - 10];
  const bx = lerp(tip[0], -100, eIn(ramp(lt, 0.05, 0.45)));
  line(c, [[tip[0], tip[1]], [bx, tip[1] - 20]], 46, INK); line(c, [[tip[0], tip[1]], [bx, tip[1] - 20]], 30, '#7dff6b'); line(c, [[tip[0], tip[1]], [bx, tip[1] - 20]], 10, '#efffd9');
  glow(c, bx, tip[1] - 20, 120, 'rgba(125,255,107,A)', 0.8);
  const duck = eOut(ramp(lt, 0.0, 0.18));
  stick(c, { ...ODY, x: 260, y: 1560, s: 1.15, t: lt, mood: 'shock', look: 1, lean: -0.15 - duck * 0.25,
    legs: [[-0.7 * duck - 0.2, 1.2 * duck], [0.7 * duck + 0.2, -1.2 * duck]], arms: [[2.6, 0.4], [2.9, -0.3]], props: { r: 'sword' } });
});
// 3. "and the land of the dead." - ghosts swirl; he cuts through one; the camera pulls back
S(2.12 - D, 3.95 - D, 'cut', [[0, [540, 1050, 1.25, 0]], [1.8, [540, 960, 1.0, 0]]], (c, lt) => {
  hades(c, lt);
  for (let i = 0; i < 7; i++) {
    const a = lt * 1.6 + i / 7 * Math.PI * 2, rr = 330 + (i % 2) * 80;
    const gx = 540 + Math.cos(a) * rr, gy = 1000 + Math.sin(a) * rr * 0.55;
    if (i === 2 && lt > 0.75) { burst(c, gx, gy, 180, ramp(lt, 0.75, 1.15), '#b8fff2'); continue; }
    ghost(c, gx, gy, 1.0, lt, i);
  }
  const slash = ramp(lt, 0.55, 0.8);
  stick(c, { ...ODY, x: 540, y: 1560, s: 1.25, t: lt, mood: 'determined', look: Math.sin(lt * 3) * 0.6,
    arms: [[lerp(2.8, 0.9, eOut(slash)), -0.2], [-0.6, -0.4]], legs: [[-0.4, 0.15], [0.4, -0.1]], props: { l: 'sword' } });
});
// 4. "But the real monster... was him." - the music drops; his shadow becomes a monster
S(3.95 - D, 6.72 - D, 'cut', [[0, [540, 1000, 1.0, 0]], [2.7, [540, 900, 1.45, 0.0]]], (c, lt) => {
  sky(c, '#0d0a14', '#1c1424');
  glow(c, 540, 700, 700, 'rgba(255,240,200,A)', 0.18);
  const grow = eOut(ramp(lt, 0.4, 1.8)), red = ramp(lt, 1.6, 1.95);
  // the shadow on the wall behind him
  c.save(); c.globalAlpha = 0.85; c.fillStyle = '#000';
  const sh = 1 + grow * 0.7;
  withT(c, 540, 1560, 0, sh, () => {
    c.beginPath(); c.moveTo(-90, 0); c.lineTo(-60, -330); c.lineTo(-140, -380); c.lineTo(-150, -470); c.lineTo(-90, -440);
    c.quadraticCurveTo(-100, -560, 0, -580); c.quadraticCurveTo(100, -560, 90, -440); c.lineTo(150, -470); c.lineTo(140, -380); c.lineTo(60, -330); c.lineTo(90, 0); c.closePath(); c.fill();
    // horns grow in
    for (const s of [-1, 1]) { poly(c, [[s * 50, -560], [s * (70 + grow * 90), -560 - grow * 170], [s * 95, -530]]); c.fill(); }
    // glowing eyes
    for (const s of [-1, 1]) { ell(c, s * 34, -490, 18, 9, s * 0.4); c.fillStyle = `rgba(255,40,40,${red})`; c.fill(); }
    c.fillStyle = '#000';
  });
  c.restore();
  if (red > 0) glow(c, 540, 600, 500, 'rgba(255,30,30,A)', red * 0.25);
  stick(c, { ...ODY, x: 540, y: 1560, s: 1.25, t: lt, mood: lt > 1.75 ? 'evil' : 'flat', look: lt > 1.75 ? 0 : -0.4, lookY: lt > 1.75 ? -0.2 : 0,
    arms: [[-0.25, -0.1], [0.25, 0.1]], legs: [[-0.12, 0], [0.12, 0]], props: { r: 'sword', rRot: 0 }, shadow: false });
});
// 5. "Troy has fallen." - he walks away from the burning city past the wooden horse
S(6.72 - D, 8.46 - D, 'whip', [[0, [440, 980, 1.05, 0]], [1.75, [640, 960, 1.05, 0]]], (c, lt) => {
  troyWalls(c, lt);
  trojanHorse(c, 330, 1310, 1.25);
  const ph = lt * 7;
  stick(c, { ...ODY, x: lerp(380, 700, lt / 1.75), y: 1560, s: 1.2, t: lt, mood: 'sad', look: -1, lookY: -0.2, legs: walkLegs(ph), arms: walkArms(ph), props: { r: 'sword', rRot: 0.4 } });
});
// 6. "Odysseus just wants to go home." - at the prow, dreaming of home
S(8.46 - D, 10.95 - D, 'whip', [[0, [540, 1020, 1.0, 0]], [2.5, [500, 930, 1.18, 0]]], (c, lt) => {
  sky(c, '#47b6ff', '#c8ecff'); sun(c, 880, 300, 80, lt);
  cloud(c, 200, 330, 0.9); cloud(c, 760, 520, 0.7);
  sea(c, 1380, lt);
  ship(c, 520, 1720, 1.45, lt, { sail: false });
  for (let i = 0; i < 2; i++) { const gx = (lt * 120 + i * 400) % 1200 - 100, gy = 420 + i * 90; line(c, [[gx - 30, gy], [gx, gy + 14 + Math.sin(lt * 9 + i) * 8], [gx + 30, gy]], 6); }
  stick(c, { ...ODY, x: 640, y: 1560, s: 1.15, t: lt, mood: 'sad', look: 1, lookY: -0.3, blink: blink(lt, 2), arms: [[0.3, 0.6], [-0.3, -0.6]], legs: [[-0.2, 0], [0.25, 0]], shadow: false });
  // thought bubble: home, wife, son and dog
  const b = eBack(ramp(lt, 0.9, 1.35));
  if (b > 0) withT(c, 330, 560, 0, b, () => {
    for (const [x, y, r] of [[260, 420, 14], [220, 360, 22]]) { circ(c, x, y, r); fs(c, '#fff', 6); }
    ell(c, 0, 0, 260, 190); fs(c, '#fff', 9);
    poly(c, [[-120, 60], [-120, -30], [-40, -90], [40, -30], [40, 60]]); fs(c, '#ffd98a', 7); poly(c, [[-140, -25], [-40, -110], [60, -25]]); fs(c, '#e2403b', 7);
    rrect(c, -55, 10, 30, 50, 4); fs(c, '#8a5432', 5);
    stick(c, { x: 110, y: 90, s: 0.32, mood: 'smile', dress: ACC.penelope, gear: { bun: '#6a3a22' }, shadow: false, arms: [[-2.6, 0], [0.3, 0]] });
    stick(c, { x: 170, y: 90, s: 0.24, mood: 'smile', shadow: false, gear: { hairTop: '#6a3a22' }, arms: [[-0.3, 0], [2.6, 0]] });
    ell(c, 215, 80, 22, 12); fs(c, '#c98b52', 4); circ(c, 236, 68, 10); fs(c, '#c98b52', 4);
    // a little heart
    c.save(); c.translate(150, -95); c.rotate(Math.PI / 4); c.fillStyle = '#ff4f7a'; c.fillRect(-12, -12, 24, 24); circ(c, -12, 0, 12); c.fill(); circ(c, 0, -12, 12); c.fill(); c.restore();
  });
});
// 7. "A Cyclops eats his men." - a giant hand plucks a sailor; the Cyclops chews; a helmet clangs back down
S(10.95 - D, 13.40 - D, 'whip', [[0, [540, 960, 1.0, 0]], [2.4, [540, 1000, 1.08, 0]]], (c, lt) => {
  cave(c, lt);
  const chew = lt > 0.75 && lt < 1.9;
  cyclopsEye(c, 560, 330, 360, lt, { mouth: chew ? 0.6 + 0.4 * Math.abs(Math.sin(lt * 14)) : 0.3, look: 0.2, blink: blink(lt, 5) });
  // the hand comes down, grabs the middle sailor, goes up
  const down = ramp(lt, 0.0, 0.3), up = ramp(lt, 0.35, 0.7);
  const hy = lerp(-200, 1180, eOut(down)) - eIn(up) * 1500;
  const grabbed = lt > 0.3;
  if (!grabbed || hy > -300) {
    if (grabbed) stick(c, { ...CREW[0], x: 540, y: hy + 380, s: 0.95, t: lt, mood: 'yell', arms: [[2.6, 0.3], [-2.6, -0.3]], legs: [[-0.5, 0.4], [0.5, -0.4]], shadow: false });
    withT(c, 540, hy, 0, 1, () => { rrect(c, -150, -400, 300, 330, 70); fs(c, '#b7c79a', 12); for (let k = 0; k < 4; k++) { rrect(c, -140 + k * 72, -110, 62, 200, 30); fs(c, '#b7c79a', 10); } });
  }
  if (!grabbed) stick(c, { ...CREW[0], x: 540, y: 1560, s: 0.95, t: lt, mood: 'scared', look: 0, lookY: -1 });
  stick(c, { ...CREW[1], x: 230, y: 1560, s: 0.95, t: lt, mood: lt > 0.5 ? 'scared' : 'worried', lookY: -1, look: 0.5, arms: [[-2.7, 0.2], [2.7, -0.2]] });
  stick(c, { ...ODY, x: 850, y: 1560, s: 1.05, t: lt, mood: lt > 0.5 ? 'shock' : 'worried', lookY: -1, look: -0.6, arms: [[-0.4, -0.3], [2.4, 0.4]], props: { r: 'sword' } });
  // the empty helmet falls back down
  if (lt > 1.6) { const u = ramp(lt, 1.6, 2.0); const y = lerp(-100, 1500, eIn(u)); withT(c, 540, y, u * 6, 0.6, () => headgear(c, 64, { gear: { cap: ACC.bronze } }, false)); if (u >= 1) burst(c, 540, 1520, 90, ramp(lt, 2.0, 2.3), '#fff'); }
});
// 8. "Giants sink his ships." - boulders from the cliffs
S(13.40 - D, 14.93 - D, 'whip', [[0, [540, 1060, 0.9, 0]], [1.5, [540, 1080, 0.95, 0.01]]], (c, lt) => {
  sky(c, '#5ec2ff', '#d2f0ff'); cloud(c, 200, 300, 0.8);
  rock(c, 950, 1250, 420, 560, '#a29a8f');
  const throwA = Math.sin(lt * 5) * 0.8;
  stick(c, { x: 900, y: 700, s: 1.0, t: lt, mood: 'evil', look: -1, arms: [[-2.4 + throwA, -0.3], [-2.9, 0.2]], shadow: false, props: { l: 'boulder' } });
  sea(c, 1320, lt);
  const hit1 = ramp(lt, 0.15, 0.5), sink1 = ramp(lt, 0.5, 1.5);
  ship(c, 300, 1560 + sink1 * 220, 0.9, lt, { tilt: -sink1 * 0.6, seed: 1 });
  ship(c, 760, 1700, 0.75, lt, { seed: 2 });
  if (hit1 < 1) { const bx = lerp(780, 300, hit1), by = lerp(640, 1450, hit1) - Math.sin(hit1 * Math.PI) * 250; prop(c, 'boulder', bx, by, hit1 * 8, 0.9, lt); }
  else { for (let i = 0; i < 8; i++) { const a = -Math.PI / 2 + (i - 3.5) * 0.25, u = ramp(lt, 0.5, 1.1); circ(c, 300 + Math.cos(a) * u * 260, 1420 + Math.sin(a) * u * 300 + u * u * 300, 26 * (1 - u) + 4); fs(c, '#e8f6ff', 6); } }
});
// 9. "A witch turns his crew into pigs." - zap, poof, pigs in helmets
S(14.93 - D, 17.60 - D, 'whip', [[0, [540, 1060, 1.0, 0]], [0.9, [540, 1080, 1.0, 0]], [1.4, [460, 1330, 1.22, 0]], [2.6, [470, 1340, 1.28, 0]]], (c, lt) => {
  sky(c, '#7a3fc0', '#ffb3e6'); grassBeach(c, 1580, '#5a2f8a');
  for (const x of [80, 1000]) { rrect(c, x - 45, 450, 90, 1130, 6); fs(c, '#efe0ff', 9); }
  const zap = ramp(lt, 0.33, 0.6), poof = lt > 0.95;
  const r = stick(c, { x: 860, y: 1560, s: 1.15, t: lt, mood: poof ? 'evil' : 'smug', look: -1, dress: ACC.circe, gear: { hair: ACC.circe, crown: true }, arms: [[-1.9 + zap * 0.3, -0.2], [0.4, 0.2]], props: { l: 'wand' } });
  if (zap > 0 && zap < 1) { const tip = [r.hands[0][0] - 150, r.hands[0][1]]; for (let k = 0; k < 3; k++) { const ex = 180 + k * 200; line(c, [tip, [lerp(tip[0], ex, zap), lerp(tip[1], 1250, zap)]], 18, '#7dff6b'); } }
  for (let k = 0; k < 3; k++) {
    const x = 180 + k * 200;
    if (!poof) stick(c, { ...CREW[k], x, y: 1560, s: 0.95, t: lt, mood: zap > 0 ? 'shock' : 'smile', look: 1, blink: blink(lt, k) });
    else pig(c, x, 1560, 1.0, lt, { helmet: true, seed: k });
    burst(c, x, 1300, 170, ramp(lt, 0.9, 1.3), '#ffd1f0');
  }
});
// 10. "He visits the dead," - ghosts wave hello
S(17.60 - D, 18.83 - D, 'whip', [[0, [540, 960, 1.05, 0]], [1.2, [540, 960, 1.0, 0]]], (c, lt) => {
  hades(c, lt + 3);
  for (let i = 0; i < 5; i++) ghost(c, 150 + i * 190, 700 + (i % 2) * 160 + Math.sin(lt * 3 + i) * 20, 0.95, lt, i + 3);
  const ph = lt * 6;
  stick(c, { ...ODY, x: lerp(300, 520, lt / 1.2), y: 1560, s: 1.15, t: lt, mood: 'worried', look: 0.5, lookY: -0.6, legs: walkLegs(ph, 0.3), arms: [[-0.3, -0.2], [2.5 + Math.sin(lt * 14) * 0.3, 0.3]] });
});
// 11. "slips past the Sirens," - tied to the mast, straining toward the singing
S(18.83 - D, 20.46 - D, 'whip', [[0, [540, 960, 1.0, 0]], [1.6, [600, 960, 1.04, 0]]], (c, lt) => {
  sky(c, '#2f9bf0', '#b9e4ff'); sea(c, 1300, lt);
  rock(c, 230, 1330, 230, 260, '#8f8a99'); rock(c, 470, 1340, 170, 200, '#9e98a8');
  siren(c, 180, 1110, 0.75, lt, 0); siren(c, 420, 1150, 0.7, lt, 1);
  const sx = lerp(520, 800, lt / 1.6);
  ship(c, sx, 1740, 1.15, lt, { billow: 50 });
  const strain = Math.sin(lt * 12) * 0.12;
  stick(c, { ...ODY, x: sx + 10, y: 1590, s: 1.0, t: lt, mood: 'shock', look: -1, lean: -0.25 + strain, arms: [[-1.6, 0.4 + strain], [-1.3, 0.2]], shadow: false });
  for (const y of [1300, 1380]) line(c, [[sx - 40, y], [sx + 60, y + 10]], 8, '#e3c58a');
});
// 12. "and his starving men eat a god's cattle." - forks out; an angry god in the clouds
S(20.46 - D, 23.18 - D, 'whip', [[0, [540, 1220, 1.1, 0]], [1.4, [540, 1240, 1.12, 0]], [2.0, [540, 1120, 1.0, 0]], [2.7, [540, 1110, 1.02, 0]]], (c, lt) => {
  sky(c, '#5ec2ff', '#e4f7ff'); grassBeach(c, 1520, '#7ed36a');
  const god = eOut(ramp(lt, 1.55, 1.95));
  if (god > 0) withT(c, 540, 640, 0, god * 0.85, () => {
    cloud(c, 0, 60, 2.6, '#ffffff');
    circ(c, 0, -10, 150); fs(c, '#fff3c0', 10);
    for (let i = 0; i < 12; i++) { const a = i / 12 * Math.PI * 2; line(c, [[Math.cos(a) * 170, -10 + Math.sin(a) * 170], [Math.cos(a) * 230, -10 + Math.sin(a) * 230]], 12, '#ffcf3a'); }
    face(c, 140, { mood: 'angry', look: 0.3, lookY: 0.6 });
  });
  cow(c, 560, 1500, 1.2, lt, { halo: true, scared: lt > 1.0, sweat: lt > 1.2 });
  const sneak = eOut(ramp(lt, 0.0, 1.0)), pounce = ramp(lt, 1.0, 1.25);
  const freeze = god > 0.5;
  for (let k = 0; k < 3; k++) {
    const x0 = [120, 300, 960][k], x1 = [330, 420, 800][k];
    const x = lerp(x0, x1, sneak) + (freeze ? 0 : pounce * (k < 2 ? 40 : -40));
    stick(c, { ...CREW[k], x, y: 1560 - pounce * (freeze ? 0 : 40), s: 0.85, t: lt, mood: freeze ? 'scared' : (pounce > 0 ? 'grin' : 'smug'), look: k < 2 ? 1 : -1, lookY: freeze ? -1 : 0,
      lean: k < 2 ? 0.15 : -0.15, arms: k < 2 ? [[1.5, -0.4], [2.0, 0]] : [[-2.0, 0], [-1.5, 0.4]], props: k < 2 ? { r: 'fork' } : { l: 'fork', lRot: Math.PI } });
  }
});
// 13. "A storm kills them all." - lightning splits the ship; only he is left, on a plank
S(23.18 - D, 25.10 - D, 'cut', [[0, [540, 960, 1.0, 0]], [1.9, [540, 1060, 1.12, -0.02]]], (c, lt) => {
  const fl = decay(lt, 0.12, 7);
  stormSky(c, lt, fl);
  sea(c, 1300, lt * 1.8, '#1f4f80', '#3f78b0');
  const split = ramp(lt, 0.15, 0.6), gone = ramp(lt, 0.6, 1.2);
  if (gone < 1) {
    c.save(); c.globalAlpha = 1 - gone;
    ship(c, 480 - split * 140, 1600 + gone * 250, 1.0, lt, { tilt: -split * 0.5, sailCol: '#d8d2c4', seed: 3 });
    ship(c, 620 + split * 160, 1620 + gone * 250, 0.9, lt, { tilt: split * 0.6, sail: false, seed: 4 });
    c.restore();
  }
  if (lt > 0.08 && lt < 0.35) bolt(c, 640, -200, 520, 1500, 7);
  // tiny sailors tumbling away
  for (let k = 0; k < 3; k++) if (split > 0 && gone < 1) { const u = split; withT(c, 520 + (k - 1) * 200 * u, 1350 - Math.sin(u * Math.PI) * 300, u * 5 * (k - 1), 0.45, () => stick(c, { ...CREW[k], x: 0, y: 0, s: 1, mood: 'yell', arms: [[2.6, 0.2], [-2.6, -0.2]], shadow: false })); }
  if (lt > 1.1) {
    const bob = Math.sin(lt * 3) * 18;
    rrect(c, 300, 1400 + bob, 480, 40, 14); fs(c, '#8a5432', 9);
    stick(c, { ...ODY, x: 560, y: 1560 + bob, s: 0.9, t: lt, mood: 'sad', look: -0.3, lean: -1.2, arms: [[-1.2, 0.3], [-1.4, 0.2]], legs: [[1.4, 0.3], [1.6, 0.1]], shadow: false });
  }
});
// 14. "A nymph feeds him lotus." - dizzy spirals set in
S(25.10 - D, 27.04 - D, 'cut', [[0, [540, 1000, 1.0, 0]], [1.95, [500, 980, 1.12, 0]]], (c, lt) => {
  sky(c, '#38c4ff', '#d6f7ff'); sun(c, 900, 260, 70, lt);
  sea(c, 1150, lt, '#2fb6d8', '#7fdcf0');
  grassBeach(c, 1380); palm(c, 920, 1400, 1.3, lt);
  const eat = lt > 0.85, dizzy = lt > 1.25;
  const r = stick(c, { x: 760, y: 1560, s: 1.15, t: lt, mood: 'smile', look: -1, dress: '#3ec7c0', gear: { hair: ACC.calypso, flowers: true }, arms: [[-1.4, -0.2], [0.3, 0.2]], props: eat ? {} : { l: 'lotus', lRot: Math.PI / 2 } });
  stick(c, { ...ODY, x: 360, y: 1560, s: 1.1, t: lt, mood: dizzy ? 'dizzy' : (eat ? 'chew' : 'o'), look: 1, lean: dizzy ? Math.sin(lt * 5) * 0.12 : 0,
    arms: eat ? [[2.4, 0.9], [0.4, 0.2]] : [[1.2, 0.3], [0.4, 0.2]], legs: [[-0.3, 0.1], [0.3, -0.1]] });
  if (dizzy) for (let i = 0; i < 4; i++) { const a = lt * 4 + i / 4 * Math.PI * 2; circ(c, 360 + Math.cos(a) * 110, 990 + Math.sin(a) * 30, 14); fs(c, '#ffe14d', 5); }
});
// 15. "He forgets home for seven years." - hammock, sun and moon racing, beard growing, seven tally marks
S(27.04 - D, 29.57 - D, 'whip', [[0, [540, 960, 1.12, 0]], [2.5, [540, 960, 1.0, 0]]], (c, lt) => {
  const u = ramp(lt, 0.2, 1.5), days = u * 7;
  const night = 0.5 - 0.5 * Math.cos(days * Math.PI * 2);
  sky(c, `rgb(${lerp(56, 20, night)},${lerp(196, 30, night)},${lerp(255, 80, night)})`, `rgb(${lerp(214, 60, night)},${lerp(247, 50, night)},${lerp(255, 110, night)})`);
  const a = days * Math.PI * 2;
  sun(c, 540 + Math.cos(a - Math.PI / 2) * 520, 820 + Math.sin(a - Math.PI / 2) * 480, 60, lt);
  circ(c, 540 + Math.cos(a + Math.PI / 2) * 520, 820 + Math.sin(a + Math.PI / 2) * 480, 50); fs(c, '#f4f1e6', 8);
  sea(c, 1150, lt, '#2fb6d8', '#7fdcf0');
  grassBeach(c, 1380);
  palm(c, 170, 1420, 1.25, lt); palm(c, 930, 1420, 1.25, lt);
  // tally marks scratched on a rock
  rock(c, 860, 1560, 130, 170, '#b8b0a2');
  const marks = Math.min(7, Math.floor(days + 0.001));
  for (let i = 0; i < marks; i++) { if (i === 4) line(c, [[770, 1490], [880, 1430]], 7); else line(c, [[775 + (i % 5) * 24 + (i > 4 ? 120 : 0), 1420], [775 + (i % 5) * 24 + (i > 4 ? 120 : 0), 1500]], 7); }
  // hammock
  c.beginPath(); c.moveTo(240, 1000); c.quadraticCurveTo(540, 1250, 860, 1000); c.lineWidth = 10; c.strokeStyle = INK; c.stroke();
  c.beginPath(); c.moveTo(270, 1010); c.quadraticCurveTo(540, 1280, 830, 1010); c.quadraticCurveTo(540, 1180, 270, 1010); fs(c, '#ff7a59', 8);
  withT(c, 540, 1150, -1.45, 1, () => stick(c, { ...ODY, gear: { helmet: false, beard: true, longBeard: u }, x: 0, y: 0, s: 1.0, t: lt, mood: 'sleepy', blink: lt > 0.6 && lt < 2.0, arms: [[-2.6, -0.4], [2.6, 0.4]], shadow: false }));
});
// 16. "Back home, suitors want his throne." - one of them sits on it
S(29.57 - D, 32.10 - D, 'whip', [[0, [540, 960, 1.0, 0]], [2.5, [560, 1000, 1.1, 0]]], (c, lt) => {
  hall(c, lt);
  const sit = eBack(ramp(lt, 1.5, 1.75));
  throne(c, 540, 1560, 1.1);
  stick(c, { x: 150, y: 1560, s: 1.0, t: lt, mood: 'angry', look: 1, dress: ACC.penelope, gear: { bun: '#6a3a22' }, arms: [[0.9, -1.9], [-0.9, 1.9]], blink: blink(lt, 4) });
  const ss = [[330, '#f07ab0'], [760, '#f0c040'], [930, '#7a9cf0']];
  ss.forEach(([x, col], k) => stick(c, { x: x + Math.sin(lt * 2 + k) * 8, y: 1560, s: 0.95, t: lt, mood: sit > 0.5 ? 'angry' : 'smug', look: k === 0 ? 1 : -1, tunic: col, gear: { laurel: true },
    arms: [[-0.4, -0.3], [k === 0 ? 1.0 : -1.0, 0.8]], props: { r: 'goblet', rRot: k === 0 ? 0.3 : -0.3 }, blink: blink(lt, k) }));
  const sy = lerp(1560, 1430, sit), sx = lerp(620, 540, sit);
  stick(c, { x: sx, y: sy, s: 0.95, t: lt, mood: sit > 0.5 ? 'smug' : 'grin', look: -0.3, tunic: '#3fbf5a', gear: { laurel: !(sit > 0.5), crown: sit > 0.5 },
    legs: sit > 0.5 ? [[-1.4, 1.4], [-1.2, 1.3]] : [[-0.2, 0], [0.2, 0]], arms: [[-1.2, 1.0], [1.2, -1.0]], shadow: sit < 0.5 });
});
// 17. "He returns in disguise," - a hooded beggar shuffles in and winks
S(32.10 - D, 33.71 - D, 'cut', [[0, [540, 960, 1.0, 0]], [1.6, [520, 860, 1.25, 0]]], (c, lt) => {
  hall(c, lt);
  // doorway light
  rrect(c, 330, 600, 420, 960, 200); fs(c, '#fff6d0', 12);
  glow(c, 540, 1100, 520, 'rgba(255,240,180,A)', 0.6);
  const ph = lt * 5;
  stick(c, { ...ODY, gear: { hood: true, beard: true, longBeard: 0.6 }, cloakBody: true, x: lerp(480, 560, lt / 1.6), y: 1560, s: 1.15, t: lt,
    mood: lt > 0.75 ? 'smug' : 'flat', look: lt > 0.75 ? 0 : 0.6, blink: false, lean: 0.12, legs: walkLegs(ph, 0.2), arms: [[-0.2, -0.2], [0.6, 0.6]] });
});
// 18. "strings the bow no one else can..." - a suitor fails; he strings it easily and draws
S(33.71 - D, 36.05 - D, 'whip', [[0, [640, 1220, 1.2, 0]], [1.0, [640, 1220, 1.2, 0]], [1.3, [520, 1200, 1.15, 0]], [2.3, [430, 1120, 1.45, 0]]], (c, lt) => {
  hall(c, lt);
  axes(c, 780, 1560, 4, 70, 0.9);
  const fail = lt < 1.0;
  const strain = Math.sin(lt * 30) * 0.08;
  stick(c, { x: fail ? 700 : 880, y: 1560, s: 0.95, t: lt, mood: fail ? 'yell' : 'shock', look: -1, tunic: '#f07ab0', gear: { laurel: true },
    lean: fail ? strain : (lt < 1.3 ? -0.5 : -0.2), arms: fail ? [[-1.5, 0.2], [1.6, -0.2]] : [[-0.5, 0], [0.5, 0]], props: fail ? { l: 'bow', lRot: -Math.PI / 2 } : {},
    legs: fail ? [[-0.4, 0], [0.4, 0]] : [[0.9, 0.5], [1.2, 0.2]] });
  if (!fail) {
    const draw = eOut(ramp(lt, 1.35, 1.9));
    stick(c, { ...ODY, gear: { hood: false, beard: true, longBeard: 0.6, helmet: false }, cloakBody: true, x: 360, y: 1560, s: 1.15, t: lt, mood: 'determined', look: 1,
      arms: [[1.57, 0], [1.57 - draw * 0.2, -draw * 2.2]], props: { l: 'bow', lRot: 0, lT: draw } });
  }
});
// 19. "and the suitors pay." - the arrow zips through the axes; the suitors scatter
S(36.05 - D, 37.57 - D, 'cut', [[0, [420, 1240, 1.2, 0]], [0.6, [760, 1240, 1.2, 0]], [1.5, [620, 1180, 1.05, 0]]], (c, lt) => {
  hall(c, lt);
  axes(c, 380, 1560, 4, 140, 0.9);
  const u = ramp(lt, 0.0, 0.45), ax = lerp(150, 1200, u);
  if (u < 1) { line(c, [[ax - 160, 1410], [ax, 1410]], 12, '#a0682f'); poly(c, [[ax, 1395], [ax + 40, 1410], [ax, 1425]]); fs(c, '#c9d2dc', 5); speedLines(c, ax - 300, 1410, lt, 10, 40, 400, 0.4); }
  const panic = lt > 0.45;
  [[700, '#f0c040'], [860, '#7a9cf0'], [980, '#3fbf5a']].forEach(([x, col], k) => {
    const run = panic ? ramp(lt, 0.45 + k * 0.08, 1.4) : 0;
    stick(c, { x: x + run * 500 * (k % 2 ? 1 : 0.8), y: 1560 - Math.abs(Math.sin(lt * 14 + k)) * (panic ? 40 : 0), s: 0.9, t: lt, mood: panic ? 'scared' : 'smug', look: -1, tunic: col, gear: { laurel: true },
      arms: panic ? [[-2.8, 0.2], [2.8, -0.2]] : [[-0.4, -0.3], [-1.0, 0.8]], legs: panic ? walkLegs(lt * 18, 0.7) : [[-0.15, 0], [0.15, 0]], props: panic ? {} : { r: 'goblet', rRot: -0.3 } });
  });
  burst(c, 820, 1150, 260, ramp(lt, 0.6, 1.0), '#ffe14d');
  for (let i = 0; i < 3; i++) { const g = ramp(lt, 0.5, 1.2); if (g > 0 && g < 1) prop(c, 'goblet', 820 + i * 80 + g * 200, 1200 - Math.sin(g * Math.PI) * 400 + g * 300, g * 9 + i, 1, lt); }
});
// 20. "The twist?" - freeze; he slowly turns to camera
S(37.57 - D, 38.53 - D, 'whip', [[0, [540, 1060, 1.3, 0]], [0.95, [540, 1050, 1.6, 0]]], (c, lt) => {
  sky(c, '#2a2238', '#5b4a6a');
  speedLines(c, 540, 820, lt * 0.3, 30, 420, 1400, 0.25);
  stick(c, { ...ODY, x: 540, y: 1560, s: 1.25, t: lt, mood: lt > 0.5 ? 'smug' : 'flat', look: lerp(-1, 0, ease(ramp(lt, 0.15, 0.55))), shadow: false });
}, { sat: 0.35 });
// 21. "The raiders from the sea everyone feared were the Greeks." - dark sails on the horizon; the emblem is his
S(38.53 - D, 42.05 - D, 'cut', [[0, [540, 1000, 1.0, 0]], [1.4, [540, 1000, 1.0, 0]], [2.6, [560, 1260, 1.6, 0]], [3.5, [600, 1240, 1.75, 0]]], (c, lt) => {
  sky(c, '#3b2a5c', '#ff8a5c'); sun(c, 560, 1140, 90, lt);
  sea(c, 1250, lt, '#3b4f8a', '#5a73b0');
  const near = ramp(lt, 0.0, 3.4);
  for (const [x, sc, sd] of [[260, 0.35, 1], [800, 0.33, 2], [560, 0.45, 3]]) ship(c, x, 1330 + near * 60, sc + near * 0.15, lt, { sailCol: '#2b2233', stripes: false, emblem: lt > 1.9, seed: sd, oars: true });
  if (lt > 2.1) stick(c, { ...ODY, x: 560 + 70, y: 1330 + near * 60 - 30 * (0.45 + near * 0.15), s: 0.45 + near * 0.15 * 0.55, t: lt, mood: 'determined', look: 1, arms: [[-0.3, 0], [2.4, 0.2]], props: { r: 'sword' }, shadow: false });
  // villagers on the shore, afraid
  const shore = 1590;
  c.fillStyle = '#d9b27a'; c.fillRect(-1200, shore - 140, 3500, 900); line(c, [[-1200, shore - 140], [2300, shore - 140]], 10);
  if (lt < 1.9) for (let k = 0; k < 2; k++) stick(c, { x: k ? 930 : 150, y: shore + 60, s: 0.85, t: lt, mood: 'scared', lookY: -0.6, look: k === 0 ? 0.6 : -0.6, dress: k === 1 ? '#d4402e' : null, gear: k === 1 ? { bun: '#6a3a22' } : { hairTop: '#3a2a1a' }, arms: [[-2.5, 0.3], [2.5, -0.3]], shadow: false });
});
// 22. "They were him." - the shadow returns; cut to black after "him"
S(42.05 - D, 99, 'cut', [[0, [540, 1010, 1.85, 0]], [0.9, [540, 1030, 2.05, 0]]], (c, lt, t) => {
  sky(c, '#0d0a14', '#2a0d14');
  glow(c, 540, 700, 700, 'rgba(255,30,30,A)', 0.3);
  c.save(); c.fillStyle = '#000'; c.globalAlpha = 0.9;
  withT(c, 540, 1560, 0, 1.75, () => { c.beginPath(); c.moveTo(-90, 0); c.quadraticCurveTo(-100, -560, 0, -580); c.quadraticCurveTo(100, -560, 90, 0); c.closePath(); c.fill();
    for (const s of [-1, 1]) { poly(c, [[s * 50, -560], [s * 160, -730], [s * 95, -530]]); c.fill(); }
    for (const s of [-1, 1]) { ell(c, s * 34, -490, 18, 9, s * 0.4); c.fillStyle = '#ff2828'; c.fill(); c.fillStyle = '#000'; } });
  c.restore();
  stick(c, { ...ODY, x: 540, y: 1560, s: 1.25, t: lt, mood: 'evil', look: 0, lookY: -0.1, shadow: false });
}, { blackAt: 42.72 });
