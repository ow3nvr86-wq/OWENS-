import React from "react";
import { AbsoluteFill } from "remotion";
import { Bolt, defaultPose } from "../characters/Bolt";
import { EXPRESSIONS } from "../characters/BoltExpressions";
import { wave } from "../characters/BoltAnimations";
import { C, ensureFonts } from "../theme";

/**
 * Channel profile picture (800x800). Built for YouTube's circular crop:
 * everything important sits inside the central circle, no text (it would be
 * unreadable at 40-98px). Uses the production Bolt rig.
 */
export const ChannelAvatar: React.FC = () => {
  ensureFonts();
  const S = 800;
  const cx = S / 2;
  const rays = 20;
  const pose = wave(
    {
      ...defaultPose(),
      x: cx - 10,
      y: 950,
      scale: 1.62,
      headTilt: 6,
      turn: 0.12,
      expr: { ...EXPRESSIONS.happy, sparkle: 1, pupil: 1.2, eyeScale: 1.08, lookX: 0.05, lookY: 0.05, mouthOpen: 0.85, glow: 1.3 },
      shadow: false,
      chestGlow: 1,
    },
    0.32,
    0,
  );
  const bolt = (x: number, y: number, s: number, r: number, fill: string) => (
    <path
      transform={`translate(${x} ${y}) rotate(${r}) scale(${s})`}
      d="M 6 -46 L -22 6 L -2 6 L -10 46 L 22 -10 L 2 -10 Z"
      fill={fill}
      stroke={C.navy}
      strokeWidth={6}
      strokeLinejoin="round"
    />
  );
  return (
    <AbsoluteFill>
      <svg width={S} height={S} viewBox={`0 0 ${S} ${S}`}>
        <defs>
          <radialGradient id="av-bg" cx="0.5" cy="0.45" r="0.65">
            <stop offset="0" stopColor="#FFE08A" />
            <stop offset="0.45" stopColor={C.yellow} />
            <stop offset="1" stopColor={C.orange} />
          </radialGradient>
          <radialGradient id="av-glow" cx="0.5" cy="0.5" r="0.5">
            <stop offset="0" stopColor={C.white} stopOpacity="0.75" />
            <stop offset="1" stopColor={C.white} stopOpacity="0" />
          </radialGradient>
        </defs>
        <rect width={S} height={S} fill="url(#av-bg)" />
        {/* sunburst */}
        <g transform={`translate(${cx} ${cx - 30})`} opacity={0.35}>
          {Array.from({ length: rays }).map((_, i) => {
            const a0 = (i / rays) * Math.PI * 2;
            const a1 = ((i + 0.5) / rays) * Math.PI * 2;
            return <path key={i} d={`M 0 0 L ${Math.cos(a0) * 700} ${Math.sin(a0) * 700} L ${Math.cos(a1) * 700} ${Math.sin(a1) * 700} Z`} fill={C.white} />;
          })}
        </g>
        <circle cx={cx} cy={cx - 40} r={330} fill="url(#av-glow)" />
        {/* lightning accents (kept inside the circular crop) */}
        {bolt(158, 250, 1.25, -18, C.white)}
        {bolt(650, 205, 0.95, 16, C.white)}
        {bolt(140, 470, 0.7, -8, C.gold)}
        <Bolt id="avatar" pose={pose} />
      </svg>
    </AbsoluteFill>
  );
};
