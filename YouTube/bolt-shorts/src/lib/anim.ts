import { Easing, interpolate, random } from "remotion";
import timeline from "../timeline.json";

export const FPS = timeline.fps;
export const W = timeline.width;
export const H = timeline.height;
export const B = timeline.beats;

export type Ease = (t: number) => number;
export const ease = {
  linear: (t: number) => t,
  in: Easing.in(Easing.cubic),
  out: Easing.out(Easing.cubic),
  inOut: Easing.inOut(Easing.cubic),
  outBack: Easing.out(Easing.back(1.8)),
  outBackBig: Easing.out(Easing.back(3)),
  inBack: Easing.in(Easing.back(1.6)),
  outExpo: Easing.out(Easing.exp),
  inExpo: Easing.in(Easing.exp),
  outQuad: Easing.out(Easing.quad),
  inQuad: Easing.in(Easing.quad),
  inOutSine: Easing.inOut(Easing.sin),
};

/** Clamped interpolation over seconds. */
export const lerpT = (t: number, t0: number, t1: number, v0: number, v1: number, e: Ease = ease.inOut) =>
  interpolate(t, [t0, t1], [v0, v1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: e });

/** Piecewise keyframes: [[time, value, easeIntoThisKey?], ...] */
export type Key = [number, number] | [number, number, Ease];
export const keys = (t: number, ks: Key[]): number => {
  if (t <= ks[0][0]) return ks[0][1];
  for (let i = 1; i < ks.length; i++) {
    const [t1, v1, e] = ks[i] as [number, number, Ease | undefined];
    const [t0, v0] = ks[i - 1];
    if (t <= t1) return lerpT(t, t0, t1, v0, v1, e ?? ease.inOut);
  }
  return ks[ks.length - 1][1];
};

export const clamp01 = (v: number) => Math.max(0, Math.min(1, v));
export const mix = (a: number, b: number, t: number) => a + (b - a) * t;
export const progress = (t: number, t0: number, t1: number) => clamp01((t - t0) / (t1 - t0));

/** Damped spring impulse that starts at `t0` (0 before). Returns overshooting 0->1. */
export const springAt = (t: number, t0: number, stiffness = 14, damping = 5) => {
  if (t < t0) return 0;
  const x = t - t0;
  return 1 - Math.exp(-damping * x) * Math.cos(stiffness * x);
};

/** Decaying wobble (impulse) that starts at t0: sin wave with exponential decay. */
export const wobble = (t: number, t0: number, freq = 18, decay = 6, amp = 1) => {
  if (t < t0) return 0;
  const x = t - t0;
  return amp * Math.sin(freq * x) * Math.exp(-decay * x);
};

/** Smooth deterministic noise in [-1,1]. */
export const noise = (seed: string, t: number) => {
  const i = Math.floor(t);
  const f = t - i;
  const a = random(`${seed}-${i}`) * 2 - 1;
  const b = random(`${seed}-${i + 1}`) * 2 - 1;
  const s = f * f * (3 - 2 * f);
  return a + (b - a) * s;
};

/** Camera shake offset for an impact at t0. */
export const shake = (t: number, t0: number, strength = 30, dur = 0.45, seed = "s") => {
  if (t < t0 || t > t0 + dur) return { x: 0, y: 0, r: 0 };
  const k = 1 - (t - t0) / dur;
  const s = strength * k * k;
  return {
    x: noise(seed + "x", t * 40) * s,
    y: noise(seed + "y", t * 40) * s,
    r: noise(seed + "r", t * 30) * s * 0.04,
  };
};

export const sumShake = (...s: { x: number; y: number; r: number }[]) =>
  s.reduce((a, b) => ({ x: a.x + b.x, y: a.y + b.y, r: a.r + b.r }), { x: 0, y: 0, r: 0 });

/** Challenge clock value (seconds remaining) for video time t. */
export const timerValue = (t: number) => {
  const ks = timeline.timer.keys as [number, number][];
  if (t <= ks[0][0]) return ks[0][1];
  for (let i = 1; i < ks.length; i++) {
    if (t <= ks[i][0]) {
      const [t0, v0] = ks[i - 1];
      const [t1, v1] = ks[i];
      return v0 + ((t - t0) / (t1 - t0)) * (v1 - v0);
    }
  }
  return ks[ks.length - 1][1];
};

export const fmtTimer = (v: number) => {
  const s = Math.max(0, v);
  const whole = Math.floor(s);
  const tenth = Math.floor((s - whole) * 10);
  return `${String(whole).padStart(2, "0")}.${tenth}`;
};
