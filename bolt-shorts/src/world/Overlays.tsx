import React from "react";
import { C, FONT_DISPLAY } from "../theme";
import { ease, clamp01, wobble, timerValue, fmtTimer, B, noise } from "../lib/anim";
import { Starburst, HeartShape } from "./Effects";
import { TimerBoard } from "./Props";

/**
 * Big slam-in title (screen space). Lines are stacked; each line can have its own colour.
 * Slams in from huge scale with overshoot at t0, holds, and exits at t1.
 */
export const TitleSlam: React.FC<{
  t: number;
  t0: number;
  t1: number;
  lines: { text: string; fill?: string; size?: number }[];
  y: number;
  burst?: boolean;
  rotate?: number;
  heart?: boolean;
  exit?: "pop" | "up" | "none";
  burstR?: number;
}> = ({ t, t0, t1, lines, y, burst = false, rotate = -4, heart = false, exit = "pop", burstR = 560 }) => {
  if (t < t0 || t > t1 + 0.25) return null;
  const kIn = clamp01((t - t0) / 0.2);
  const sIn = 2.6 - 1.6 * ease.outBackBig(kIn);
  const kOut = exit === "none" ? 0 : clamp01((t - t1) / 0.2);
  const sOut = exit === "pop" ? 1 + kOut * 0.4 : 1;
  const yOut = exit === "up" ? -kOut * 300 : 0;
  const op = Math.min(kIn * 3, 1) * (1 - kOut);
  const wob = wobble(t, t0 + 0.2, 20, 7, 1);
  const scale = sIn * sOut * (1 + 0.04 * Math.sin((t - t0) * 6)) * (1 + 0.05 * wob);
  let yy = 0;
  return (
    <svg width={1080} height={1920} style={{ position: "absolute", inset: 0 }}>
      <g transform={`translate(540 ${y + yOut}) rotate(${rotate + wob * 3}) scale(${scale})`} opacity={op}>
        {burst && <Starburst x={0} y={-20} r={burstR} t={t} opacity={0.5} />}
        {lines.map((l, i) => {
          const size = l.size ?? 140;
          yy += i === 0 ? 0 : size * 0.98;
          return (
            <text
              key={i}
              y={yy}
              textAnchor="middle"
              fontFamily={FONT_DISPLAY}
              fontSize={size}
              fill={l.fill ?? C.gold}
              stroke={C.navy}
              strokeWidth={size * 0.16}
              strokeLinejoin="round"
              paintOrder="stroke"
              style={{ filter: "drop-shadow(0 10px 0 rgba(14,22,38,0.85))" }}
            >
              {l.text}
            </text>
          );
        })}
        {heart && <HeartShape x={0} y={yy + 150} s={2.1 + 0.15 * Math.sin(t * 9)} />}
      </g>
    </svg>
  );
};

/** HUD countdown timer pinned to the top of the frame during the challenge. */
export const HudTimer: React.FC<{ t: number; show: number; shakeAmt?: number }> = ({ t, show, shakeAmt = 0 }) => {
  if (show <= 0.01) return null;
  const v = timerValue(t);
  const stopped = t >= B.buttonSlam;
  const danger = !stopped && v < 5.5;
  const beat = danger ? 1 + 0.08 * Math.max(0, Math.sin(t * Math.PI * 4)) : 1;
  const goPulse = wobble(t, B.go, 22, 6, 1);
  const sx = noise("hudx", t * 30) * 10 * shakeAmt;
  const sy = noise("hudy", t * 30) * 8 * shakeAmt;
  const flashOn = stopped ? Math.floor(t * 5) % 2 === 0 || t > B.buttonSlam + 1.2 : !danger || Math.floor(t * 8) % 2 === 0;
  return (
    <svg width={1080} height={1920} style={{ position: "absolute", inset: 0 }}>
      <g transform={`translate(${540 + sx} ${300 + sy - (1 - show) * 400}) scale(${0.78 * beat * (1 + 0.12 * goPulse)})`}>
        <TimerBoard x={0} y={0} text={fmtTimer(v)} danger={danger ? 1 : 0} stopped={stopped} flashOn={flashOn} />
        <rect x={-130} y={-170} width={260} height={56} rx={20} fill={stopped ? "#5CF08A" : danger ? C.red : C.yellow} stroke={C.navy} strokeWidth={6} />
        <text y={-128} textAnchor="middle" fontFamily={FONT_DISPLAY} fontSize={40} fill={C.navy}>{stopped ? "STOPPED!" : "TIME LEFT"}</text>
      </g>
    </svg>
  );
};
