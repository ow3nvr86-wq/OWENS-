/**
 * Reusable motion functions for Bolt. Each takes a pose (plus time) and returns
 * a new pose, so moves can be layered: run(jump(idle(pose))).
 * All times are in seconds.
 */
import { BoltPose, Limb, defaultPose } from "./Bolt";
import { springAt, wobble, clamp01, mix, progress, ease, noise } from "../lib/anim";

const P = (p: BoltPose, patch: Partial<BoltPose>): BoltPose => ({ ...p, ...patch });
const limb = (a: number, b: number): Limb => ({ a, b });
const mixLimb = (x: Limb, y: Limb, t: number): Limb => ({ a: mix(x.a, y.a, t), b: mix(x.b, y.b, t) });

/** Blend every numeric field of two poses (discrete fields come from whichever side t is nearer to). */
export const blendPose = (a: BoltPose, b: BoltPose, t: number): BoltPose => {
  const k = clamp01(t);
  const n = (x: number, y: number) => mix(x, y, k);
  return {
    ...(k < 0.5 ? a : b),
    x: n(a.x, b.x),
    y: n(a.y, b.y),
    scale: n(a.scale, b.scale),
    rot: n(a.rot, b.rot),
    sx: n(a.sx, b.sx),
    sy: n(a.sy, b.sy),
    lean: n(a.lean, b.lean),
    bodyY: n(a.bodyY, b.bodyY),
    headTilt: n(a.headTilt, b.headTilt),
    headY: n(a.headY, b.headY),
    turn: n(a.turn, b.turn),
    armL: mixLimb(a.armL, b.armL, k),
    armR: mixLimb(a.armR, b.armR, k),
    legL: mixLimb(a.legL, b.legL, k),
    legR: mixLimb(a.legR, b.legR, k),
    footL: n(a.footL, b.footL),
    footR: n(a.footR, b.footR),
    antenna: n(a.antenna, b.antenna),
    antennaStretch: n(a.antennaStretch, b.antennaStretch),
    antennaSpin: n(a.antennaSpin, b.antennaSpin),
    legBlur: n(a.legBlur, b.legBlur),
    chestGlow: n(a.chestGlow, b.chestGlow),
    shadowLift: n(a.shadowLift, b.shadowLift),
  };
};

/** Gentle breathing, antenna sway and chest pulse. */
export const idle = (p: BoltPose, t: number): BoltPose =>
  P(p, {
    bodyY: p.bodyY + Math.sin(t * 3.2) * 3,
    headY: p.headY + Math.sin(t * 3.2 - 0.5) * 2,
    antenna: p.antenna + Math.sin(t * 2.4) * 5,
    chestGlow: 0.85 + 0.15 * Math.sin(t * 5),
  });

/** Walk cycle in direction dir (1 = right). */
export const walk = (p: BoltPose, t: number, dir: 1 | -1 = 1, rate = 1.6): BoltPose => {
  const ph = t * rate * Math.PI * 2;
  const s = Math.sin(ph);
  return P(p, {
    legL: limb(dir * 18 * s, -dir * (6 + 20 * Math.max(0, -s))),
    legR: limb(-dir * 18 * s, -dir * (6 + 20 * Math.max(0, s))),
    armL: limb(-14 - dir * 14 * s, 16),
    armR: limb(14 - dir * 14 * s, -16),
    bodyY: p.bodyY - Math.abs(Math.cos(ph)) * 6,
    lean: p.lean + dir * 4,
    turn: dir * 0.35,
    antenna: p.antenna - dir * 6 + Math.sin(ph * 2) * 4,
  });
};

/** Cartoon sprint: big leg swings, pumping arms, forward lean, bounce. */
export const run = (p: BoltPose, t: number, dir: 1 | -1 = 1, rate = 3): BoltPose => {
  const ph = t * rate * Math.PI * 2;
  const s = Math.sin(ph);
  const back = (v: number) => Math.max(0, -v * dir);
  return P(p, {
    legL: limb(dir * 40 * s, -dir * (14 + 70 * back(s))),
    legR: limb(-dir * 40 * s, -dir * (14 + 70 * back(-s))),
    footL: dir * 10 * s,
    footR: -dir * 10 * s,
    armL: limb(-20 - dir * 48 * s, dir * 70),
    armR: limb(20 + dir * 48 * s, dir * 70),
    handL: "fist",
    handR: "fist",
    bodyY: p.bodyY - Math.abs(s) * 12,
    y: p.y - Math.abs(Math.cos(ph)) * 14,
    lean: p.lean + dir * 13,
    headTilt: p.headTilt - dir * 3,
    turn: dir * 0.6,
    antenna: p.antenna - dir * 22 + Math.sin(ph * 2) * 8,
    sy: p.sy * (1 + Math.cos(ph * 2) * 0.03),
  });
};

/**
 * Jump arc between takeoff t0 and landing t1. Includes anticipation squash
 * (before t0), stretch on takeoff, tucked legs, and landing squash (after t1).
 */
export const jump = (p: BoltPose, t: number, t0: number, t1: number, height = 300, dir: 1 | -1 = 1): BoltPose => {
  const pre = 0.12;
  if (t < t0 - pre) return p;
  if (t < t0) {
    const k = progress(t, t0 - pre, t0);
    return P(p, { sy: p.sy * mix(1, 0.82, k), sx: p.sx * mix(1, 1.12, k), bodyY: p.bodyY + 10 * k, legL: limb(-12, 30 * k), legR: limb(12, -30 * k) });
  }
  if (t <= t1) {
    const k = progress(t, t0, t1);
    const arc = 4 * k * (1 - k);
    const stretch = k < 0.3 ? mix(1.2, 1, k / 0.3) : k > 0.8 ? mix(1, 1.1, (k - 0.8) / 0.2) : 1;
    return P(p, {
      y: p.y - height * arc,
      shadowLift: height * arc,
      sy: p.sy * stretch,
      sx: p.sx / Math.sqrt(stretch),
      legL: limb(dir * 30, -dir * 80),
      legR: limb(dir * 6, -dir * 60),
      armL: limb(-120, -30),
      armR: limb(120, 30),
      handL: "open",
      handR: "open",
      rot: p.rot + dir * 12 * Math.sin(k * Math.PI),
      antenna: p.antenna + (k < 0.5 ? -25 : 30) * dir,
      antennaStretch: 1 + 0.25 * Math.sin(k * Math.PI),
    });
  }
  // landing squash spring
  const s = wobble(t, t1, 22, 9, 1);
  return P(p, { sy: p.sy * (1 - 0.18 * s), sx: p.sx * (1 + 0.14 * s), antenna: p.antenna + 20 * s });
};

/** Duck under something: squash down, head tucks, arms over head. Strength 0..1. */
export const duck = (p: BoltPose, k: number): BoltPose =>
  blendPose(
    p,
    P(p, {
      sy: p.sy * 0.66,
      sx: p.sx * 1.16,
      bodyY: p.bodyY + 20,
      armL: limb(-150, -70),
      armR: limb(150, 70),
      legL: limb(-30, 60),
      legR: limb(30, -60),
      antenna: -60,
      lean: p.lean + 6,
    }),
    k,
  );

/** Slip & fall: feet fly up, body tilts backward. k = 0..1 through the fall. */
export const slipFall = (p: BoltPose, t: number, k: number, dir: 1 | -1 = 1): BoltPose => {
  const flail = Math.sin(t * 28);
  return P(p, {
    rot: p.rot - dir * 70 * ease.out(k),
    legL: limb(dir * (60 + 30 * k) + flail * 14, -dir * 20),
    legR: limb(dir * (85 + 30 * k) - flail * 14, -dir * 10),
    armL: limb(-150 + flail * 25, -40 + flail * 20),
    armR: limb(150 - flail * 25, 40 - flail * 20),
    handL: "open",
    handR: "open",
    antennaSpin: p.antennaSpin + t * 900,
    lean: p.lean - dir * 10,
  });
};

/** Hanging from a ledge with one hand (right hand up). Swing amount 0..1, effort pulls body up. */
export const hang = (p: BoltPose, t: number, swing = 1, effort = 0): BoltPose => {
  const sw = Math.sin(t * 4.2) * 6 * swing;
  const kick = Math.sin(t * 16) * (12 + 20 * effort);
  return P(p, {
    rot: p.rot + sw,
    armR: limb(178 - effort * 18, effort * 40),
    handR: "grab",
    armL: limb(-120 + Math.sin(t * 12) * 30 * (1 - effort) - effort * 50, -50 + Math.sin(t * 14) * 30),
    handL: effort > 0.5 ? "grab" : "open",
    legL: limb(-10 + kick, 20 + kick),
    legR: limb(10 - kick, -20 - kick),
    antennaSpin: p.antennaSpin,
  });
};

/** Quick look left/right/up sequence between t0 and t1. */
export const lookAround = (p: BoltPose, t: number, t0: number, t1: number): BoltPose => {
  const k = progress(t, t0, t1);
  const lx = Math.sin(k * Math.PI * 2) * 0.9;
  return P(p, {
    turn: p.turn + lx * 0.6,
    headTilt: p.headTilt + lx * 6,
    expr: { ...p.expr, lookX: lx, lookY: -0.2 * Math.sin(k * Math.PI) },
  });
};

/** Surprise take at t0: jolt upward, antenna springs, eyes pop, arms fling out. */
export const surprised = (p: BoltPose, t: number, t0: number): BoltPose => {
  if (t < t0) return p;
  const sp = springAt(t, t0, 16, 6);
  const jolt = wobble(t, t0, 14, 7, 1);
  const pop = Math.max(0, jolt);
  return P(p, {
    y: p.y - 40 * pop,
    sy: p.sy * (1 + 0.12 * jolt),
    sx: p.sx * (1 - 0.06 * jolt),
    antennaStretch: p.antennaStretch * (1 + 0.45 * Math.max(0, jolt)),
    antenna: p.antenna + 12 * wobble(t, t0, 30, 5, 1),
    armL: mixLimb(p.armL, limb(-95, -40), sp),
    armR: mixLimb(p.armR, limb(95, 40), sp),
    handL: "open",
    handR: "open",
    expr: { ...p.expr, eyeScale: p.expr.eyeScale * (1 + 0.18 * Math.max(0, jolt)) },
  });
};

/** Celebration: arms pumping overhead, little hops. */
export const celebrate = (p: BoltPose, t: number, t0: number): BoltPose => {
  if (t < t0) return p;
  const x = t - t0;
  const s = Math.sin(x * 14);
  return P(p, {
    armL: limb(-160 + s * 18, -20 + s * 20),
    armR: limb(160 + s * 18, 20 + s * 20),
    handL: "fist",
    handR: "fist",
    bodyY: p.bodyY - Math.abs(s) * 8,
    headTilt: p.headTilt + s * 5,
    antenna: p.antenna + s * 18,
  });
};

/** Friendly wave with the right arm (the side nearest camera-right). */
export const wave = (p: BoltPose, t: number, t0: number, strength = 1): BoltPose => {
  if (t < t0) return p;
  const k = clamp01((t - t0) / 0.25) * strength;
  const s = Math.sin((t - t0) * 13);
  return P(p, {
    armR: mixLimb(p.armR, limb(118, 22 + s * 28), k),
    handR: "open",
    armRFront: k > 0.3,
    headTilt: p.headTilt + 5 * k + s * 2 * k,
    bodyY: p.bodyY - 3 * s * k,
  });
};

/** Spinning-feet wind-up before launching (cartoon peel-out). */
export const windUp = (p: BoltPose, t: number, k: number, dir: 1 | -1 = 1): BoltPose =>
  P(p, {
    legBlur: k,
    lean: p.lean + dir * 22 * k,
    armL: mixLimb(p.armL, limb(-dir * 60, dir * 40), k),
    armR: mixLimb(p.armR, limb(-dir * 40 + 20, dir * 60), k),
    handL: "fist",
    handR: "fist",
    bodyY: p.bodyY + Math.sin(t * 60) * 3 * k,
    antenna: p.antenna - dir * 35 * k + Math.sin(t * 50) * 6 * k,
    turn: dir * 0.5 * k,
  });

/** Crouch at the starting line, ready stance. k = 0..1 */
export const crouch = (p: BoltPose, k: number, dir: 1 | -1 = 1): BoltPose =>
  blendPose(
    p,
    P(p, {
      sy: p.sy * 0.9,
      bodyY: p.bodyY + 14,
      lean: p.lean + dir * 16,
      legL: limb(-dir * 22, dir * 36),
      legR: limb(dir * 24, -dir * 30),
      armL: limb(-dir * 40 - 10, dir * 60),
      armR: limb(dir * 10 + 20, dir * 70),
      handL: "fist",
      handR: "fist",
      turn: dir * 0.4,
    }),
    k,
  );

/** Reach out and press a button to the right. k = 0..1 (1 = pressed). */
export const pressRight = (p: BoltPose, k: number): BoltPose =>
  blendPose(p, P(p, { armR: limb(82 + 6 * k, -4), handR: "fist", lean: p.lean + 8 * k, turn: 0.45 }), clamp01(k * 1.4));

/** Panicked limb jitter for tense moments (amount 0..1). */
export const jitter = (p: BoltPose, t: number, amount: number): BoltPose =>
  P(p, {
    x: p.x + noise("jx", t * 30) * 4 * amount,
    antenna: p.antenna + noise("ja", t * 25) * 25 * amount,
  });

export { defaultPose };
