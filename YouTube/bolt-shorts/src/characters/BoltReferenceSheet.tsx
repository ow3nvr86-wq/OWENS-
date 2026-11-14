import React from "react";
import { AbsoluteFill } from "remotion";
import { Bolt, defaultPose, BoltPose } from "./Bolt";
import { EXPRESSIONS, ExpressionName } from "./BoltExpressions";
import { celebrate, wave, run, surprised, crouch } from "./BoltAnimations";
import { C, ensureFonts, FONT_DISPLAY, FONT_CAPTION } from "../theme";

/** Character model sheet rendered from the production rig (source of truth). */
export const BoltReferenceSheet: React.FC = () => {
  ensureFonts();
  const at = (x: number, y: number, s: number, patch: Partial<BoltPose> = {}): BoltPose => ({ ...defaultPose(), x, y, scale: s, ...patch });
  const exprs: ExpressionName[] = ["neutral", "excited", "amazed", "determined", "terrified", "strain", "joyful", "warmSmile"];
  return (
    <AbsoluteFill style={{ background: "#F3F0E8" }}>
      <svg width={1080} height={1920} viewBox="0 0 1080 1920">
        <text x={540} y={110} textAnchor="middle" fontFamily={FONT_DISPLAY} fontSize={84} fill={C.navy}>BOLT — MODEL SHEET</text>
        <text x={540} y={160} textAnchor="middle" fontFamily={FONT_CAPTION} fontWeight={900} fontSize={26} fill={C.steelDark}>Rendered from src/characters/Bolt.tsx · same rig used in every scene</text>
        <Bolt id="ref-main" pose={at(300, 900, 1.3)} />
        <Bolt id="ref-wave" pose={wave(at(800, 900, 1.05, { expr: EXPRESSIONS.warmSmile }), 1.2, 0)} />
        <text x={300} y={950} textAnchor="middle" fontFamily={FONT_CAPTION} fontWeight={900} fontSize={26} fill={C.navy}>FRONT · NEUTRAL</text>
        <text x={800} y={950} textAnchor="middle" fontFamily={FONT_CAPTION} fontWeight={900} fontSize={26} fill={C.navy}>WAVE</text>
        <Bolt id="ref-run" pose={run(at(190, 1400, 0.72, { expr: EXPRESSIONS.focused }), 0.1, 1)} />
        <Bolt id="ref-crouch" pose={crouch(at(450, 1400, 0.72, { expr: EXPRESSIONS.determined }), 1)} />
        <Bolt id="ref-cel" pose={celebrate(at(700, 1400, 0.72, { expr: EXPRESSIONS.joyful }), 0.4, 0)} />
        <Bolt id="ref-sur" pose={surprised(at(930, 1400, 0.72, { expr: EXPRESSIONS.amazed }), 0.08, 0)} />
        {exprs.map((n, i) => {
          const cx = 90 + i * 130;
          return (
            <g key={n}>
              <Bolt id={`ref-e${i}`} pose={at(cx, 1790, 0.33, { expr: EXPRESSIONS[n], shadow: false })} />
              <text x={cx} y={1840} textAnchor="middle" fontFamily={FONT_CAPTION} fontWeight={900} fontSize={17} fill={C.navy}>{n.toUpperCase()}</text>
            </g>
          );
        })}
        {[["TEAL", C.teal], ["ORANGE", C.orange], ["YELLOW", C.yellow], ["NAVY", C.navy], ["AMBER EYE", C.amber], ["STEEL", C.steel]].map(([n, c], i) => (
          <g key={n} transform={`translate(${70 + i * 160} 1480)`}>
            <rect width={130} height={60} rx={14} fill={c} stroke={C.navy} strokeWidth={4} />
            <text x={65} y={88} textAnchor="middle" fontFamily={FONT_CAPTION} fontWeight={900} fontSize={18} fill={C.navy}>{n}</text>
          </g>
        ))}
      </svg>
    </AbsoluteFill>
  );
};
