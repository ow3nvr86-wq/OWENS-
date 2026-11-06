import React from "react";
import { C } from "../theme";
import { EXPRESSIONS, Expression } from "./BoltExpressions";

/**
 * BOLT — the permanent recurring character.
 *
 * One parametric SVG rig. Every scene renders this component; only pose,
 * expression and temporary prop interactions change. Proportions, colours,
 * face, antenna and mechanical features are fixed here and nowhere else.
 *
 * Local coordinates: origin = ground point between the feet, y grows downward
 * (so the character occupies negative y). Unscaled height ≈ 520 units.
 */

export type Limb = { a: number; b: number }; // a: upper angle (deg, 0 = straight down, + toward screen right); b: lower bend relative
export type HandShape = "open" | "fist" | "grab";

export type BoltPose = {
  x: number;
  y: number;
  scale: number;
  rot: number;
  sx: number;
  sy: number;
  lean: number;
  bodyY: number;
  headTilt: number;
  headY: number;
  /** -1..1 fake 3/4 head turn */
  turn: number;
  armL: Limb;
  armR: Limb;
  legL: Limb;
  legR: Limb;
  footL: number;
  footR: number;
  handL: HandShape;
  handR: HandShape;
  /** antenna angle in degrees */
  antenna: number;
  /** antenna length multiplier (springs up) */
  antennaStretch: number;
  /** extra antenna spin, degrees (spins wildly when panicking) */
  antennaSpin: number;
  /** 0..1: cartoon spinning-feet blur */
  legBlur: number;
  chestGlow: number;
  expr: Expression;
  /** ground shadow: distance from root down to the floor (0 = standing) */
  shadowLift: number;
  shadow: boolean;
  /** draw the right arm in front of the head (waving) */
  armRFront: boolean;
};

export const defaultPose = (): BoltPose => ({
  x: 0,
  y: 0,
  scale: 1,
  rot: 0,
  sx: 1,
  sy: 1,
  lean: 0,
  bodyY: 0,
  headTilt: 0,
  headY: 0,
  turn: 0,
  armL: { a: -14, b: 14 },
  armR: { a: 14, b: -14 },
  legL: { a: -3, b: 0 },
  legR: { a: 3, b: 0 },
  footL: 0,
  footR: 0,
  handL: "open",
  handR: "open",
  antenna: 0,
  antennaStretch: 1,
  antennaSpin: 0,
  legBlur: 0,
  chestGlow: 1,
  expr: EXPRESSIONS.neutral,
  shadowLift: 0,
  shadow: true,
  armRFront: false,
});

// ---- fixed design dimensions ----
const HIP_Y = -112;
const HIP_X = 33;
const THIGH = 38;
const SHIN = 36;
const SHOULDER_X = 70;
const SHOULDER_Y = -204;
const UPPER_ARM = 44;
const FOREARM = 40;
const NECK_Y = -238;
const HEAD_CY = -345;
const HEAD_W = 244;
const HEAD_H = 210;
const FACE_W = 198;
const FACE_H = 152;
const FACE_CY = -342;
const EYE_X = 47;
const EYE_Y = -354;
const EYE_RX = 31;
const EYE_RY = 37;
const MOUTH_Y = -297;
const STROKE = 6;
const FACE_COLOR = "#121C30";

const Leg: React.FC<{ side: -1 | 1; limb: Limb; foot: number; ids: Ids }> = ({ side, limb, foot, ids }) => (
  <g transform={`translate(${side * HIP_X} ${HIP_Y}) rotate(${-limb.a})`}>
    {/* thigh piston */}
    <rect x={-13} y={-4} width={26} height={THIGH + 8} rx={11} fill={`url(#${ids.steel})`} stroke={C.navy} strokeWidth={STROKE} />
    <rect x={-6} y={4} width={5} height={THIGH - 8} rx={2.5} fill={C.steelLight} opacity={0.7} />
    <g transform={`translate(0 ${THIGH}) rotate(${-limb.b})`}>
      <circle r={12} fill={C.steelDark} stroke={C.navy} strokeWidth={STROKE} />
      <rect x={-11} y={2} width={22} height={SHIN} rx={9} fill={`url(#${ids.steel})`} stroke={C.navy} strokeWidth={STROKE} />
      <g transform={`translate(0 ${SHIN}) rotate(${limb.a + limb.b - foot})`}>
        {/* bright orange mechanical foot */}
        <path
          d={`M ${-28 + side * 4} 6 Q ${-30 + side * 4} -4 ${-14 + side * 4} -4 L ${14 + side * 4} -4 Q ${34 + side * 4} -4 ${34 + side * 4} 14 L ${34 + side * 4} 26 Q ${34 + side * 4} 34 ${26 + side * 4} 34 L ${-22 + side * 4} 34 Q ${-30 + side * 4} 34 ${-30 + side * 4} 26 Z`}
          fill={`url(#${ids.foot})`}
          stroke={C.navy}
          strokeWidth={STROKE}
          strokeLinejoin="round"
        />
        <rect x={-20 + side * 4} y={1} width={40} height={6} rx={3} fill={C.orangeLight} opacity={0.75} />
        <rect x={-27 + side * 4} y={26} width={58} height={5} rx={2.5} fill="#B5521F" opacity={0.6} />
        <circle r={9} fill={C.steelDark} stroke={C.navy} strokeWidth={4} />
      </g>
    </g>
  </g>
);

const Hand: React.FC<{ shape: HandShape }> = ({ shape }) => {
  if (shape === "fist") {
    return <circle cx={0} cy={10} r={15} fill={C.steelLight} stroke={C.navy} strokeWidth={STROKE} />;
  }
  if (shape === "grab") {
    return (
      <g>
        <path d="M -16 2 Q -20 24 -6 28 L -4 18 Q -10 14 -8 4 Z" fill={C.steelLight} stroke={C.navy} strokeWidth={5} strokeLinejoin="round" />
        <path d="M 16 2 Q 20 24 6 28 L 4 18 Q 10 14 8 4 Z" fill={C.steelLight} stroke={C.navy} strokeWidth={5} strokeLinejoin="round" />
        <rect x={-12} y={-4} width={24} height={14} rx={6} fill={C.steel} stroke={C.navy} strokeWidth={5} />
      </g>
    );
  }
  // open mitten-claw
  return (
    <g>
      <path d="M -15 0 Q -21 26 -2 30 Q 6 31 8 22 L 3 18 Q 0 22 -4 19 Q -9 14 -6 2 Z" fill={C.steelLight} stroke={C.navy} strokeWidth={5} strokeLinejoin="round" />
      <path d="M 15 0 Q 22 20 12 28 L 6 22 Q 10 16 7 2 Z" fill={C.steelLight} stroke={C.navy} strokeWidth={5} strokeLinejoin="round" />
      <rect x={-13} y={-6} width={26} height={14} rx={6} fill={C.steel} stroke={C.navy} strokeWidth={5} />
    </g>
  );
};

const Arm: React.FC<{ side: -1 | 1; limb: Limb; hand: HandShape; ids: Ids }> = ({ side, limb, hand, ids }) => (
  <g transform={`translate(${side * SHOULDER_X} ${SHOULDER_Y}) rotate(${-limb.a})`}>
    <rect x={-12} y={-6} width={24} height={UPPER_ARM + 8} rx={11} fill={`url(#${ids.armTeal})`} stroke={C.navy} strokeWidth={STROKE} />
    <circle r={13} fill={C.steel} stroke={C.navy} strokeWidth={STROKE} />
    <circle r={4} fill={C.steelLight} />
    <g transform={`translate(0 ${UPPER_ARM}) rotate(${-limb.b})`}>
      <rect x={-11} y={0} width={22} height={FOREARM} rx={10} fill={`url(#${ids.armTeal})`} stroke={C.navy} strokeWidth={STROKE} />
      <circle r={11} fill={C.steel} stroke={C.navy} strokeWidth={STROKE} />
      <g transform={`translate(0 ${FOREARM})`}>
        <Hand shape={hand} />
      </g>
    </g>
  </g>
);

type Ids = ReturnType<typeof makeIds>;
const makeIds = (p: string) => ({
  teal: `${p}-teal`,
  armTeal: `${p}-armteal`,
  steel: `${p}-steel`,
  foot: `${p}-foot`,
  face: `${p}-face`,
  faceClip: `${p}-faceclip`,
  eye: `${p}-eye`,
  glow: `${p}-glow`,
  softGlow: `${p}-softglow`,
  chest: `${p}-chest`,
});

const Eye: React.FC<{ side: -1 | 1; e: Expression; ids: Ids; turn: number }> = ({ side, e, ids, turn }) => {
  const cx = side * EYE_X + turn * 20 + (turn * side > 0 ? -turn * 4 : 0);
  const cy = EYE_Y;
  // eyes nearer the turn direction get slightly smaller (fake perspective)
  const persp = 1 - Math.max(0, -turn * side) * 0.12;
  const rx = EYE_RX * e.eyeScale * persp;
  const ry = EYE_RY * e.eyeScale * Math.max(0.06, e.eyeOpen);
  const pr = 15 * e.pupil * e.eyeScale;
  const px = e.lookX * (rx - pr - 3) * 0.9;
  const py = e.lookY * (ry - pr - 3) * 0.9;
  const openOpacity = 1 - e.happy;
  const lidY = -ry + e.lidTop * ry * 2;
  const lowY = ry - e.lidBottom * ry * 2;
  return (
    <g transform={`translate(${cx} ${cy})`}>
      {/* glow halo */}
      <ellipse rx={rx * 1.35} ry={Math.max(ry, 8) * 1.3} fill={C.amber} opacity={0.22 * e.glow} filter={`url(#${ids.softGlow})`} />
      <defs>
        <clipPath id={`${ids.eye}-top${side}`}>
          <rect transform={`rotate(${-side * e.brow})`} x={-rx * 3} y={lidY} width={rx * 6} height={ry * 6 + 40} />
        </clipPath>
        <clipPath id={`${ids.eye}-bot${side}`}>
          <path d={`M ${-rx * 3} ${-ry * 6 - 40} L ${rx * 3} ${-ry * 6 - 40} L ${rx * 3} ${lowY + 6} Q 0 ${lowY - 14} ${-rx * 3} ${lowY + 6} Z`} />
        </clipPath>
      </defs>
      <g opacity={openOpacity} clipPath={`url(#${ids.eye}-top${side})`}>
        <g clipPath={e.lidBottom > 0.01 ? `url(#${ids.eye}-bot${side})` : undefined}>
          <ellipse rx={rx} ry={ry} fill={`url(#${ids.eye})`} filter={`url(#${ids.glow})`} />
          {e.eyeOpen > 0.25 && (
            <>
              <ellipse cx={px} cy={py} rx={pr} ry={Math.min(pr * 1.1, ry * 0.8)} fill={FACE_COLOR} />
              <circle cx={px - pr * 0.35} cy={py - pr * 0.4} r={Math.max(2.5, pr * 0.32)} fill={C.white} />
              {e.sparkle > 0 && (
                <g opacity={e.sparkle}>
                  <circle cx={px + pr * 0.45} cy={py + pr * 0.4} r={Math.max(1.5, pr * 0.15)} fill={C.white} />
                  <path d={`M ${-rx * 0.55} ${-ry * 0.55} l 4 -12 l 4 12 l 12 4 l -12 4 l -4 12 l -4 -12 l -12 -4 Z`} fill={C.white} opacity={0.9} />
                </g>
              )}
            </>
          )}
        </g>
      </g>
      {/* happy ^ ^ eyes */}
      {e.happy > 0.01 && (
        <path
          d={`M ${-rx * 0.85} ${8} Q 0 ${-ry * 0.95} ${rx * 0.85} ${8}`}
          fill="none"
          stroke={C.amber}
          strokeWidth={13}
          strokeLinecap="round"
          opacity={e.happy}
          filter={`url(#${ids.glow})`}
        />
      )}
    </g>
  );
};

const Mouth: React.FC<{ e: Expression; ids: Ids; turn: number }> = ({ e, ids, turn }) => {
  const w = 30 * e.mouthWidth;
  const o = e.mouthOpen;
  const common = {
    fill: "none",
    stroke: C.amber,
    strokeWidth: 8,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    filter: `url(#${ids.glow})`,
  };
  let el: React.ReactNode;
  switch (e.mouth) {
    case "grin":
      el = (
        <g filter={`url(#${ids.glow})`}>
          <path d={`M ${-w} -4 L ${w} -4 Q ${w} ${10 + 22 * o} 0 ${12 + 22 * o} Q ${-w} ${10 + 22 * o} ${-w} -4 Z`} fill={C.amber} stroke={C.amber} strokeWidth={5} strokeLinejoin="round" />
          <path d={`M ${-w * 0.7} 0 L ${w * 0.7} 0`} stroke={FACE_COLOR} strokeWidth={4} strokeDasharray="7 5" opacity={0.55} />
        </g>
      );
      break;
    case "open":
      el = <ellipse rx={w * 0.62} ry={6 + 18 * o} fill={C.amber} opacity={0.95} filter={`url(#${ids.glow})`} />;
      break;
    case "o":
    case "ooh":
      el = <ellipse rx={7 + 7 * o} ry={8 + 9 * o} {...common} />;
      break;
    case "flat":
      el = <path d={`M ${-w * 0.65} 4 L ${w * 0.65} 4`} {...common} strokeDasharray="9 5" />;
      break;
    case "frown":
      el = <path d={`M ${-w * 0.75} 10 Q 0 ${-8 - 6 * o} ${w * 0.75} 10`} {...common} />;
      break;
    case "wavy": {
      const a = 5 + 6 * o;
      const s = (w * 2) / 6;
      let d = `M ${-w} 0`;
      for (let i = 1; i <= 6; i++) d += ` L ${-w + s * i} ${i % 2 ? -a : a}`;
      el = <path d={d} {...common} strokeWidth={7} />;
      break;
    }
    case "smile":
    default:
      el = <path d={`M ${-w} -2 Q 0 ${10 + 22 * o} ${w} -2`} {...common} strokeDasharray="10 4" />;
  }
  return <g transform={`translate(${turn * 22} ${MOUTH_Y})`}>{el}</g>;
};

const Antenna: React.FC<{ p: BoltPose; ids: Ids }> = ({ p, ids }) => {
  const bx = 36 + p.turn * 14;
  const by = HEAD_CY - HEAD_H / 2 + 4;
  const st = p.antennaStretch;
  return (
    <g transform={`translate(${bx} ${by}) rotate(${p.antenna + p.antennaSpin})`}>
      <rect x={-13} y={-10} width={26} height={16} rx={6} fill={C.steel} stroke={C.navy} strokeWidth={STROKE} />
      {/* short, slightly crooked stem */}
      <path d={`M 0 -8 L ${-2} ${-30 * st} L ${11} ${-50 * st}`} fill="none" stroke={C.navy} strokeWidth={13} strokeLinecap="round" strokeLinejoin="round" />
      <path d={`M 0 -8 L ${-2} ${-30 * st} L ${11} ${-50 * st}`} fill="none" stroke={C.steelLight} strokeWidth={5} strokeLinecap="round" strokeLinejoin="round" />
      <circle cx={11} cy={-56 * st} r={20} fill={C.yellow} opacity={0.35} filter={`url(#${ids.softGlow})`} />
      <circle cx={11} cy={-56 * st} r={12} fill={C.yellow} stroke={C.navy} strokeWidth={STROKE} />
      <circle cx={7} cy={-60 * st} r={4} fill={C.white} opacity={0.9} />
    </g>
  );
};

export const Bolt: React.FC<{ pose: BoltPose; id?: string }> = ({ pose: p, id = "bolt" }) => {
  const ids = makeIds(id);
  const e = p.expr;
  const glowPulse = p.chestGlow;
  return (
    <g transform={`translate(${p.x} ${p.y}) rotate(${p.rot}) scale(${p.scale})`}>
      <defs>
        <linearGradient id={ids.teal} x1="0" y1="0" x2="0.35" y2="1">
          <stop offset="0" stopColor={C.tealLight} />
          <stop offset="0.55" stopColor={C.teal} />
          <stop offset="1" stopColor={C.tealDark} />
        </linearGradient>
        <linearGradient id={ids.armTeal} x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stopColor={C.tealLight} />
          <stop offset="1" stopColor={C.teal} />
        </linearGradient>
        <linearGradient id={ids.steel} x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stopColor={C.steelLight} />
          <stop offset="1" stopColor={C.steel} />
        </linearGradient>
        <linearGradient id={ids.foot} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor={C.orangeLight} />
          <stop offset="0.5" stopColor={C.orange} />
          <stop offset="1" stopColor="#D05E22" />
        </linearGradient>
        <linearGradient id={ids.face} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#1A2844" />
          <stop offset="1" stopColor={FACE_COLOR} />
        </linearGradient>
        <radialGradient id={ids.eye} cx="0.42" cy="0.38" r="0.7">
          <stop offset="0" stopColor={C.amberCore} />
          <stop offset="0.45" stopColor={C.amber} />
          <stop offset="1" stopColor="#F08A1C" />
        </radialGradient>
        <radialGradient id={ids.chest} cx="0.5" cy="0.5" r="0.5">
          <stop offset="0" stopColor="#FFE2B8" />
          <stop offset="0.5" stopColor={C.orange} />
          <stop offset="1" stopColor="#C4561C" />
        </radialGradient>
        <filter id={ids.glow} x="-60%" y="-60%" width="220%" height="220%">
          <feGaussianBlur stdDeviation="4" result="b" />
          <feMerge>
            <feMergeNode in="b" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
        <filter id={ids.softGlow} x="-100%" y="-100%" width="300%" height="300%">
          <feGaussianBlur stdDeviation="10" />
        </filter>
        <clipPath id={ids.faceClip}>
          <rect x={-FACE_W / 2 + p.turn * 10} y={FACE_CY - FACE_H / 2} width={FACE_W - Math.abs(p.turn) * 8} height={FACE_H} rx={46} />
        </clipPath>
      </defs>

      {/* ground shadow (stays on the floor while Bolt jumps) */}
      {p.shadow && (
        <ellipse
          cx={0}
          cy={p.shadowLift + 2}
          rx={95 * Math.max(0.35, 1 - p.shadowLift / 500)}
          ry={16 * Math.max(0.35, 1 - p.shadowLift / 500)}
          fill={C.navyDeep}
          opacity={0.38 * Math.max(0.3, 1 - p.shadowLift / 400)}
        />
      )}

      <g transform={`scale(${p.sx} ${p.sy})`}>
        {/* legs */}
        <g opacity={1 - p.legBlur * 0.85}>
          <Leg side={-1} limb={p.legL} foot={p.footL} ids={ids} />
          <Leg side={1} limb={p.legR} foot={p.footR} ids={ids} />
        </g>
        {p.legBlur > 0.01 && (
          <g opacity={p.legBlur} transform={`translate(0 -60)`}>
            <ellipse rx={74} ry={56} fill={C.orange} opacity={0.28} />
            <ellipse rx={64} ry={48} fill="none" stroke={C.orange} strokeWidth={16} strokeDasharray="38 22" />
            <ellipse rx={40} ry={30} fill="none" stroke={C.steelLight} strokeWidth={10} strokeDasharray="20 18" />
          </g>
        )}

        {/* upper body: leans around the hips */}
        <g transform={`translate(0 ${p.bodyY}) rotate(${p.lean} 0 ${HIP_Y})`}>
          {/* compact mechanical body */}
          <rect x={-58} y={-124} width={116} height={22} rx={10} fill={C.steelDark} stroke={C.navy} strokeWidth={STROKE} />
          <rect x={-76} y={-232} width={152} height={124} rx={34} fill={`url(#${ids.teal})`} stroke={C.navy} strokeWidth={STROKE} />
          <path d="M -60 -212 Q -66 -170 -58 -132" stroke={C.white} strokeWidth={8} strokeLinecap="round" fill="none" opacity={0.28} />
          <rect x={-46} y={-212} width={92} height={78} rx={20} fill={C.tealDark} opacity={0.35} />
          <circle cx={-52} cy={-134} r={4} fill={C.tealDark} />
          <circle cx={52} cy={-134} r={4} fill={C.tealDark} />
          {/* small orange glowing chest indicator */}
          <circle cx={0} cy={-172} r={30} fill={C.orange} opacity={0.32 * glowPulse} filter={`url(#${ids.softGlow})`} />
          <circle cx={0} cy={-172} r={16} fill={`url(#${ids.chest})`} stroke={C.navy} strokeWidth={5} />
          <circle cx={-5} cy={-177} r={4.5} fill={C.white} opacity={0.85} />
          <rect x={-24} y={-148} width={14} height={6} rx={3} fill={C.yellow} opacity={0.8} />
          <rect x={-6} y={-148} width={14} height={6} rx={3} fill={C.navy} opacity={0.5} />
          <rect x={12} y={-148} width={14} height={6} rx={3} fill={C.navy} opacity={0.5} />

          {/* short articulated arms */}
          <Arm side={-1} limb={p.armL} hand={p.handL} ids={ids} />
          {!p.armRFront && <Arm side={1} limb={p.armR} hand={p.handR} ids={ids} />}

          {/* neck + head */}
          <g transform={`translate(0 ${p.headY}) rotate(${p.headTilt} 0 ${NECK_Y})`}>
            <rect x={-24} y={-252} width={48} height={26} rx={8} fill={C.steel} stroke={C.navy} strokeWidth={STROKE} />
            <rect x={-16} y={-246} width={32} height={4} rx={2} fill={C.steelLight} />
            <Antenna p={p} ids={ids} />
            {/* large rounded-square head */}
            <rect x={-HEAD_W / 2} y={HEAD_CY - HEAD_H / 2} width={HEAD_W} height={HEAD_H} rx={64} fill={`url(#${ids.teal})`} stroke={C.navy} strokeWidth={STROKE} />
            <path
              d={`M ${-HEAD_W / 2 + 26} ${HEAD_CY - 40} Q ${-HEAD_W / 2 + 24} ${HEAD_CY - HEAD_H / 2 + 22} ${-40} ${HEAD_CY - HEAD_H / 2 + 16}`}
              stroke={C.white}
              strokeWidth={10}
              strokeLinecap="round"
              fill="none"
              opacity={0.3}
            />
            {/* face screen */}
            <rect
              x={-FACE_W / 2 + p.turn * 10}
              y={FACE_CY - FACE_H / 2}
              width={FACE_W - Math.abs(p.turn) * 8}
              height={FACE_H}
              rx={46}
              fill={`url(#${ids.face})`}
              stroke={C.navy}
              strokeWidth={STROKE}
            />
            <g clipPath={`url(#${ids.faceClip})`}>
              <Eye side={-1} e={e} ids={ids} turn={p.turn} />
              <Eye side={1} e={e} ids={ids} turn={p.turn} />
              <Mouth e={e} ids={ids} turn={p.turn} />
              {/* glass glare */}
              <path d={`M ${-70 + p.turn * 10} ${FACE_CY - 62} Q ${-30} ${FACE_CY - 74} ${20} ${FACE_CY - 70}`} stroke={C.white} strokeWidth={6} strokeLinecap="round" fill="none" opacity={0.12} />
            </g>
          </g>
          {p.armRFront && <Arm side={1} limb={p.armR} hand={p.handR} ids={ids} />}
        </g>
      </g>
    </g>
  );
};
