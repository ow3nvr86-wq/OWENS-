/**
 * Bolt's reusable facial-expression states.
 * Only the face changes between states — never the design.
 */
export type MouthShape = "smile" | "grin" | "open" | "o" | "flat" | "wavy" | "frown" | "ooh";

export type Expression = {
  /** overall eye size multiplier */
  eyeScale: number;
  /** 0 = closed, 1 = open */
  eyeOpen: number;
  /** pupil look direction, -1..1 */
  lookX: number;
  lookY: number;
  /** pupil size multiplier (0.4 = terrified pin-pricks) */
  pupil: number;
  /** lid angle in degrees: + = determined / angry, - = worried */
  brow: number;
  /** how far the top lid drops, 0..1 */
  lidTop: number;
  /** how far the bottom lid rises (smile squint), 0..1 */
  lidBottom: number;
  /** 0..1 morph into happy ^ ^ arcs */
  happy: number;
  mouth: MouthShape;
  /** mouth openness 0..1 */
  mouthOpen: number;
  /** mouth width multiplier */
  mouthWidth: number;
  /** glow intensity of eyes + mouth */
  glow: number;
  /** sparkle highlights in the eyes (money eyes, joy) */
  sparkle: number;
};

const base: Expression = {
  eyeScale: 1,
  eyeOpen: 1,
  lookX: 0,
  lookY: 0,
  pupil: 1,
  brow: 0,
  lidTop: 0,
  lidBottom: 0,
  happy: 0,
  mouth: "smile",
  mouthOpen: 0.3,
  mouthWidth: 1,
  glow: 1,
  sparkle: 0,
};

const make = (e: Partial<Expression>): Expression => ({ ...base, ...e });

export const EXPRESSIONS = {
  neutral: make({}),
  curious: make({ lookY: -0.3, brow: -6, mouth: "o", mouthOpen: 0.4, mouthWidth: 0.7 }),
  excited: make({ eyeScale: 1.22, pupil: 1.15, mouth: "grin", mouthOpen: 0.9, sparkle: 1, glow: 1.25 }),
  amazed: make({ eyeScale: 1.38, pupil: 0.9, lookY: -0.55, mouth: "open", mouthOpen: 1, sparkle: 1, glow: 1.35 }),
  determined: make({ brow: 18, lidTop: 0.28, pupil: 0.95, mouth: "flat", mouthOpen: 0, mouthWidth: 0.9 }),
  focused: make({ brow: 12, lidTop: 0.18, mouth: "grin", mouthOpen: 0.45, mouthWidth: 0.85 }),
  startled: make({ eyeScale: 1.32, pupil: 0.6, brow: -8, mouth: "o", mouthOpen: 0.9, mouthWidth: 0.8 }),
  scared: make({ eyeScale: 1.2, pupil: 0.65, brow: -16, lidTop: 0.1, mouth: "wavy", mouthOpen: 0.6 }),
  terrified: make({ eyeScale: 1.5, pupil: 0.42, brow: -14, mouth: "wavy", mouthOpen: 1, mouthWidth: 1.2, glow: 1.3 }),
  strain: make({ brow: 16, lidTop: 0.42, lidBottom: 0.25, pupil: 0.8, mouth: "wavy", mouthOpen: 0.3, mouthWidth: 1.1 }),
  relieved: make({ happy: 0.6, lidTop: 0.2, mouth: "smile", mouthOpen: 0.5 }),
  joyful: make({ happy: 1, mouth: "grin", mouthOpen: 1, mouthWidth: 1.15, glow: 1.4 }),
  happy: make({ lidBottom: 0.22, pupil: 1.1, mouth: "grin", mouthOpen: 0.7, sparkle: 0.6 }),
  soft: make({ lidTop: 0.16, lidBottom: 0.2, pupil: 1.2, brow: -5, mouth: "smile", mouthOpen: 0.35, mouthWidth: 0.85, sparkle: 0.5 }),
  thoughtful: make({ lookX: 0.8, lookY: -0.1, brow: -4, lidTop: 0.12, mouth: "flat", mouthOpen: 0, mouthWidth: 0.7 }),
  warmSmile: make({ lidBottom: 0.24, lidTop: 0.08, pupil: 1.25, sparkle: 0.8, mouth: "smile", mouthOpen: 0.7, mouthWidth: 1.05, glow: 1.2 }),
} satisfies Record<string, Expression>;

export type ExpressionName = keyof typeof EXPRESSIONS;

const num = (a: number, b: number, t: number) => a + (b - a) * t;

/** Blend two expressions. Discrete mouth shape swaps at the midpoint. */
export const blendExpr = (a: Expression, b: Expression, t: number): Expression => {
  const k = Math.max(0, Math.min(1, t));
  return {
    eyeScale: num(a.eyeScale, b.eyeScale, k),
    eyeOpen: num(a.eyeOpen, b.eyeOpen, k),
    lookX: num(a.lookX, b.lookX, k),
    lookY: num(a.lookY, b.lookY, k),
    pupil: num(a.pupil, b.pupil, k),
    brow: num(a.brow, b.brow, k),
    lidTop: num(a.lidTop, b.lidTop, k),
    lidBottom: num(a.lidBottom, b.lidBottom, k),
    happy: num(a.happy, b.happy, k),
    mouth: k < 0.5 ? a.mouth : b.mouth,
    mouthOpen: num(a.mouthOpen, b.mouthOpen, k),
    mouthWidth: num(a.mouthWidth, b.mouthWidth, k),
    glow: num(a.glow, b.glow, k),
    sparkle: num(a.sparkle, b.sparkle, k),
  };
};

/**
 * Expression track: [[time, name, blendSeconds?], ...]. Each entry blends in from the
 * previous state over `blendSeconds` (default 0.15s).
 */
export type ExprKey = [number, ExpressionName | Expression, number?];
export const exprTrack = (t: number, track: ExprKey[]): Expression => {
  const get = (e: ExpressionName | Expression) => (typeof e === "string" ? EXPRESSIONS[e] : e);
  let cur = get(track[0][1]);
  for (let i = 1; i < track.length; i++) {
    const [ti, e, dur = 0.15] = track[i];
    if (t < ti) break;
    cur = blendExpr(cur, get(e), (t - ti) / dur);
  }
  return cur;
};

/** Natural blink: returns eyeOpen multiplier. */
export const blink = (t: number, times: number[], dur = 0.16) => {
  for (const bt of times) {
    if (t >= bt && t <= bt + dur) {
      const x = (t - bt) / dur;
      return Math.abs(Math.cos(x * Math.PI));
    }
  }
  return 1;
};
