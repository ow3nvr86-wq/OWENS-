import React from "react";
import { random } from "remotion";
import { C, FONT_DISPLAY } from "../theme";
import { Cam, Parallax } from "./Camera";

/** Original challenge-show identity: "MEGA DASH" with a lightning-dash mark. */
export const ShowLogo: React.FC<{ x: number; y: number; scale?: number; t: number; lit?: number }> = ({ x, y, scale = 1, t, lit = 1 }) => {
  const bulbs = [];
  const w = 760;
  const h = 250;
  for (let i = 0; i < 30; i++) {
    const u = i / 30;
    const per = 2 * (w + h);
    let d = u * per;
    let bx: number, by: number;
    if (d < w) { bx = -w / 2 + d; by = -h / 2; }
    else if ((d -= w) < h) { bx = w / 2; by = -h / 2 + d; }
    else if ((d -= h) < w) { bx = w / 2 - d; by = h / 2; }
    else { d -= w; bx = -w / 2; by = h / 2 - d; }
    const on = (Math.floor(t * 8) + i) % 3 !== 0;
    bulbs.push(<circle key={i} cx={bx} cy={by} r={11} fill={on ? C.gold : "#6B5320"} opacity={on ? lit : 0.6} />);
  }
  return (
    <g transform={`translate(${x} ${y}) scale(${scale})`}>
      <rect x={-w / 2 - 30} y={-h / 2 - 30} width={w + 60} height={h + 60} rx={50} fill={C.gold} opacity={0.12 * lit} />
      <rect x={-w / 2} y={-h / 2} width={w} height={h} rx={40} fill={C.navyDeep} stroke={C.gold} strokeWidth={10} />
      {bulbs}
      <path d="M -300 -70 L -240 -70 L -270 -5 L -225 -5 L -320 95 L -290 15 L -335 15 Z" fill={C.yellow} stroke={C.navy} strokeWidth={6} />
      <text x={40} y={-8} textAnchor="middle" fontFamily={FONT_DISPLAY} fontSize={110} fill={C.orange} stroke={C.navy} strokeWidth={10} paintOrder="stroke">MEGA</text>
      <text x={40} y={92} textAnchor="middle" fontFamily={FONT_DISPLAY} fontSize={110} fill={C.gold} stroke={C.navy} strokeWidth={10} paintOrder="stroke">DASH!</text>
    </g>
  );
};

/** Crowd stands: rows of silhouettes with phone/camera flashes. Tiled across a wide span. */
const Crowd: React.FC<{ x0: number; x1: number; y: number; t: number; excite?: number }> = ({ x0, x1, y, t, excite = 0 }) => {
  const rows = 5;
  const els: React.ReactNode[] = [];
  const colors = ["#2A3B5C", "#34486E", "#283654", "#3A4F78"];
  for (let r = 0; r < rows; r++) {
    const yy = y + r * 64;
    const step = 46;
    for (let xx = x0 + (r % 2) * 23; xx < x1; xx += step) {
      const k = random(`c${r}-${xx}`);
      const bounce = excite > 0 ? Math.abs(Math.sin(t * 9 + k * 10)) * 14 * excite : Math.sin(t * 2 + k * 8) * 2;
      els.push(
        <g key={`${r}-${xx}`} transform={`translate(${xx} ${yy - bounce})`}>
          <circle cy={-30} r={15} fill={colors[Math.floor(k * 4)]} />
          <rect x={-20} y={-16} width={40} height={50} rx={16} fill={colors[Math.floor(k * 4)]} />
          {excite > 0.3 && k > 0.6 && <rect x={k > 0.8 ? 12 : -26} y={-62} width={10} height={36} rx={5} fill={colors[Math.floor(k * 4)]} />}
        </g>,
      );
      if (k > 0.93 && Math.floor(t * 6 + k * 50) % 7 === 0) {
        els.push(<circle key={`f${r}-${xx}`} cx={xx} cy={yy - 30} r={10} fill={C.white} opacity={0.9} />);
      }
    }
  }
  return <g>{els}</g>;
};

/** Sweeping spotlight beam (gradient trapezoid, no blur filter for speed). */
const Beam: React.FC<{ x: number; y: number; angle: number; color: string; length?: number; width?: number; opacity?: number; id: string }> = ({
  x, y, angle, color, length = 1700, width = 380, opacity = 0.35, id,
}) => (
  <g transform={`translate(${x} ${y}) rotate(${angle})`}>
    <defs>
      <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stopColor={color} stopOpacity={opacity} />
        <stop offset="1" stopColor={color} stopOpacity={0} />
      </linearGradient>
    </defs>
    <path d={`M -18 0 L 18 0 L ${width / 2} ${length} L ${-width / 2} ${length} Z`} fill={`url(#${id})`} />
    <circle r={26} fill={color} opacity={0.9} />
    <circle r={14} fill={C.white} />
  </g>
);

/**
 * Massive arena backdrop: back wall, crowd stands, truss, sweeping spotlights and
 * giant signage. Rendered with parallax so the venue feels enormous.
 */
export const ArenaBackdrop: React.FC<{
  cam: Cam;
  t: number;
  span?: [number, number];
  excite?: number;
  warm?: number;
  logoXs?: number[];
}> = ({ cam, t, span = [-2000, 8000], excite = 0, warm = 0, logoXs = [540] }) => {
  const [a, b] = span;
  const beams = [];
  const colors = [C.yellow, C.teal, C.orange, C.white, C.pink];
  for (let i = 0, xx = a; xx < b; xx += 520, i++) {
    beams.push(
      <Beam key={i} id={`beam${i}`} x={xx} y={-120} angle={Math.sin(t * 1.4 + i * 1.7) * 28} color={colors[i % colors.length]} opacity={0.22 + 0.12 * excite} />,
    );
  }
  return (
    <g>
      <defs>
        <linearGradient id="wallGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#0A1120" />
          <stop offset="0.55" stopColor={C.navy} />
          <stop offset="1" stopColor="#243756" />
        </linearGradient>
      </defs>
      <Parallax cam={cam} factor={0.25}>
        <rect x={a - 3000} y={-2500} width={b - a + 6000} height={6000} fill="url(#wallGrad)" />
        <Crowd x0={a - 1500} x1={b + 1500} y={420} t={t} excite={excite} />
        <rect x={a - 3000} y={735} width={b - a + 6000} height={36} fill={C.navyMid} />
        <rect x={a - 3000} y={735} width={b - a + 6000} height={8} fill={C.teal} opacity={0.8} />
      </Parallax>
      <Parallax cam={cam} factor={0.45}>
        {logoXs.map((lx) => (
          <ShowLogo key={lx} x={lx} y={70} scale={0.7} t={t} lit={0.8} />
        ))}
        <rect x={a - 3000} y={-140} width={b - a + 6000} height={46} fill={C.steelDark} />
        {Array.from({ length: Math.ceil((b - a + 6000) / 90) }).map((_, i) => (
          <path key={i} d={`M ${a - 3000 + i * 90} -140 l 45 46 l 45 -46`} stroke={C.steel} strokeWidth={6} fill="none" />
        ))}
        {beams}
      </Parallax>
      {warm > 0 && <rect x={a - 4000} y={-3000} width={b - a + 8000} height={7000} fill={C.orange} opacity={0.12 * warm} />}
    </g>
  );
};

/** Glossy stage floor with stripes. */
export const StageFloor: React.FC<{ x0: number; x1: number; y: number; depth?: number }> = ({ x0, x1, y, depth = 1400 }) => (
  <g>
    <defs>
      <linearGradient id="floorGrad" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stopColor="#2C4266" />
        <stop offset="1" stopColor="#111B2E" />
      </linearGradient>
    </defs>
    <rect x={x0} y={y} width={x1 - x0} height={depth} fill="url(#floorGrad)" />
    <rect x={x0} y={y} width={x1 - x0} height={14} fill={C.teal} />
    <rect x={x0} y={y + 14} width={x1 - x0} height={6} fill={C.yellow} opacity={0.7} />
    {Array.from({ length: Math.ceil((x1 - x0) / 160) }).map((_, i) => (
      <path key={i} d={`M ${x0 + i * 160} ${y + 20} L ${x0 + i * 160 - 120} ${y + depth}`} stroke={C.white} strokeOpacity={0.05} strokeWidth={8} />
    ))}
  </g>
);
