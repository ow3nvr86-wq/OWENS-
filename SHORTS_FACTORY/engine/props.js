// Props and extra effects (original cartoon designs, drawn in code). Props live in scene.props[] and sit on a depth
// layer like characters; FX2 effects are fx[] types; hand props attach to a character's hands (st.prop).
// All motion is a function of time.
const WOOD = { face: '#c9904f', dark: '#9a6a36', line: '#7a5028' };
function inkRect(g, x, y, w, h, fill, lw = 6) { g.beginPath(); g.rect(x, y, w, h); g.fillStyle = fill; g.fill(); g.lineWidth = lw; g.strokeStyle = C.ink; g.lineJoin = 'round'; g.stroke(); }
function glow2(g, x, y, r, col) {                    // radial glow from an rgba() colour to transparent
  if (!(r > 0)) return; const m = col.match(/rgba?\(([^)]+)\)/), c = m ? m[1].split(',').map(v => v.trim()) : ['255', '255', '255', '1'];
  const gr = g.createRadialGradient(x, y, 0, x, y, r); gr.addColorStop(0, `rgba(${c[0]},${c[1]},${c[2]},${c[3] ?? 1})`); gr.addColorStop(1, `rgba(${c[0]},${c[1]},${c[2]},0)`);
  g.fillStyle = gr; g.fillRect(x - r, y - r, r * 2, r * 2);
}
function popScale(t, t0, dur = 0.32) { if (t0 == null) return 1; if (t < t0) return 0; return eBack(clamp((t - t0) / dur), 2.4); }

// ---------------- world props ----------------
const PROPS = {
  bus(g, p, s, t) {                                   // a flying bus under a striped hot-air balloon
    const bob = Math.sin(t * 1.7) * 10, sw = Math.sin(t * 1.3) * 0.03;
    g.rotate(sw); g.translate(0, bob);
    for (const x of [-120, 120]) { g.beginPath(); g.moveTo(x * 0.9, -150); g.lineTo(x * 1.1, -470); g.lineWidth = 5; g.strokeStyle = C.ink; g.stroke(); }
    g.save(); g.translate(0, -720);
    const cols = ['#e04a3a', '#f4d35e', '#e04a3a', '#f4d35e', '#e04a3a', '#f4d35e'];
    for (let k = 0; k < 6; k++) { g.beginPath(); const a0 = -Math.PI / 2 - 1.3 + k * 2.6 / 6, a1 = a0 + 2.6 / 6;
      g.moveTo(0, 250); g.quadraticCurveTo(Math.cos(a0) * 330, Math.sin(a0) * 280 + 60, Math.cos(a0) * 270, Math.sin(a0) * 270); g.arc(0, 0, 270, a0, a1); g.quadraticCurveTo(Math.cos(a1) * 330, Math.sin(a1) * 280 + 60, 0, 250);
      g.fillStyle = cols[k]; g.fill(); }
    g.beginPath(); g.arc(0, 0, 270, -Math.PI / 2 - 1.3, -Math.PI / 2 + 1.3); g.quadraticCurveTo(320, 140, 0, 250); g.quadraticCurveTo(-320, 140, Math.cos(-Math.PI / 2 - 1.3) * 270, Math.sin(-Math.PI / 2 - 1.3) * 270); g.lineWidth = 8; g.strokeStyle = C.ink; g.stroke();
    g.restore();
    g.beginPath(); g.moveTo(-300, -150); g.lineTo(290, -150); g.quadraticCurveTo(330, -150, 330, -100); g.lineTo(330, 40); g.lineTo(-300, 40); g.closePath(); g.fillStyle = '#2f7fd0'; g.fill(); g.lineWidth = 8; g.strokeStyle = C.ink; g.stroke();
    inkRect(g, -300, -20, 630, 22, '#f4d35e', 5);
    for (let k = 0; k < 5; k++) inkRect(g, -270 + k * 110, -128, 86, 70, '#bfe6ff', 5);
    for (const x of [-190, 210]) { g.beginPath(); g.arc(x, 44, 46, 0, 7); g.fillStyle = '#26232a'; g.fill(); g.lineWidth = 7; g.stroke(); g.beginPath(); g.arc(x, 44, 18, 0, 7); g.fillStyle = '#aaa'; g.fill(); }
    if (p.fan !== false) for (let k = 0; k < 2; k++) { g.save(); g.translate(-330, -60); g.rotate(t * 30 + k * Math.PI); g.beginPath(); g.ellipse(0, -40, 10, 40, 0, 0, 7); g.fillStyle = '#ddd'; g.fill(); g.stroke(); g.restore(); }
  },
  wall(g, p, s, t) {                                  // a wooden build piece, square panel
    const k = popScale(t, p.t0); if (!k) return; g.scale(k, k);
    const w = 300, h = 300; inkRect(g, -w / 2, -h, w, h, WOOD.face, 8);
    for (let i = 1; i < 5; i++) { g.beginPath(); g.moveTo(-w / 2, -h + i * h / 5); g.lineTo(w / 2, -h + i * h / 5); g.lineWidth = 4; g.strokeStyle = WOOD.line; g.stroke(); }
    for (const x of [-w / 2 + 14, w / 2 - 14]) inkRect(g, x - 10, -h, 20, h, WOOD.dark, 4);
    if (p.t0 != null && t - p.t0 < 0.4) dustPuff(g, 0, 0, t - p.t0, 0.4, 60, 3, 0.6);
  },
  ramp(g, p, s, t) {
    const k = popScale(t, p.t0); if (!k) return; g.scale(k, k);
    g.beginPath(); g.moveTo(-160, 0); g.lineTo(160, -300); g.lineTo(190, -300); g.lineTo(190, 0); g.closePath(); g.fillStyle = 'rgba(0,0,0,0.12)'; g.fill();
    g.save(); g.translate(-160, 0); g.rotate(-Math.atan2(300, 320)); inkRect(g, 0, -26, 440, 26, WOOD.face, 7);
    for (let i = 1; i < 8; i++) { g.beginPath(); g.moveTo(i * 55, -26); g.lineTo(i * 55, 0); g.lineWidth = 3; g.strokeStyle = WOOD.line; g.stroke(); } g.restore();
    inkRect(g, 150, -300, 26, 300, WOOD.dark, 6);
  },
  stairs(g, p, s, t) {                                // a zig-zag wooden staircase, optionally very tall ("to nowhere")
    const n = p.steps || 6, sh = 50, sw = 62, rate = p.rate || 0.05;
    const posX = (i) => { const fl = Math.floor(i / 6), j = i % 6; return (fl % 2 ? 1 : 0) ? 186 - (j + 1) * sw : -186 + j * sw; };
    let shown = 0; for (let i = 0; i < n; i++) if (p.t0 == null || t >= p.t0 + i * rate) shown = i + 1;
    if (!shown) return;
    const top = shown * sh + 30;
    for (const x of [-196, 176]) inkRect(g, x, -top, 20, top, WOOD.dark, 5);                   // posts grow with the stairs
    for (let fl = 0; fl * 6 < shown; fl++) {                                                     // stringers under each flight
      const a = fl * 6, b = Math.min(shown, a + 6) - 1, xa = posX(a) + (fl % 2 ? sw : 0), xb = posX(b) + (fl % 2 ? 0 : sw);
      g.beginPath(); g.moveTo(xa, -(a + 1) * sh + 34); g.lineTo(xb, -(b + 1) * sh + 34); g.lineWidth = 14; g.strokeStyle = WOOD.dark; g.lineCap = 'round'; g.stroke();
    }
    for (let i = 0; i < shown; i++) {
      const k = popScale(t, p.t0 != null ? p.t0 + i * rate : null, 0.22); if (!k) continue;
      g.save(); g.translate(posX(i) + sw / 2, -(i + 1) * sh + 8); g.scale(k, k); inkRect(g, -sw / 2 - 4, -8, sw + 8, 18, WOOD.face, 5); g.restore();
    }
  },
  hoprock(g, p, s, t) {                               // a glowing purple rock on the ground
    const pulseK = 0.75 + 0.25 * Math.sin(t * 5 + (p.seed || 0)), r = 60 * (p.size || 1);
    glow2(g, 0, -r * 0.6, r * 2.6, `rgba(170,70,255,${0.45 * pulseK})`);
    g.beginPath(); for (let i = 0; i < 7; i++) { const a = i / 7 * 6.283, rr = r * (0.75 + hash((p.seed || 1) + i) * 0.35); g.lineTo(Math.cos(a) * rr, -r * 0.6 + Math.sin(a) * rr * 0.75); }
    g.closePath(); g.fillStyle = '#7a2fd0'; g.fill(); g.lineWidth = 7; g.strokeStyle = C.ink; g.stroke();
    g.beginPath(); g.ellipse(-r * 0.25, -r * 0.85, r * 0.22, r * 0.12, -0.5, 0, 7); g.fillStyle = 'rgba(235,200,255,0.85)'; g.fill();
  },
  screenbar(g, p, s, t) {},
};
function drawProp(g, p, s, t) {
  const f = PROPS[p.type]; if (!f) return;
  let x = (p.x ?? 0.5) * W, y = (p.y ?? 0.8) * H;
  if (p.move) { const u = ease5((t - (p.move.t0 ?? s.start)) / Math.max(0.2, (p.move.t1 ?? s.end) - (p.move.t0 ?? s.start))); x = lerp(x, (p.move.x ?? p.x) * W, u); y = lerp(y, (p.move.y ?? p.y) * H, u); }
  g.translate(x, y); g.scale((p.flip ? -1 : 1) * (p.scale || 1), p.scale || 1); if (p.rot) g.rotate(p.rot);
  f(g, p, s, t);
}

// ---------------- hand props ----------------
function drawHandProp(g, prop, hands, t, st) {
  const [hx, hy, ha] = hands[1], [lx, ly] = hands[0];
  g.save();
  if (prop === 'glider') {                            // an umbrella-style glider above both hands
    const cx = (hx + lx) / 2, cy = Math.min(hy, ly) - 70;
    for (const [x, y] of [hands[0], hands[1]]) { g.beginPath(); g.moveTo(x, y); g.lineTo(cx + (x - cx) * 2.2, cy - 30); g.lineWidth = 4; g.strokeStyle = C.ink; g.stroke(); }
    g.translate(cx, cy - 40); g.rotate(Math.sin(t * 2) * 0.05);
    const cols = ['#ffcf3a', '#e8483a', '#ffcf3a', '#e8483a', '#ffcf3a'];
    for (let k = 0; k < 5; k++) { g.beginPath(); g.moveTo(0, 0); g.arc(0, 60, 230, Math.PI + 0.35 + k * 0.48, Math.PI + 0.35 + (k + 1) * 0.48); g.closePath(); g.fillStyle = cols[k]; g.fill(); g.lineWidth = 6; g.strokeStyle = C.ink; g.stroke(); }
  } else if (prop === 'shotgun' || prop === 'sniper') {
    g.translate(hx, hy); g.rotate(Math.PI / 2 - ha);
    const L = prop === 'sniper' ? 300 : 210;
    g.beginPath(); g.moveTo(-70, -6); g.lineTo(-10, -14); g.lineTo(-10, 18); g.lineTo(-80, 26); g.closePath(); g.fillStyle = '#7a4a26'; g.fill(); g.lineWidth = 6; g.strokeStyle = C.ink; g.stroke();
    inkRect(g, -14, -16, L, 18, '#2c2b31', 6);
    if (prop === 'shotgun') inkRect(g, 40, 2, 90, 16, '#7a4a26', 5);
    else { inkRect(g, 30, -44, 110, 22, '#1d1c22', 5); g.beginPath(); g.arc(140, -33, 12, 0, 7); g.fillStyle = '#9fd8ff'; g.fill(); g.stroke(); }
  } else if (prop === 'hoprock') {
    g.translate(hx, hy - 20); g.scale(0.55, 0.55); PROPS.hoprock(g, { seed: 3, size: 1 }, null, t);
  }
  g.restore();
}

// ---------------- FX2: world-plane and screen effects ----------------
const FX2 = {
  blast(g, fx, s, t) {                                // flash + shockwave ring + dirt + smoke (the knock-back is crowdReact)
    const u = t - fx.t0; if (u < 0 || u > 1.6) return; const x = fx.x * W, y = fx.y * H, r = fx.r || 260;
    if (u < 0.12) glow2(g, x, y - 40, r * 1.6 * (1 - u / 0.12 * 0.3), `rgba(255,245,200,${0.9 * (1 - u / 0.12)})`);
    if (u < 0.5) { g.save(); g.translate(x, y); g.scale(1, 0.35); g.beginPath(); g.arc(0, 0, r * 1.4 * eOut(u / 0.5), 0, 7); g.lineWidth = 26 * (1 - u / 0.5); g.strokeStyle = `rgba(255,240,210,${0.8 * (1 - u / 0.5)})`; g.stroke(); g.restore(); }
    for (let k = 0; k < 16; k++) {                    // dirt clods on arcs
      const a = -Math.PI / 2 + (hash(k * 3.3 + fx.t0) - 0.5) * 2.4, sp = 500 + hash(k * 7.1) * 700, px = x + Math.cos(a) * sp * u, py = y + Math.sin(a) * sp * u + 0.5 * 2600 * u * u;
      if (py < y + 10) { g.beginPath(); g.arc(px, py, 7 + hash(k) * 9, 0, 7); g.fillStyle = '#5a4430'; g.fill(); }
    }
    dustPuff(g, x, y, u, 1.6, r * 0.5, fx.t0 * 13, 0.75, '120,110,100');
  },
  storm(g, fx, s, t) {                                // a purple storm wall closing in (world plane)
    const u = clamp((t - fx.t0) / (fx.dur || 3)), x = lerp(fx.x0 ?? 0.95, fx.x1 ?? 0.5, ease(u)) * W;
    const gr = g.createLinearGradient(x - 220, 0, x + 260, 0); gr.addColorStop(0, 'rgba(150,60,220,0)'); gr.addColorStop(0.3, 'rgba(160,70,235,0.7)'); gr.addColorStop(1, 'rgba(110,30,190,0.9)');
    g.fillStyle = gr; g.fillRect(x - 220, -H, W * 3, H * 3);
    for (let k = 0; k < 18; k++) { const yy = (k / 18) * H * 1.6 - H * 0.3 + Math.sin(t * 1.4 + k) * 40, xx = x + 40 + hash(k) * 300 + Math.sin(t * 2 + k * 2) * 30;
      g.beginPath(); g.arc(xx, yy, 60 + hash(k * 3) * 90, 0, 7); g.fillStyle = `rgba(190,110,255,${0.12 + hash(k * 5) * 0.12})`; g.fill(); }
    const fl = Math.floor(t * 2.3); if (hash(fl * 7.7) > 0.55) { const lx = x + 100 + hash(fl) * 400; g.beginPath(); g.moveTo(lx, -100); for (let k = 1; k < 9; k++) g.lineTo(lx + (hash(fl * 3 + k) - 0.5) * 120, -100 + k * 160); g.lineWidth = 7; g.strokeStyle = 'rgba(240,220,255,0.85)'; g.stroke(); }
  },
  comet(g, fx, s, t) {                                // a comet streak with a glowing head
    const u = clamp((t - fx.t0) / (fx.dur || 1.4)); if (t < fx.t0) return;
    const x = lerp(fx.from[0], fx.to[0], u) * W, y = lerp(fx.from[1], fx.to[1], u) * H, ang = Math.atan2(fx.to[1] - fx.from[1], fx.to[0] - fx.from[0]);
    g.save(); g.translate(x, y); g.rotate(ang);
    const gr = g.createLinearGradient(-700, 0, 0, 0); gr.addColorStop(0, 'rgba(150,80,255,0)'); gr.addColorStop(1, 'rgba(220,180,255,0.9)');
    g.beginPath(); g.moveTo(-700, -14); g.lineTo(0, -46); g.lineTo(0, 46); g.lineTo(-700, 14); g.closePath(); g.fillStyle = gr; g.fill();
    glow2(g, 0, 0, 120, 'rgba(200,140,255,0.9)'); g.beginPath(); g.arc(0, 0, 34, 0, 7); g.fillStyle = '#f4e8ff'; g.fill(); g.restore();
  },
  tracer(g, fx, s, t) {                               // a bullet streak that misses
    const u = (t - fx.t0) / (fx.dur || 0.18); if (u < 0 || u > 1.6) return;
    const a = fx.from, b = fx.to, h = clamp(u), tl = clamp(u - 0.35);
    g.beginPath(); g.moveTo(lerp(a[0], b[0], tl) * W, lerp(a[1], b[1], tl) * H); g.lineTo(lerp(a[0], b[0], h) * W, lerp(a[1], b[1], h) * H);
    g.lineWidth = 9; g.lineCap = 'round'; g.strokeStyle = `rgba(255,236,150,${1 - clamp(u - 1) * 1.6})`; g.stroke();
    if (u < 0.15) glow2(g, a[0] * W, a[1] * H, 90, 'rgba(255,220,120,0.9)');
  },
  glint(g, fx, s, t) { const u = t - fx.t0; if (u < 0 || u > 0.6) return; const k = Math.sin(Math.PI * u / 0.6), x = fx.x * W, y = fx.y * H;
    glow2(g, x, y, 80 * k, 'rgba(255,255,255,0.95)'); g.save(); g.translate(x, y); g.rotate(u * 3); for (let i = 0; i < 4; i++) { g.rotate(Math.PI / 2); g.beginPath(); g.moveTo(0, -6); g.lineTo(90 * k, 0); g.lineTo(0, 6); g.fillStyle = '#fff'; g.fill(); } g.restore(); },
  burst(g, fx, s, t) {                                // a sparkle burst (purple by default)
    const u = (t - fx.t0) / (fx.dur || 0.7); if (u < 0 || u > 1) return; const x = fx.x * W, y = fx.y * H, col = fx.col || '190,110,255';
    glow2(g, x, y, 220 * eOut(u), `rgba(${col},${0.7 * (1 - u)})`);
    for (let k = 0; k < 14; k++) { const a = hash(k * 2.7 + fx.t0) * 6.283, d = (120 + hash(k) * 220) * eOut(u); star5(g, x + Math.cos(a) * d, y + Math.sin(a) * d, 16 * (1 - u) + 2, `rgba(${col},1)`); }
  },
  rushclouds(g, fx, s, t) {                           // cloud puffs rushing past (skydiving)
    for (let k = 0; k < (fx.n || 8); k++) { const sp = 900 + hash(k * 3.1) * 900, y = ((hash(k * 5.3) * 1.6 * H - (t - s.start) * sp * (fx.dir || 1)) % (1.6 * H) + 1.6 * H) % (1.6 * H) - 0.3 * H;
      const x = hash(k * 1.7) * W, r = 40 + hash(k * 9.1) * 70; for (let j = 0; j < 4; j++) { g.beginPath(); g.arc(x + (j - 1.5) * r * 0.6, y + Math.sin(j * 2) * r * 0.2, r * (0.6 + 0.2 * (j % 2)), 0, 7); g.fillStyle = 'rgba(214,196,240,0.28)'; g.fill(); } }
  },
  // ---- screen-space ----
  storm_tint(g, fx, s, t) { const k = clamp((t - fx.t0) / 0.5) * (fx.amount ?? 1); g.fillStyle = `rgba(120,40,200,${0.28 * k})`; g.fillRect(0, 0, W, H);
    const vg = g.createRadialGradient(W / 2, H / 2, H * 0.25, W / 2, H / 2, H * 0.7); vg.addColorStop(0, 'rgba(90,20,160,0)'); vg.addColorStop(1, `rgba(90,20,160,${0.55 * k})`); g.fillStyle = vg; g.fillRect(0, 0, W, H); },
  flash(g, fx, s, t) { const u = (t - fx.t0) / (fx.dur || 0.25); if (u < 0 || u > 1) return; g.fillStyle = `rgba(${fx.col || '255,255,255'},${(fx.amount ?? 0.9) * (1 - u)})`; g.fillRect(0, 0, W, H); },
  confetti(g, fx, s, t) {
    const u = t - fx.t0; if (u < 0) return; const cols = ['#ffd84a', '#ff5a5a', '#5ad1ff', '#7dff6a', '#d77dff'];
    for (let k = 0; k < 90; k++) { const x = hash(k * 1.3) * W + Math.sin(u * 3 + k) * 40, y = -80 + (u * (420 + hash(k * 2.1) * 380) + hash(k * 4.1) * 300) - 300; if (y > H + 40) continue;
      g.save(); g.translate(x, y); g.rotate(u * (4 + hash(k) * 6) + k); g.fillStyle = cols[k % 5]; g.fillRect(-11, -6, 22, 12); g.restore(); }
  },
  hud(g, fx, s, t) {                                  // a simple health bar (original design) that drains
    const u = clamp((t - fx.t0) / (fx.dur || 2)), v = lerp(fx.from ?? 1, fx.to ?? 0.2, ease(u));
    const x = 140, y = H * (fx.y ?? 0.13), w = 800, h = 56;
    g.save(); g.beginPath(); g.roundRect(x - 8, y - 8, w + 16, h + 16, 20); g.fillStyle = 'rgba(10,8,14,0.75)'; g.fill();
    g.beginPath(); g.roundRect(x, y, w * v, h, 14); g.fillStyle = v > 0.4 ? '#56d86a' : v > 0.2 ? '#f2c13a' : '#e8483a'; g.fill();
    g.font = '800 46px Poppins'; g.fillStyle = '#fff'; g.textAlign = 'left'; g.textBaseline = 'middle'; g.fillText('+', x - 62, y + h / 2 + 2);
    g.textAlign = 'right'; g.fillText(Math.round(v * 100), x + w - 16, y + h / 2 + 2); g.restore();
  },
  badge(g, fx, s, t) {                                // a gold #1 badge (original design) that pops in
    const k = popScale(t, fx.t0, 0.45); if (!k) return; const x = W / 2, y = H * (fx.y ?? 0.3);
    g.save(); g.translate(x, y); g.scale(k, k); g.rotate(Math.sin(t * 2) * 0.04);
    for (let i = 0; i < 16; i++) { g.rotate(Math.PI / 8); g.beginPath(); g.moveTo(-30, 0); g.lineTo(0, -330); g.lineTo(30, 0); g.fillStyle = 'rgba(255,220,90,0.25)'; g.fill(); }
    g.beginPath(); g.arc(0, 0, 170, 0, 7); g.fillStyle = '#f2b72e'; g.fill(); g.lineWidth = 12; g.strokeStyle = C.ink; g.stroke();
    g.beginPath(); g.arc(0, 0, 135, 0, 7); g.fillStyle = '#ffd84a'; g.fill(); g.lineWidth = 6; g.stroke();
    g.font = '800 170px Poppins'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.lineWidth = 14; g.strokeText('#1', 0, 10); g.fillStyle = '#fff'; g.fillText('#1', 0, 10); g.restore();
  },
};
window.FX2 = FX2; window.drawProp = drawProp; window.drawHandProp = drawHandProp;

// ---------------- ROCKETS V2: ripple-fired rockets on gravity arcs (fx type "rockets2") ----------------
// fx: {from:[x,y], to:[x,y], count, spread, ripple (s between launches), dur (flight s), arc (px apex height), seed,
//      blastR (px, knock-back radius at each landing; 0 = none), z}
function rocketsPlan(fx) {
  const n = fx.count || 20, out = [], sd = (fx.seed || 1) * 7.31;
  for (let i = 0; i < n; i++) {
    const r = k => hash(sd + i * 3.77 + k * 11.3);
    const t0 = fx.t0 + i * (fx.ripple ?? lerp(0.03, 0.06, r(1)));
    const x0 = fx.from[0] * W + (r(2) - 0.5) * (fx.fromSpread ?? 60), y0 = fx.from[1] * H + (r(3) - 0.5) * 20;
    const tx = fx.to[0] * W + (r(4) - 0.5) * (fx.spread ?? 400), ty = fx.to[1] * H + (r(5) - 0.5) * (fx.spread ?? 400) * 0.3;
    const T = (fx.dur || 1.1) * (0.88 + r(6) * 0.24), arc = (fx.arc ?? 380) * (0.8 + r(7) * 0.4), g = 8 * arc / (T * T);
    out.push({ t0, x0, y0, tx, ty, T, g, vx: (tx - x0) / T, vy: (ty - y0 - 0.5 * g * T * T) / T, i });
  }
  return out;
}
function rocketPos(p, tau) { return [p.x0 + p.vx * tau, p.y0 + p.vy * tau + 0.5 * p.g * tau * tau]; }
FX2.rockets2 = function (g, fx, s, t) {
  if (!fx._plan) fx._plan = rocketsPlan(fx);
  for (const p of fx._plan) {
    const tau = t - p.t0; if (tau < 0) continue;
    const life = p.T + 1.8; if (tau > life) continue;
    // launch: muzzle flash + smoke billowing backwards over the crew
    if (tau < 0.09) glow2(g, p.x0, p.y0, 120, `rgba(255,236,170,${0.9 * (1 - tau / 0.09)})`);
    if (tau < 1.0) for (let k = 0; k < 4; k++) { const a = Math.PI + Math.atan2(p.vy, p.vx) + (hash(p.i + k) - 0.5) * 1.2, d = 160 * eOut(tau);
      g.beginPath(); g.arc(p.x0 + Math.cos(a) * d * (0.6 + hash(k) * 0.6) + WIND[0] * tau, p.y0 + Math.sin(a) * d * 0.5 - 30 * tau, 30 + 60 * tau, 0, 7); g.fillStyle = `rgba(225,220,212,${0.4 * (1 - tau)})`; g.fill(); }
    // lingering smoke trail: puffs laid along the path, each growing and drifting with the wind
    const tEnd = Math.min(tau, p.T);
    for (let q = Math.max(0, tau - 1.8); q <= tEnd; q += 0.035) {
      const age = tau - q, [x, y] = rocketPos(p, q), k = age / 1.8;
      g.beginPath(); g.arc(x + WIND[0] * age, y + WIND[1] * age - 16 * age, 7 + 34 * age, 0, 7); g.fillStyle = `rgba(232,228,222,${0.3 * (1 - k) * (1 - k)})`; g.fill();
    }
    if (tau > p.T) { if (tau < p.T + 0.35) { const [x, y] = rocketPos(p, p.T), u = (tau - p.T) / 0.35; glow2(g, x, y - 20, 150 * (0.5 + u), `rgba(255,200,110,${0.9 * (1 - u)})`); dustPuff(g, x, y, tau - p.T, 1.2, 46, p.i * 9.1 + 3, 0.7, '120,105,95'); } continue; }
    // the rocket: body turned along its velocity, a flickering tail flame
    const [x, y] = rocketPos(p, tau), ang = Math.atan2(p.vy + p.g * tau, p.vx);
    g.save(); g.translate(x, y); g.rotate(ang);
    const fl = 0.75 + 0.25 * Math.sin(t * 60 + p.i * 2);
    glow2(g, -22, 0, 60 * fl, 'rgba(255,170,60,0.85)');
    g.beginPath(); g.moveTo(-14, -7); g.lineTo(-14 - 46 * fl, 0); g.lineTo(-14, 7); g.closePath(); g.fillStyle = '#ffd24a'; g.fill();
    g.beginPath(); g.moveTo(-14, -4); g.lineTo(-14 - 24 * fl, 0); g.lineTo(-14, 4); g.closePath(); g.fillStyle = '#fff6d0'; g.fill();
    inkRect(g, -16, -5, 34, 10, '#7a4a26', 3); g.beginPath(); g.moveTo(18, -6); g.lineTo(32, 0); g.lineTo(18, 6); g.closePath(); g.fillStyle = '#c9d0d8'; g.fill(); g.lineWidth = 3; g.strokeStyle = C.ink; g.stroke();
    g.restore();
  }
};
window.rocketsPlan = rocketsPlan;

// ---------------- 3D prop sprites (tools/props_blender.py) ----------------
// script.json "sprites": "props" loads <episode>/props/sprites.json + PNGs. A prop or hand prop with a sprite of the
// same name is drawn from it (anchored at its 'base' / 'grip' point); otherwise the vector version is used.
const SPRITES = {};
async function loadSprites(ep, dir) {
  try {
    const meta = await (await fetch('../' + ep + '/' + dir + '/sprites.json')).json();
    await Promise.all(Object.entries(meta).map(([k, m]) => new Promise(res => { const im = new Image(); im.onload = () => { SPRITES[k] = Object.assign({ img: im }, m); res(); }; im.onerror = () => res(); im.src = '../' + ep + '/' + dir + '/' + k + '.png'; })));
  } catch (e) { console.error('no sprites: ' + e.message); }
}
const SPRITE_SCALE = { shotgun: 0.56, sniper: 0.66, hoprock: 0.42, glider: 1.15, wall: 0.62, ramp: 0.62, stairs: 0.62, bus: 0.5 };
function drawSprite(g, name, anchor, k = 1) {
  const S = SPRITES[name]; if (!S) return false; const a = S[anchor] || [S.w / 2, S.h];
  g.save(); g.scale(k, k); g.drawImage(S.img, -a[0], -a[1]); g.restore(); return true;
}
const _vecProps = Object.assign({}, PROPS);
for (const name of ['wall', 'ramp', 'bus', 'hoprock']) PROPS[name] = function (g, p, s, t) {
  if (!SPRITES[name]) return _vecProps[name](g, p, s, t);
  const k = name === 'bus' ? 1 : popScale(t, p.t0); if (!k) return;
  if (name === 'bus') g.translate(0, Math.sin(t * 1.7) * 10), g.rotate(Math.sin(t * 1.3) * 0.03);
  g.scale(k, k); drawSprite(g, name, 'base', SPRITE_SCALE[name]);
  if (name !== 'bus' && p.t0 != null && t - p.t0 < 0.45) dustPuff(g, 0, 0, t - p.t0, 0.45, 80, 3, 0.6);
};
PROPS.stairs = function (g, p, s, t) {                 // a staircase built from stacked 3D stair pieces
  if (!SPRITES.stairs) return _vecProps.stairs(g, p, s, t);
  const S = SPRITES.stairs, n = Math.max(1, Math.round((p.steps || 6) / 6)), sc = SPRITE_SCALE.stairs, dx = S.w * sc * 0.36, dy = S.h * sc * 0.58;
  for (let i = 0; i < n; i++) { const k = popScale(t, p.t0 != null ? p.t0 + i * (p.rate || 0.05) * 6 : null); if (!k) continue;
    g.save(); g.translate((i % 2 ? -dx : dx) * 0.0 + (i % 2) * dx * 0.2, -i * dy); g.scale(k, k); drawSprite(g, 'stairs', 'base', sc); g.restore(); }
};
const _vecHand = drawHandProp;
drawHandProp = function (g, prop, hands, t, st) {
  if (!SPRITES[prop]) return _vecHand(g, prop, hands, t, st);
  const [hx, hy, ha] = hands[1], [lx, ly] = hands[0];
  g.save();
  if (prop === 'glider') { g.translate((hx + lx) / 2, Math.min(hy, ly) - 10); g.rotate(Math.sin(t * 2) * 0.05); drawSprite(g, 'glider', 'gripL', SPRITE_SCALE.glider); }
  else if (prop === 'hoprock') { g.translate(hx, hy - 6); drawSprite(g, 'hoprock', 'grip', SPRITE_SCALE.hoprock); }
  else { g.translate(hx, hy); g.rotate(Math.PI / 2 - ha); drawSprite(g, prop, 'grip', SPRITE_SCALE[prop] || 0.6); }
  g.restore();
};
window.drawHandProp = drawHandProp;

// ---------------- the logo slot and title text ----------------
// fx {type:'logo', img:'props/logo.png', x, y, w}: draws the user's logo file if it exists, otherwise styled text
const LOGOS = {};
FX2.logo = function (g, fx, s, t) {
  const k = popScale(t, fx.t0, 0.4); if (!k) return; const x = (fx.x ?? 0.5) * W, y = (fx.y ?? 0.2) * H;
  g.save(); g.translate(x, y); g.scale(k, k); g.rotate(Math.sin((t - fx.t0) * 2) * 0.02);
  const im = fx.img && LOGOS[fx.img];
  if (im) { const w = (fx.w ?? 0.8) * W, h = w * im.height / im.width; g.drawImage(im, -w / 2, -h / 2, w, h); }
  else {
    const lines = String(fx.text || 'VICTORY ROYALE').split('|'), size = fx.size || 120;
    g.font = `800 ${size}px Poppins`; g.textAlign = 'center'; g.textBaseline = 'middle'; g.lineJoin = 'round';
    lines.forEach((ln, i) => { const yy = (i - (lines.length - 1) / 2) * size * 1.02;
      const gr = g.createLinearGradient(0, yy - size / 2, 0, yy + size / 2); gr.addColorStop(0, '#fff6c2'); gr.addColorStop(0.45, '#ffd23a'); gr.addColorStop(1, '#e08a12');
      g.shadowColor = 'rgba(0,0,0,0.6)'; g.shadowBlur = 24; g.shadowOffsetY = 10; g.lineWidth = size * 0.2; g.strokeStyle = '#2a1640'; g.strokeText(ln, 0, yy);
      g.shadowColor = 'transparent'; g.lineWidth = size * 0.07; g.strokeStyle = '#7a3a10'; g.strokeText(ln, 0, yy); g.fillStyle = gr; g.fillText(ln, 0, yy); });
  }
  g.restore();
};
async function loadLogos(ep, script) {
  const names = new Set(); for (const sc of script.scenes) for (const fx of sc.fx || []) if (fx.type === 'logo' && fx.img) names.add(fx.img);
  await Promise.all([...names].map(n => new Promise(res => { const im = new Image(); im.onload = () => { LOGOS[n] = im; res(); }; im.onerror = () => res(); im.src = '../' + ep + '/' + n; })));
}
window.loadSprites = loadSprites; window.loadLogos = loadLogos;
