import React from "react";
import { AbsoluteFill } from "remotion";
import { Bolt, defaultPose } from "../characters/Bolt";
import { EXPRESSIONS } from "../characters/BoltExpressions";
import { surprised } from "../characters/BoltAnimations";
import { Stage } from "../world/Camera";
import { ArenaBackdrop, StageFloor } from "../world/Arena";
import { PrizeDisplay, Bill } from "../world/Props";
import { Grade, Starburst, HeartShape } from "../world/Effects";
import { C, ensureFonts, FONT_DISPLAY } from "../theme";

/** 1080x1920 Shorts thumbnail / cover frame. */
export const Thumbnail: React.FC = () => {
  ensureFonts();
  const cam = { x: 540, y: 1040, zoom: 1.3 };
  const pose = surprised({ ...defaultPose(), x: 540, y: 1380, scale: 1.05, expr: { ...EXPRESSIONS.amazed, lookY: -0.2 } }, 0.07, 0);
  return (
    <AbsoluteFill style={{ background: C.navyDeep }}>
      <Stage cam={cam}>
        <ArenaBackdrop cam={cam} t={1.2} span={[-600, 1700]} excite={1} />
        <Starburst x={540} y={760} r={1300} t={0.4} opacity={0.35} />
        <StageFloor x0={-1000} x1={2100} y={1200} />
        <PrizeDisplay x={540} y={1200} t={0.3} lit={1.6} ledOpacity={0} />
        {[[180, 600, 20], [880, 520, -30], [260, 980, 50], [850, 1040, -15], [120, 1250, 70], [960, 1300, 10]].map(([x, y, r], i) => (
          <Bill key={i} x={x} y={y} rot={r} s={1.3} />
        ))}
        <Bolt id="thumb" pose={pose} />
      </Stage>
      <Grade vignette={0.5} />
      <svg width={1080} height={1920} style={{ position: "absolute", inset: 0 }}>
        <g transform="translate(540 300) rotate(-4)">
          <text textAnchor="middle" fontFamily={FONT_DISPLAY} fontSize={210} fill={C.gold} stroke={C.navy} strokeWidth={30} paintOrder="stroke" style={{ filter: "drop-shadow(0 12px 0 rgba(14,22,38,.9))" }}>$100,000</text>
          <text y={150} textAnchor="middle" fontFamily={FONT_DISPLAY} fontSize={128} fill={C.white} stroke={C.navy} strokeWidth={22} paintOrder="stroke">CHALLENGE!</text>
        </g>
        <g transform="translate(540 1600) rotate(3)">
          <rect x={-420} y={-95} width={840} height={150} rx={40} fill={C.orange} stroke={C.navy} strokeWidth={10} />
          <text y={18} textAnchor="middle" fontFamily={FONT_DISPLAY} fontSize={84} fill={C.white} stroke={C.navy} strokeWidth={12} paintOrder="stroke">WAIT FOR IT...</text>
          <HeartShape x={360} y={-100} s={1.6} />
        </g>
      </svg>
    </AbsoluteFill>
  );
};
