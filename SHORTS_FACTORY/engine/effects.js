// Effects drawn over the background: rocket-arrow volleys with flame heads and smoke trails, smoke puffs, sparks,
// impact bursts, warm fire glow and a cartoon "sneeze" puff. All deterministic functions of time.
function rocketVolley(g, fx, t) {
  // fx: {from:[x,y] px, to:[x,y] px, count, spread, dur, t0}
  const u0 = t - fx.t0; if (u0 < 0) return;
  const n = fx.count || 60, dur = fx.dur || 1.1;
  for (let i = 0; i < n; i++) {
    const delay = (hash(i * 1.7 + fx.seed) * 0.35), u = (u0 - delay) / dur;
    if (u <= 0 || u > 1.15) continue;
    const sx = fx.from[0] + (hash(i * 3.1 + fx.seed) - 0.5) * (fx.fromSpread || 160), sy = fx.from[1] + (hash(i * 5.3) - 0.5) * 40;
    const tx = fx.to[0] + (hash(i * 7.9 + fx.seed) - 0.5) * (fx.spread || 700), ty = fx.to[1] + (hash(i * 2.3 + fx.seed) - 0.5) * (fx.spread || 700) * 0.35;
    const arc = (fx.arc ?? -260) * (0.6 + hash(i) * 0.8);
    const p = (k) => { const v = Math.min(1, Math.max(0, k)); return [lerp(sx, tx, v), lerp(sy, ty, v) + arc * Math.sin(v * Math.PI)]; };
    const k = (v) => lerp(1, fx.persp ?? 1, Math.min(1, Math.max(0, v)));     // perspective: smaller as they fly away
    const [hx, hy] = p(u);
    // smoke trail: fading segments behind the head
    g.save(); g.lineCap = 'round';
    const fade = 1 - Math.max(0, u - 0.85) * 6;
    for (let q = 0; q < 6; q++) {
      const a0 = u - 0.04 * (q + 1), a1 = u - 0.04 * q; if (a1 <= 0) break;
      const [x0, y0] = p(Math.max(0, a0)), [x1, y1] = p(a1);
      g.globalAlpha = Math.max(0, 0.55 * (1 - q / 6) * fade); g.lineWidth = (9 + q * 3.5) * k(a1);
      g.strokeStyle = 'rgb(232,226,214)'; g.beginPath(); g.moveTo(x0, y0); g.lineTo(x1, y1); g.stroke();
    }
    g.restore();
    if (u > 1) continue;
    // shaft + glowing head
    const [ax, ay] = p(u - 0.035), kr = k(u);
    g.beginPath(); g.moveTo(ax, ay); g.lineTo(hx, hy); g.lineWidth = 6 * kr; g.strokeStyle = '#2a1d16'; g.lineCap = 'round'; g.stroke();
    const R = 32 * kr, gr = g.createRadialGradient(hx, hy, 0, hx, hy, R); gr.addColorStop(0, 'rgba(255,248,200,1)'); gr.addColorStop(0.35, 'rgba(255,160,50,0.95)'); gr.addColorStop(1, 'rgba(255,90,20,0)');
    g.fillStyle = gr; g.beginPath(); g.arc(hx, hy, R, 0, 7); g.fill();
  }
}
function puffs(g, x, y, t0, t, n = 6, size = 70, col = '235,230,220') {
  const u = t - t0; if (u < 0 || u > 1.4) return;
  for (let i = 0; i < n; i++) {
    const a = hash(i * 2.2) * Math.PI * 2, d = eOut(Math.min(1, u / 1.0)) * size * (1 + hash(i));
    const r = size * (0.5 + u * 0.8) * (0.7 + hash(i * 3) * 0.6);
    g.beginPath(); g.arc(x + Math.cos(a) * d, y + Math.sin(a) * d * 0.6 - u * 40, r, 0, 7);
    g.fillStyle = `rgba(${col},${0.75 * (1 - u / 1.4)})`; g.fill();
  }
}
function sparks(g, x, y, t, a = 1) {
  for (let i = 0; i < 10; i++) {
    const k = (t * 3 + hash(i)) % 1, an = hash(i * 7) * Math.PI * 2;
    g.beginPath(); g.arc(x + Math.cos(an) * k * 60, y + Math.sin(an) * k * 60 - k * 30, 4 * (1 - k), 0, 7);
    g.fillStyle = `rgba(255,${200 - k * 120},80,${a * (1 - k)})`; g.fill();
  }
}
function fireGlow(g, a, col = '255,120,40') {
  if (a <= 0) return;
  const gr = g.createLinearGradient(0, H, 0, H * 0.3); gr.addColorStop(0, `rgba(${col},${0.35 * a})`); gr.addColorStop(1, `rgba(${col},0)`);
  g.fillStyle = gr; g.fillRect(0, 0, W, H);
}
function impactBurst(g, x, y, t0, t, r = 220) { burst(g, x, y, r, (t - t0) / 0.4, '#fff3b0'); }
