// LIVELIER CROWDS (feature flag "crowdFX"): seeded variation, dust on every footstep, and slapstick knock-backs.
// Blasts (fx type "blast", or anything that registers in scene._impacts) push every character inside the radius
// outward on a ballistic arc: spin, flailing rubber-hose limbs, the hat flies off on its own arc, one bounce, a slide
// with dust, then dazed stars or scrambling back up. Cartoon and bloodless. Pure functions of time and seeds.
const WIND = [38, -6];                                 // px / s, global dust drift

function crowdVariation(cr, i) {
  const sd = (cr.seed || 1) * 977 + i * 13.37, r = k => hash(sd + k * 7.77);
  const variants = cr.variants || null;
  return {
    height: 1 + (r(1) - 0.5) * 0.16,                   // +-8 %
    speed: 1 + (r(2) - 0.5) * 0.2,                     // +-10 %
    phase: (i * 0.6180339887 + r(3) * 0.25) % 1,       // gait cycle offset: golden-ratio spread, so neighbours never sync
    delay: r(4) * 0.4,                                 // start delay 0-0.4 s
    def: Object.assign({ hatSpring: { freq: 2.6 + r(5) * 1.6, damping: 0.16 + r(6) * 0.14, mass: 0.8 + r(7) * 0.5 } },
      variants ? { costume: variants[Math.floor(r(8) * variants.length)] } : {}),
  };
}

// ---------------- dust ----------------
function dustPuff(g, x, y, age, life, size, seed, alpha, col = '205,190,165') {
  if (age < 0 || age > life) return;
  const u = age / life;
  for (let k = 0; k < 3 + Math.floor(hash(seed) * 4); k++) {                     // 3-6 puffs
    const a = hash(seed + k * 1.3) * Math.PI * 2, sp = 12 + hash(seed + k * 2.1) * 30;
    const px = x + Math.cos(a) * sp * eOut(u) + WIND[0] * age, py = y - 4 - Math.abs(Math.sin(a)) * sp * 0.4 * eOut(u) - 18 * age + WIND[1] * age;
    const r = size * (0.45 + hash(seed + k * 3.3) * 0.4) * (0.6 + u * 1.3);
    g.beginPath(); g.arc(px, py, r, 0, 7); g.fillStyle = `rgba(${col},${alpha * (1 - u) * (1 - u)})`; g.fill();
  }
}
function crowdDust(g, m, s, t) {
  const st = m.st, z = m.z ?? 150;
  if (st.ragdoll || st.lying) return;
  if (!GAIT[st.action] || st.dist == null || !(st.speedL > 1)) return;
  const sc = st.scale || 1, run = st.action === 'run', fade = clamp(150 / z, 0.35, 1);
  const life = run ? 0.95 : 0.6, evs = plantEvents(st.action, st.dist - st.speedL * life, st.dist, st.cycle || 0);
  const vx = st.vel ? st.vel[0] : (st.flip ? -1 : 1), vy = st.vel ? st.vel[1] : 0, vl = Math.hypot(vx, vy) || 1;
  for (const e of evs) {
    const age = (st.dist - e.d) / st.speedL, back = (st.dist - e.d) * sc;            // how far the body moved since the plant
    const fx = st.x + ((e.foot ? 14 : -14) + e.x) * sc * (st.flip ? -1 : 1) - vx / vl * back, fy = st.y - vy / vl * back;
    dustPuff(g, fx, fy, age, life, (run ? 26 : 16) * sc * 1.6, (st.id || 1) * 31 + e.d * 0.013, 0.55 * fade);
  }
}

// ---------------- knock-backs ----------------
const GRAV = 2600;                                     // px / s^2
function crowdReact(st, s, t, z) {
  for (const im of s._impacts || []) {
    if (t < im.t0 || (im.only && !im.only.includes(st.id))) continue;
    const tau0 = t - im.t0;
    const x0 = st.x - (st.vel ? st.vel[0] * tau0 : 0), y0 = st.y - (st.vel ? st.vel[1] * tau0 : 0);
    const dx = x0 - im.x, dy = (y0 - im.y) * 1.6, d = Math.hypot(dx, dy);
    if (d > im.r) continue;                             // outside the blast: no reaction
    const k = 1 - d / im.r, sd = hash((st.id || 7) * 3.1 + im.t0), dir = dx === 0 ? (sd > 0.5 ? 1 : -1) : Math.sign(dx);
    const sc = st.scale || 1, out = Object.assign({}, st);
    const vx = dir * (500 + 500 * sd) * (0.4 + k) * im.force * sc, vy = (900 + 600 * k) * im.force * sc, spin = dir * (7 + 8 * sd) * (0.5 + k);
    const t1 = 2 * vy / GRAV, e = 0.35, t2 = t1 + 2 * vy * e / GRAV;               // first landing, bounce landing
    let x, air, rot, phase;
    if (tau0 < t1) { x = x0 + vx * tau0; air = vy * tau0 - 0.5 * GRAV * tau0 * tau0; rot = spin * tau0; phase = 'fly'; }
    else if (tau0 < t2) { const u = tau0 - t1; x = x0 + vx * t1 + vx * 0.5 * u; air = vy * e * u - 0.5 * GRAV * u * u; rot = spin * t1 + spin * 0.4 * u; phase = 'bounce'; }
    else { const u = tau0 - t2, sv = vx * 0.5, stop = Math.abs(sv) / 1800, us = Math.min(u, stop);
      x = x0 + vx * t1 + vx * 0.5 * (t2 - t1) + sv * us - Math.sign(sv) * 900 * us * us; air = 0; rot = Math.round((spin * t1) / (Math.PI)) * Math.PI + dir * Math.PI / 2; phase = 'slide'; }
    out.x = x; out.vel = null; out.air = Math.max(0, air) / sc; out.dist = undefined;
    const lieT = tau0 - t2, getUp = !im.stay && sd > 0.45;                                     // some scramble up, some stay dazed
    if (phase !== 'slide') { out.ragdoll = true; out.action = 'fall'; out.bodyRot = rot; out.mood = 'shocked'; }
    else if (!getUp || lieT < 1.1) { out.lying = true; out.action = 'idle'; out.bodyRot = dir * Math.PI / 2; out.mood = 'sad'; out.y = st.y; out.blink = 0.9; }
    else if (lieT < 1.5) { const u = (lieT - 1.1) / 0.4; out.bodyRot = dir * Math.PI / 2 * (1 - eOut(u)); out.action = 'flail'; out.mood = 'scared'; }
    else { out.action = 'run'; out.flip = dir < 0; out.mood = 'scared'; const run = (lieT - 1.5) * 520 * sc; out.x = x + dir * run; out.dist = run / sc; out.speedL = 520; out.vel = [dir * 520 * sc, 0]; }
    if (out.lying) out.y = st.y - 0;                                              // lie on the ground
    out.hatOff = true;
    out._post = (g) => {                                                           // hat on its own arc + landing dust + stars
      const def = out._def; const hv = vy * 1.15, ht = Math.min(tau0, 2 * hv / GRAV + 0.4);
      const hx = x0 + vx * 1.25 * ht, hy = y0 - 330 * sc - (hv * ht - 0.5 * GRAV * ht * ht);
      if (def) drawLooseHat(g, def, hx, Math.min(hy, y0 - 20 * sc), dir * 9 * Math.min(ht, 2 * hv / GRAV), sc * 0.95);
      if (tau0 > t1) dustPuff(g, x0 + vx * t1, st.y, tau0 - t1, 0.9, 40 * sc, sd * 99, 0.6);
      if (tau0 > t2) dustPuff(g, out.x, st.y, tau0 - t2, 0.8, 30 * sc, sd * 77, 0.5);
      if (out.lying && !getUp) for (let k = 0; k < 3; k++) {                       // dazed cartoon stars
        const a = t * 4 + k * 2.09, sx = out.x + dir * 230 * sc + Math.cos(a) * 70 * sc, sy = st.y - 60 * sc + Math.sin(a) * 22 * sc;
        star5(g, sx, sy, 16 * sc, '#ffd84a');
      }
    };
    return out;
  }
  return st;
}
function star5(g, x, y, r, col) {
  g.beginPath(); for (let i = 0; i < 10; i++) { const a = -Math.PI / 2 + i * Math.PI / 5, rr = i % 2 ? r * 0.45 : r; g.lineTo(x + Math.cos(a) * rr, y + Math.sin(a) * rr); }
  g.closePath(); g.fillStyle = col; g.fill(); g.lineWidth = 3; g.strokeStyle = C.ink; g.stroke();
}
