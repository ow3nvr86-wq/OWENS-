import React from "react";
import { AbsoluteFill, random } from "remotion";
import { C } from "../theme";

const CONFETTI_COLORS = [C.gold, C.orange, C.teal, C.pink, C.white, C.purple, C.yellow];

/** Deterministic confetti burst from (x,y) at time t0. World space. */
export const Confetti: React.FC<{ t: number; t0: number; x: number; y: number; count?: number; spread?: number; power?: number; seed?: string; gravity?: number }> = ({
  t, t0, x, y, count = 90, spread = 1, power = 1400, seed = "cf", gravity = 900,
}) => {
  if (t < t0) return null;
  const dt = t - t0;
  const pieces = [];
  for (let i = 0; i < count; i++) {
    const a = -Math.PI / 2 + (random(`${seed}a${i}`) - 0.5) * Math.PI * 1.1 * spread;
    const v = power * (0.45 + random(`${seed}v${i}`) * 0.65);
    const drag = 1.8;
    const k = (1 - Math.exp(-drag * dt)) / drag;
    const px = x + Math.cos(a) * v * k + Math.sin(dt * 3 + i) * 30 * dt;
    const py = y + Math.sin(a) * v * k + gravity * 0.35 * dt * dt + 120 * dt;
    const spin = dt * (6 + random(`${seed}s${i}`) * 10) + i;
    const w = 14 + random(`${seed}w${i}`) * 14;
    const col = CONFETTI_COLORS[i % CONFETTI_COLORS.length];
    const op = dt > 3.2 ? Math.max(0, 1 - (dt - 3.2) / 0.8) : 1;
    pieces.push(
      i % 4 === 0 ? (
        <circle key={i} cx={px} cy={py} r={w * 0.4} fill={col} opacity={op} />
      ) : (
        <rect key={i} x={-w / 2} y={-w * 0.3} width={w} height={w * 0.6 * Math.abs(Math.cos(spin))} fill={col} opacity={op} transform={`translate(${px} ${py}) rotate(${spin * 57})`} />
      ),
    );
  }
  return <g>{pieces}</g>;
};

/** Ambient falling confetti across the screen (screen space). */
export const ConfettiRain: React.FC<{ t: number; t0: number; count?: number; opacity?: number }> = ({ t, t0, count = 70, opacity = 1 }) => {
  if (t < t0) return null;
  const dt = t - t0;
  const els = [];
  for (let i = 0; i < count; i++) {
    const x = random(`rx${i}`) * 1080 + Math.sin(dt * 2 + i) * 40;
    const speed = 300 + random(`rs${i}`) * 400;
    const y = ((random(`ry${i}`) * 2200 + dt * speed) % 2200) - 200 - (dt < 1 ? (1 - dt) * 0 : 0);
    const startY = -100 - random(`rd${i}`) * 900 + dt * speed;
    const yy = dt < 2.5 ? startY : y;
    const spin = dt * 8 + i;
    els.push(
      <rect key={i} x={-9} y={-5} width={18} height={10 * Math.abs(Math.cos(spin))} fill={CONFETTI_COLORS[i % 7]} transform={`translate(${x} ${yy}) rotate(${spin * 50})`} opacity={opacity} />,
    );
  }
  return (
    <svg width={1080} height={1920} style={{ position: "absolute", inset: 0 }}>
      {els}
    </svg>
  );
};

/** Horizontal speed streaks (screen space). intensity 0..1 */
export const SpeedLines: React.FC<{ t: number; intensity: number; dir?: 1 | -1 }> = ({ t, intensity, dir = 1 }) => {
  if (intensity <= 0.01) return null;
  const lines = [];
  for (let i = 0; i < 26; i++) {
    const y = random(`sl${i}`) * 1920;
    const len = 200 + random(`sll${i}`) * 500;
    const speed = 2600 + random(`sls${i}`) * 1600;
    const x = (((random(`slx${i}`) * 2000 - t * speed * dir) % 2000) + 2000) % 2000 - 400;
    lines.push(<rect key={i} x={x} y={y} width={len} height={4 + random(`slh${i}`) * 6} rx={4} fill={C.white} opacity={0.18 * intensity + random(`slo${i}`) * 0.2 * intensity} />);
  }
  return (
    <svg width={1080} height={1920} style={{ position: "absolute", inset: 0 }}>
      {lines}
    </svg>
  );
};

/** Radial zoom lines (screen space) for dramatic hits. */
export const ZoomLines: React.FC<{ intensity: number; cx?: number; cy?: number; t: number; color?: string }> = ({ intensity, cx = 540, cy = 900, t, color = C.white }) => {
  if (intensity <= 0.01) return null;
  const rays = [];
  for (let i = 0; i < 40; i++) {
    const a = (i / 40) * Math.PI * 2 + random(`zl${i}`) * 0.1;
    const r0 = 420 + random(`zr${i}-${Math.floor(t * 15)}`) * 200;
    const r1 = 1400;
    const w = 0.012 + random(`zw${i}`) * 0.02;
    rays.push(
      <path
        key={i}
        d={`M ${cx + Math.cos(a - w) * r0} ${cy + Math.sin(a - w) * r0} L ${cx + Math.cos(a) * r1} ${cy + Math.sin(a) * r1} L ${cx + Math.cos(a + w) * r0} ${cy + Math.sin(a + w) * r0} Z`}
        fill={color}
        opacity={0.35 * intensity}
      />,
    );
  }
  return (
    <svg width={1080} height={1920} style={{ position: "absolute", inset: 0 }}>
      {rays}
    </svg>
  );
};

/** Dust puff cloud (world space). */
export const Dust: React.FC<{ t: number; t0: number; x: number; y: number; dir?: number; size?: number; seed?: string }> = ({ t, t0, x, y, dir = -1, size = 1, seed = "d" }) => {
  if (t < t0 || t > t0 + 0.7) return null;
  const k = (t - t0) / 0.7;
  const puffs = [];
  for (let i = 0; i < 7; i++) {
    const ox = dir * (30 + i * 28) * (0.4 + k) * size + (random(`${seed}x${i}`) - 0.5) * 40;
    const oy = -20 - random(`${seed}y${i}`) * 60 * k;
    puffs.push(<circle key={i} cx={x + ox} cy={y + oy} r={(18 + i * 4) * size * (0.6 + k)} fill="#D9E2EC" opacity={0.75 * (1 - k)} />);
  }
  return <g>{puffs}</g>;
};

/** Full-screen colour flash. */
export const Flash: React.FC<{ amount: number; color?: string }> = ({ amount, color = C.white }) =>
  amount > 0.001 ? <AbsoluteFill style={{ background: color, opacity: Math.min(1, amount) }} /> : null;

/** Rotating starburst (behind title text). */
export const Starburst: React.FC<{ x: number; y: number; r: number; t: number; color?: string; color2?: string; opacity?: number; rays?: number }> = ({
  x, y, r, t, color = C.gold, color2 = C.orange, opacity = 1, rays = 18,
}) => {
  const els = [];
  for (let i = 0; i < rays; i++) {
    const a0 = (i / rays) * Math.PI * 2;
    const a1 = ((i + 0.5) / rays) * Math.PI * 2;
    els.push(<path key={i} d={`M 0 0 L ${Math.cos(a0) * r} ${Math.sin(a0) * r} L ${Math.cos(a1) * r} ${Math.sin(a1) * r} Z`} fill={i % 2 ? color : color2} />);
  }
  return (
    <g transform={`translate(${x} ${y}) rotate(${t * 25})`} opacity={opacity}>
      {els}
    </g>
  );
};

/** Vignette + colour grade overlay. */
export const Grade: React.FC<{ vignette?: number; warm?: number; red?: number }> = ({ vignette = 0.55, warm = 0, red = 0 }) => (
  <>
    <AbsoluteFill style={{ background: `radial-gradient(ellipse at 50% 45%, rgba(0,0,0,0) 55%, rgba(5,8,18,${vignette}) 100%)` }} />
    {warm > 0 && <AbsoluteFill style={{ background: `radial-gradient(ellipse at 50% 40%, rgba(255,190,90,${0.28 * warm}) 0%, rgba(240,120,54,${0.12 * warm}) 60%, rgba(0,0,0,0) 100%)`, mixBlendMode: "screen" }} />}
    {red > 0 && <AbsoluteFill style={{ background: `radial-gradient(ellipse at 50% 50%, rgba(0,0,0,0) 40%, rgba(232,67,58,${0.45 * red}) 100%)` }} />}
  </>
);

/** Floating hearts (world or screen space). */
export const Hearts: React.FC<{ t: number; t0: number; x: number; y: number; count?: number; seed?: string; spread?: number }> = ({ t, t0, x, y, count = 10, seed = "h", spread = 500 }) => {
  if (t < t0) return null;
  const els = [];
  for (let i = 0; i < count; i++) {
    const st = t0 + random(`${seed}t${i}`) * 1.2;
    if (t < st) continue;
    const dt = t - st;
    const life = 1.8;
    if (dt > life) continue;
    const k = dt / life;
    const hx = x + (random(`${seed}x${i}`) - 0.5) * spread + Math.sin(dt * 4 + i) * 20;
    const hy = y - dt * 260;
    const s = 0.6 + random(`${seed}s${i}`) * 0.7;
    els.push(<HeartShape key={i} x={hx} y={hy} s={s * Math.min(1, dt * 5)} opacity={1 - k} />);
  }
  return <g>{els}</g>;
};

export const HeartShape: React.FC<{ x: number; y: number; s?: number; opacity?: number; color?: string }> = ({ x, y, s = 1, opacity = 1, color = "#FF4F6D" }) => (
  <g transform={`translate(${x} ${y}) scale(${s})`} opacity={opacity}>
    <path d="M 0 30 C -50 -5 -40 -45 -14 -42 C -4 -41 0 -32 0 -26 C 0 -32 4 -41 14 -42 C 40 -45 50 -5 0 30 Z" fill={color} stroke={C.navy} strokeWidth={6} strokeLinejoin="round" />
    <ellipse cx={-16} cy={-26} rx={8} ry={5} fill={C.white} opacity={0.6} transform="rotate(-30 -16 -26)" />
  </g>
);

/** Motion-blur whip-pan overlay (screen space). amount 0..1 */
export const Whip: React.FC<{ amount: number; t: number; dir?: 1 | -1 }> = ({ amount, t, dir = 1 }) => {
  if (amount <= 0.01) return null;
  return (
    <>
      <AbsoluteFill style={{ background: `linear-gradient(${dir > 0 ? 90 : 270}deg, rgba(24,36,56,${0.5 * amount}), rgba(255,255,255,${0.25 * amount}), rgba(24,36,56,${0.5 * amount}))` }} />
      <SpeedLines t={t} intensity={amount * 2} dir={dir} />
    </>
  );
};
