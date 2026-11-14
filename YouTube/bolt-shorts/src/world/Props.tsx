import React from "react";
import { C, FONT_DISPLAY } from "../theme";

/** A single banded cash bundle (front view). */
export const CashBundle: React.FC<{ x: number; y: number; w?: number; h?: number; rot?: number }> = ({ x, y, w = 120, h = 54, rot = 0 }) => (
  <g transform={`translate(${x} ${y}) rotate(${rot})`}>
    <rect x={-w / 2} y={-h / 2} width={w} height={h} rx={6} fill={C.cash} stroke={C.navy} strokeWidth={5} />
    <rect x={-w / 2 + 6} y={-h / 2 + 6} width={w - 12} height={h - 12} rx={4} fill="none" stroke={C.cashDark} strokeWidth={3} />
    <circle r={h * 0.26} fill={C.cashDark} />
    <text y={h * 0.13} textAnchor="middle" fontFamily={FONT_DISPLAY} fontSize={h * 0.4} fill={C.cash}>$</text>
    <rect x={-w * 0.12} y={-h / 2} width={w * 0.24} height={h} fill={C.gold} stroke={C.navy} strokeWidth={4} />
  </g>
);

/** A flying banknote (used for the donation stream). */
export const Bill: React.FC<{ x: number; y: number; rot: number; flip?: number; s?: number }> = ({ x, y, rot, flip = 1, s = 1 }) => (
  <g transform={`translate(${x} ${y}) rotate(${rot}) scale(${s} ${s * flip})`}>
    <rect x={-46} y={-22} width={92} height={44} rx={5} fill={C.cash} stroke={C.navy} strokeWidth={4} />
    <circle r={12} fill={C.cashDark} />
    <text y={7} textAnchor="middle" fontFamily={FONT_DISPLAY} fontSize={20} fill={C.cash}>$</text>
  </g>
);

export const Coin: React.FC<{ x: number; y: number; spin: number; r?: number }> = ({ x, y, spin, r = 24 }) => (
  <g transform={`translate(${x} ${y}) scale(${Math.max(0.15, Math.abs(Math.cos(spin)))} 1)`}>
    <circle r={r} fill={C.gold} stroke={C.navy} strokeWidth={4} />
    <circle r={r * 0.68} fill="none" stroke={C.goldDeep} strokeWidth={3} />
    <text y={r * 0.32} textAnchor="middle" fontFamily={FONT_DISPLAY} fontSize={r * 0.9} fill={C.goldDeep}>$</text>
  </g>
);

const formatMoney = (v: number) => "$" + Math.round(v).toLocaleString("en-US");

/**
 * The massive $100,000 prize display: gold-framed glass vault full of cash on a
 * pedestal, topped by an LED amount panel.
 * fill: 0..1 how much cash remains; lit: glow; flash: white flash amount.
 */
export const PrizeDisplay: React.FC<{
  x: number;
  y: number; // bottom (floor) point
  scale?: number;
  t: number;
  lit?: number;
  flash?: number;
  fill?: number;
  amount?: number;
  label?: string;
  ledOpacity?: number;
}> = ({ x, y, scale = 1, t, lit = 0.6, flash = 0, fill = 1, amount = 100000, label, ledOpacity = 1 }) => {
  const w = 720;
  const caseH = 560;
  const ped = 110;
  const bundles: React.ReactNode[] = [];
  const rows = 7;
  let idx = 0;
  const total = 7 + 6 + 6 + 5 + 4 + 3 + 2;
  for (let r = 0; r < rows; r++) {
    const n = [7, 6, 6, 5, 4, 3, 2][r];
    for (let i = 0; i < n; i++) {
      idx++;
      const visible = idx / total <= fill + 0.0001;
      if (!visible) continue;
      const bx = (i - (n - 1) / 2) * 94;
      const by = -ped - 40 - r * 58;
      bundles.push(<CashBundle key={`${r}-${i}`} x={bx} y={by} w={90} h={52} rot={((r * 7 + i * 13) % 5) - 2} />);
    }
  }
  const glow = lit + flash;
  const sparkles = [];
  for (let i = 0; i < 9; i++) {
    const ph = (t * 1.3 + i * 0.37) % 1;
    const sx = Math.sin(i * 12.9898) * 280;
    const sy = -ped - 60 - ((i * 73) % 380);
    const s = Math.sin(ph * Math.PI);
    sparkles.push(
      <path key={i} transform={`translate(${sx} ${sy}) scale(${s * 1.3})`} d="M 0 -18 L 5 -5 L 18 0 L 5 5 L 0 18 L -5 5 L -18 0 L -5 -5 Z" fill={C.white} opacity={0.85 * fill} />,
    );
  }
  return (
    <g transform={`translate(${x} ${y}) scale(${scale})`}>
      {/* halo */}
      <ellipse cx={0} cy={-ped - caseH / 2} rx={w * 0.8} ry={caseH * 0.75} fill={C.gold} opacity={0.18 * glow} />
      {/* pedestal */}
      <rect x={-w / 2 - 30} y={-ped} width={w + 60} height={ped} rx={18} fill={C.navyMid} stroke={C.navy} strokeWidth={8} />
      <rect x={-w / 2 - 30} y={-ped} width={w + 60} height={22} rx={10} fill={C.gold} stroke={C.navy} strokeWidth={6} />
      <text x={0} y={-24} textAnchor="middle" fontFamily={FONT_DISPLAY} fontSize={54} fill={C.gold} opacity={0.9}>{label ?? "GRAND PRIZE"}</text>
      {/* glass case */}
      <rect x={-w / 2} y={-ped - caseH} width={w} height={caseH} rx={26} fill="#9FE6FF" fillOpacity={0.1} stroke={C.gold} strokeWidth={14} />
      {bundles}
      <path d={`M ${-w / 2 + 40} ${-ped - caseH + 40} L ${-w / 2 + 140} ${-ped - caseH + 40} L ${-w / 2 + 40} ${-ped - 120} Z`} fill={C.white} opacity={0.12} />
      {sparkles}
      <rect x={-w / 2} y={-ped - caseH} width={w} height={caseH} rx={26} fill={C.white} opacity={flash * 0.6} />
      {/* LED amount panel */}
      <g transform={`translate(0 ${-ped - caseH - 90})`} opacity={ledOpacity}>
        <rect x={-w / 2 + 20} y={-80} width={w - 40} height={160} rx={30} fill={C.navyDeep} stroke={C.gold} strokeWidth={10} />
        <text
          y={45}
          textAnchor="middle"
          fontFamily={FONT_DISPLAY}
          fontSize={128}
          fill={C.gold}
          stroke={C.goldDeep}
          strokeWidth={3}
          style={{ filter: `drop-shadow(0 0 ${12 + 20 * glow}px rgba(255,212,71,${0.5 + 0.4 * Math.min(1, glow)}))` }}
        >
          {formatMoney(amount)}
        </text>
      </g>
    </g>
  );
};

/** Giant digital countdown board. */
export const TimerBoard: React.FC<{ x: number; y: number; scale?: number; text: string; danger?: number; stopped?: boolean; flashOn?: boolean }> = ({
  x, y, scale = 1, text, danger = 0, stopped = false, flashOn = true,
}) => {
  const color = stopped ? "#5CF08A" : danger > 0.5 ? C.red : C.orange;
  return (
    <g transform={`translate(${x} ${y}) scale(${scale})`}>
      <rect x={-250} y={-110} width={500} height={220} rx={36} fill={C.navyDeep} stroke={stopped ? "#5CF08A" : danger > 0.5 ? C.red : C.yellow} strokeWidth={12} />
      <rect x={-220} y={-82} width={440} height={164} rx={22} fill="#0A0F1A" />
      <text y={58} textAnchor="middle" fontFamily={FONT_DISPLAY} fontSize={150} fill={color} opacity={flashOn ? 1 : 0.35} style={{ filter: `drop-shadow(0 0 18px ${color})` }}>
        {text}
      </text>
      <rect x={-60} y={-142} width={120} height={36} rx={10} fill={C.steelDark} stroke={C.navy} strokeWidth={6} />
    </g>
  );
};

/** Giant foam hammer on a pendulum. Pivot at (x,y); angle in degrees. */
export const FoamHammer: React.FC<{ x: number; y: number; length: number; angle: number; color?: string; drop?: number }> = ({
  x, y, length, angle, color = C.pink, drop = 0,
}) => (
  <g transform={`translate(${x} ${y - drop})`}>
    <rect x={-60} y={-40} width={120} height={40} rx={10} fill={C.steelDark} stroke={C.navy} strokeWidth={6} />
    <g transform={`rotate(${angle})`}>
      <rect x={-14} y={0} width={28} height={length} rx={10} fill={C.steelLight} stroke={C.navy} strokeWidth={6} />
      <rect x={-6} y={10} width={6} height={length - 20} fill={C.white} opacity={0.4} />
      <g transform={`translate(0 ${length})`}>
        <rect x={-150} y={-80} width={300} height={160} rx={70} fill={color} stroke={C.navy} strokeWidth={8} />
        <rect x={-150} y={-80} width={60} height={160} rx={30} fill={C.white} opacity={0.18} />
        <rect x={-36} y={-80} width={72} height={160} fill={C.yellow} stroke={C.navy} strokeWidth={6} />
        <path d="M -120 -40 Q -60 -66 0 -60" stroke={C.white} strokeWidth={10} strokeLinecap="round" fill="none" opacity={0.45} />
      </g>
    </g>
  </g>
);

/** Colourful striped track segment. Top surface at y. */
export const Track: React.FC<{ x0: number; x1: number; y: number; color?: string; rise?: number; thickness?: number }> = ({
  x0, x1, y, color = C.teal, rise = 0, thickness = 120,
}) => (
  <g transform={`translate(0 ${rise})`}>
    <rect x={x0} y={y} width={x1 - x0} height={thickness} rx={14} fill={color} stroke={C.navy} strokeWidth={8} />
    <rect x={x0 + 8} y={y + 8} width={x1 - x0 - 16} height={16} rx={6} fill={C.white} opacity={0.25} />
    {Array.from({ length: Math.floor((x1 - x0) / 120) }).map((_, i) => (
      <rect key={i} x={x0 + 30 + i * 120} y={y + 40} width={60} height={22} rx={6} fill={C.yellow} opacity={0.85} />
    ))}
    <rect x={x0 + 20} y={y + thickness} width={40} height={900} fill={C.steelDark} stroke={C.navy} strokeWidth={6} />
    <rect x={x1 - 60} y={y + thickness} width={40} height={900} fill={C.steelDark} stroke={C.navy} strokeWidth={6} />
  </g>
);

/** Pit filled with bouncy foam cubes (or slime). */
export const FoamPit: React.FC<{ x0: number; x1: number; y: number; t: number; slime?: boolean }> = ({ x0, x1, y, t, slime }) => {
  const cubes = [];
  const cols = [C.pink, C.yellow, C.teal, C.orange, C.purple];
  if (!slime) {
    for (let i = 0; x0 + i * 70 < x1; i++) {
      for (let r = 0; r < 3; r++) {
        cubes.push(
          <rect
            key={`${i}-${r}`}
            x={x0 + i * 70 + (r % 2) * 30}
            y={y + r * 50 + Math.sin(t * 3 + i + r) * 4}
            width={66}
            height={60}
            rx={14}
            fill={cols[(i * 3 + r) % cols.length]}
            stroke={C.navy}
            strokeWidth={5}
            transform={`rotate(${((i * 17 + r * 11) % 30) - 15} ${x0 + i * 70 + 33} ${y + r * 50 + 30})`}
          />,
        );
      }
    }
  }
  return (
    <g>
      <rect x={x0} y={y - 40} width={x1 - x0} height={1000} fill={slime ? "#3D1F5C" : "#1A1530"} />
      {slime && (
        <>
          <path
            d={`M ${x0} ${y + 60} ${Array.from({ length: 24 }).map((_, i) => `Q ${x0 + ((i + 0.5) * (x1 - x0)) / 24} ${y + 60 + Math.sin(t * 4 + i) * 18} ${x0 + ((i + 1) * (x1 - x0)) / 24} ${y + 60}`).join(" ")} L ${x1} ${y + 1000} L ${x0} ${y + 1000} Z`}
            fill={C.pink}
          />
          <path
            d={`M ${x0} ${y + 90} ${Array.from({ length: 24 }).map((_, i) => `Q ${x0 + ((i + 0.5) * (x1 - x0)) / 24} ${y + 90 + Math.cos(t * 3 + i) * 14} ${x0 + ((i + 1) * (x1 - x0)) / 24} ${y + 90}`).join(" ")} L ${x1} ${y + 1000} L ${x0} ${y + 1000} Z`}
            fill={C.purple}
          />
        </>
      )}
      {cubes}
    </g>
  );
};

/** Small moving platform (top at y). */
export const MovingPlatform: React.FC<{ x: number; y: number; w?: number; color?: string }> = ({ x, y, w = 200, color = C.orange }) => (
  <g transform={`translate(${x} ${y})`}>
    <rect x={-w / 2} y={0} width={w} height={46} rx={14} fill={color} stroke={C.navy} strokeWidth={8} />
    <rect x={-w / 2 + 10} y={8} width={w - 20} height={10} rx={5} fill={C.white} opacity={0.35} />
    <rect x={-14} y={46} width={28} height={70} fill={C.steelDark} stroke={C.navy} strokeWidth={5} />
    <circle cy={130} r={22} fill={C.yellow} stroke={C.navy} strokeWidth={5} />
    <path d="M -10 122 L 0 140 L 10 122" stroke={C.navy} strokeWidth={4} fill="none" />
  </g>
);

/** Narrow moving plank bridge with hazard stripes. */
export const Bridge: React.FC<{ x0: number; x1: number; y: number; tilt?: number }> = ({ x0, x1, y, tilt = 0 }) => {
  const cx = (x0 + x1) / 2;
  return (
    <g transform={`rotate(${tilt} ${cx} ${y})`}>
      <rect x={x0} y={y} width={x1 - x0} height={34} rx={10} fill={C.yellow} stroke={C.navy} strokeWidth={7} />
      {Array.from({ length: Math.floor((x1 - x0) / 50) }).map((_, i) => (
        <path key={i} d={`M ${x0 + 14 + i * 50} ${y + 30} l 24 -26`} stroke={C.navy} strokeWidth={10} />
      ))}
      <path d={`M ${x0 + 20} ${y} L ${cx} -400 L ${x1 - 20} ${y}`} stroke={C.steelLight} strokeWidth={5} fill="none" opacity={0.7} />
    </g>
  );
};

/** Giant arcade-style push button on a pedestal (top of pedestal at y). */
export const BigButton: React.FC<{
  x: number;
  y: number;
  press?: number;
  color?: string;
  dark?: string;
  label?: string;
  scale?: number;
  glow?: number;
}> = ({ x, y, press = 0, color = C.red, dark = C.redDark, label = "FINISH", scale = 1, glow = 0 }) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    {glow > 0 && <ellipse cx={0} cy={-80} rx={200} ry={120} fill={color} opacity={0.25 * glow} />}
    <rect x={-90} y={0} width={180} height={190} rx={18} fill={C.navyMid} stroke={C.navy} strokeWidth={8} />
    <rect x={-90} y={60} width={180} height={50} fill={C.yellow} stroke={C.navy} strokeWidth={6} />
    <text x={0} y={98} textAnchor="middle" fontFamily={FONT_DISPLAY} fontSize={38} fill={C.navy}>{label}</text>
    <rect x={-120} y={-34} width={240} height={44} rx={16} fill={C.steel} stroke={C.navy} strokeWidth={8} />
    <g transform={`translate(0 ${press * 26})`}>
      <path d="M -100 -26 L -100 -60 Q -100 -130 0 -130 Q 100 -130 100 -60 L 100 -26 Z" fill={color} stroke={C.navy} strokeWidth={8} />
      <path d="M -100 -60 Q -100 -130 0 -130 Q 100 -130 100 -60 Q 100 -20 0 -20 Q -100 -20 -100 -60 Z" fill={dark} opacity={0.0} />
      <ellipse cx={-40} cy={-96} rx={30} ry={14} fill={C.white} opacity={0.45} />
    </g>
  </g>
);

/** Start pad with chequered line. */
export const StartPad: React.FC<{ x0: number; x1: number; y: number }> = ({ x0, x1, y }) => (
  <g>
    <rect x={x0} y={y} width={x1 - x0} height={140} rx={16} fill={C.navyMid} stroke={C.navy} strokeWidth={8} />
    {Array.from({ length: Math.floor((x1 - x0 - 20) / 30) }).map((_, i) =>
      [0, 1].map((r) => (
        <rect key={`${i}-${r}`} x={x0 + 10 + i * 30} y={y + 8 + r * 26} width={30} height={26} fill={(i + r) % 2 ? C.white : C.navy} />
      )),
    )}
    <text x={(x0 + x1) / 2} y={y + 120} textAnchor="middle" fontFamily={FONT_DISPLAY} fontSize={50} fill={C.yellow}>START</text>
  </g>
);
