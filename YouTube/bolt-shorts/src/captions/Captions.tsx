import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { C, FONT_CAPTION } from "../theme";
import { activeChunk } from "./subtitles";
import { clamp01, ease } from "../lib/anim";

/**
 * Word-by-word animated captions. White text, thick navy outline, keywords in
 * yellow. Positioned in the lower-middle safe area (top edge y=1340, never
 * reaching the bottom ~380px that YouTube's UI covers).
 */
export const Captions: React.FC<{ y?: number }> = ({ y = 1340 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const chunk = activeChunk(t);
  if (!chunk) return null;
  const kChunk = clamp01((t - chunk.start) / 0.12);
  const chunkScale = 0.85 + 0.15 * ease.outBack(kChunk);
  return (
    <div
      style={{
        position: "absolute",
        left: 90,
        width: 860,
        top: y,
        display: "flex",
        flexWrap: "wrap",
        justifyContent: "center",
        alignContent: "flex-start",
        columnGap: 50,
        rowGap: 0,
        transform: `scale(${chunkScale})`,
        transformOrigin: "50% 0%",
      }}
    >
      {chunk.words.map((w, i) => {
        const visible = t >= w.start - 0.02;
        const k = clamp01((t - w.start) / 0.1);
        const speaking = t >= w.start && t < w.end + 0.05;
        const s = visible ? (0.6 + 0.4 * ease.outBackBig(k)) * (speaking ? 1.05 : 1) : 0.6;
        return (
          <span
            key={i}
            style={{
              fontFamily: FONT_CAPTION,
              fontWeight: 900,
              fontSize: w.keyword ? 86 : 78,
              lineHeight: 1.12,
              color: w.keyword ? C.gold : C.white,
              WebkitTextStroke: `16px ${C.navy}`,
              paintOrder: "stroke fill",
              textShadow: `0 8px 0 ${C.navyDeep}, 0 0 24px rgba(14,22,38,0.6)`,
              opacity: visible ? 1 : 0,
              display: "inline-block",
              transform: `scale(${s}) rotate(${speaking && w.keyword ? -2 : 0}deg)`,
              letterSpacing: 1,
            }}
          >
            {w.text}
          </span>
        );
      })}
    </div>
  );
};
