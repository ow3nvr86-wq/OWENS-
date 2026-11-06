import React from "react";
import { C, FONT_DISPLAY } from "../theme";

const SKIN = ["#F1C7A5", "#D9A07A", "#B87A52", "#8D5A3B", "#6B4128", "#F5D6BC"];
const SHIRT = [C.orange, C.teal, C.purple, "#4A90D9", C.pink, C.yellow, "#5DBB73"];
const HAIR = ["#2B1B12", "#4A2E1C", "#8A5A2B", "#1A1A1A", "#C7792E", "#6E6E6E"];

/** Simple original cartoon person. cheer 0..1 raises arms and adds hops. */
export const Person: React.FC<{ x: number; y: number; i: number; s?: number; t: number; cheer?: number; hope?: number; kid?: boolean; face?: -1 | 1 }> = ({
  x, y, i, s = 1, t, cheer = 0, hope = 0, kid = false, face = 1,
}) => {
  const skin = SKIN[i % SKIN.length];
  const shirt = SHIRT[(i * 3) % SHIRT.length];
  const hair = HAIR[(i * 5) % HAIR.length];
  const hop = cheer > 0 ? Math.abs(Math.sin(t * 8 + i * 1.3)) * 26 * cheer : Math.sin(t * 2 + i) * 2;
  const armUp = cheer;
  const wobbleA = Math.sin(t * 10 + i) * 14 * cheer;
  const sc = s * (kid ? 0.72 : 1);
  const smile = 0.3 + 0.7 * Math.max(cheer, hope * 0.5);
  return (
    <g transform={`translate(${x} ${y - hop}) scale(${sc * face} ${sc})`}>
      <ellipse cx={0} cy={hop / sc} rx={50} ry={10} fill={C.navyDeep} opacity={0.25} />
      {/* legs */}
      <rect x={-26} y={-90} width={22} height={90} rx={10} fill={C.navyMid} stroke={C.navy} strokeWidth={5} />
      <rect x={4} y={-90} width={22} height={90} rx={10} fill={C.navyMid} stroke={C.navy} strokeWidth={5} />
      {/* arms */}
      <g transform={`translate(-38 -190) rotate(${20 + armUp * 140 + wobbleA})`}>
        <rect x={-10} y={0} width={20} height={80} rx={10} fill={shirt} stroke={C.navy} strokeWidth={5} />
        <circle cy={84} r={13} fill={skin} stroke={C.navy} strokeWidth={5} />
      </g>
      <g transform={`translate(38 -190) rotate(${-20 - armUp * 140 - wobbleA})`}>
        <rect x={-10} y={0} width={20} height={80} rx={10} fill={shirt} stroke={C.navy} strokeWidth={5} />
        <circle cy={84} r={13} fill={skin} stroke={C.navy} strokeWidth={5} />
      </g>
      {/* body */}
      <rect x={-44} y={-205} width={88} height={125} rx={34} fill={shirt} stroke={C.navy} strokeWidth={6} />
      {/* head */}
      <circle cy={-250} r={44} fill={skin} stroke={C.navy} strokeWidth={6} />
      {i % 3 === 0 ? (
        <path d="M -46 -252 Q -48 -300 0 -300 Q 48 -300 46 -252 Q 30 -278 0 -276 Q -30 -278 -46 -252 Z" fill={hair} stroke={C.navy} strokeWidth={5} />
      ) : i % 3 === 1 ? (
        <g>
          <circle cx={-30} cy={-282} r={22} fill={hair} stroke={C.navy} strokeWidth={5} />
          <circle cx={0} cy={-296} r={24} fill={hair} stroke={C.navy} strokeWidth={5} />
          <circle cx={30} cy={-282} r={22} fill={hair} stroke={C.navy} strokeWidth={5} />
        </g>
      ) : (
        <path d="M -44 -244 Q -50 -306 4 -298 Q 50 -292 44 -244 L 40 -266 Q 0 -262 -40 -266 Z" fill={hair} stroke={C.navy} strokeWidth={5} />
      )}
      <circle cx={-15} cy={-252} r={5.5} fill={C.navy} />
      <circle cx={15} cy={-252} r={5.5} fill={C.navy} />
      <path d={`M -16 -232 Q 0 ${-232 + 14 * smile} 16 -232`} stroke={C.navy} strokeWidth={5} fill={cheer > 0.5 ? C.white : "none"} strokeLinecap="round" />
      <circle cx={-26} cy={-236} r={7} fill={C.pink} opacity={0.35} />
      <circle cx={26} cy={-236} r={7} fill={C.pink} opacity={0.35} />
    </g>
  );
};

/** Cardboard supply box / food crate. */
export const SupplyBox: React.FC<{ x: number; y: number; s?: number; kind?: "food" | "box" | "water" | "apple"; pop?: number }> = ({ x, y, s = 1, kind = "box", pop = 1 }) => {
  if (pop <= 0.001) return null;
  return (
    <g transform={`translate(${x} ${y}) scale(${s * pop})`}>
      {kind === "apple" ? (
        <g>
          <rect x={-70} y={-70} width={140} height={70} rx={8} fill="#B07A45" stroke={C.navy} strokeWidth={6} />
          {[-45, -15, 15, 45].map((ax, k) => (
            <circle key={k} cx={ax} cy={-80} r={20} fill={k % 2 ? C.red : C.orange} stroke={C.navy} strokeWidth={5} />
          ))}
          <rect x={-70} y={-48} width={140} height={10} fill="#8A5A2B" />
        </g>
      ) : kind === "water" ? (
        <g>
          {[-40, 0, 40].map((bx, k) => (
            <g key={k}>
              <rect x={bx - 16} y={-110} width={32} height={110} rx={10} fill="#7FD3F7" stroke={C.navy} strokeWidth={5} />
              <rect x={bx - 8} y={-124} width={16} height={16} rx={4} fill="#4A90D9" stroke={C.navy} strokeWidth={4} />
            </g>
          ))}
        </g>
      ) : (
        <g>
          <rect x={-70} y={-110} width={140} height={110} rx={6} fill="#D49A5A" stroke={C.navy} strokeWidth={6} />
          <rect x={-70} y={-110} width={140} height={22} fill="#B97F43" stroke={C.navy} strokeWidth={5} />
          <rect x={-12} y={-110} width={24} height={110} fill="#E9C38E" opacity={0.7} />
          {kind === "food" && (
            <g>
              <path d="M -40 -110 L -30 -150 L -10 -112" fill={C.yellow} stroke={C.navy} strokeWidth={4} />
              <circle cx={28} cy={-122} r={18} fill={C.red} stroke={C.navy} strokeWidth={4} />
              <rect x={-6} y={-150} width={22} height={40} rx={6} fill="#5DBB73" stroke={C.navy} strokeWidth={4} />
            </g>
          )}
          <text y={-34} textAnchor="middle" fontFamily={FONT_DISPLAY} fontSize={26} fill="#7A4E22">{kind === "food" ? "FOOD" : "SUPPLIES"}</text>
        </g>
      )}
    </g>
  );
};

/** Warm community-center building. glow 0..1 = warm light after donation. */
export const CommunityCenter: React.FC<{ x: number; y: number; t: number; glow?: number }> = ({ x, y, t, glow = 0 }) => (
  <g transform={`translate(${x} ${y})`}>
    {/* building */}
    <rect x={-520} y={-640} width={1040} height={640} rx={20} fill="#E9A86B" stroke={C.navy} strokeWidth={10} />
    <path d="M -580 -630 L 0 -900 L 580 -630 Z" fill={C.orange} stroke={C.navy} strokeWidth={10} strokeLinejoin="round" />
    <rect x={-360} y={-830} width={720} height={130} rx={24} fill={C.white} stroke={C.navy} strokeWidth={8} />
    <text x={0} y={-790} textAnchor="middle" fontFamily={FONT_DISPLAY} fontSize={50} fill={C.teal}>COMMUNITY</text>
    <text x={0} y={-730} textAnchor="middle" fontFamily={FONT_DISPLAY} fontSize={50} fill={C.orange}>CENTER</text>
    {[-380, -170, 170, 380].map((wx, k) => (
      <g key={k}>
        <rect x={wx - 70} y={-560} width={140} height={150} rx={14} fill={glow > 0 ? "#FFE39A" : "#7FA9C7"} stroke={C.navy} strokeWidth={7} />
        <rect x={wx - 70} y={-560} width={140} height={150} rx={14} fill="#FFF2B8" opacity={glow * (0.6 + 0.2 * Math.sin(t * 6 + k))} />
        <path d={`M ${wx} -560 L ${wx} -410 M ${wx - 70} -485 L ${wx + 70} -485`} stroke={C.navy} strokeWidth={6} />
      </g>
    ))}
    {/* door */}
    <rect x={-90} y={-300} width={180} height={300} rx={16} fill={C.teal} stroke={C.navy} strokeWidth={8} />
    <circle cx={50} cy={-150} r={10} fill={C.gold} />
    {/* awning */}
    <path d="M -520 -360 L 520 -360 L 490 -300 L -490 -300 Z" fill={C.white} stroke={C.navy} strokeWidth={6} />
    {Array.from({ length: 13 }).map((_, k) => (
      <path key={k} d={`M ${-520 + k * 80} -360 L ${-520 + k * 80 + 40} -360 L ${-490 + k * 80 + 30} -300 L ${-490 + k * 80 - 10} -300 Z`} fill={C.red} opacity={0.85} />
    ))}
    {/* hearts sign */}
    <path transform="translate(-430 -250) scale(0.9)" d="M 0 30 C -50 -5 -40 -45 -14 -42 C -4 -41 0 -32 0 -26 C 0 -32 4 -41 14 -42 C 40 -45 50 -5 0 30 Z" fill="#FF4F6D" stroke={C.navy} strokeWidth={6} />
  </g>
);

/** Long table for food distribution. */
export const Table: React.FC<{ x: number; y: number; w?: number }> = ({ x, y, w = 520 }) => (
  <g transform={`translate(${x} ${y})`}>
    <rect x={-w / 2} y={-120} width={w} height={26} rx={8} fill="#C98A4B" stroke={C.navy} strokeWidth={6} />
    <rect x={-w / 2 + 20} y={-94} width={18} height={94} fill="#8A5A2B" stroke={C.navy} strokeWidth={5} />
    <rect x={w / 2 - 38} y={-94} width={18} height={94} fill="#8A5A2B" stroke={C.navy} strokeWidth={5} />
    <rect x={-w / 2} y={-120} width={w} height={60} fill={C.white} opacity={0.0} />
  </g>
);
