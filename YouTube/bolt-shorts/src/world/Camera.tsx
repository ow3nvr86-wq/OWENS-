import React from "react";
import { W, H } from "../lib/anim";

export type Cam = { x: number; y: number; zoom: number; rot?: number; shakeX?: number; shakeY?: number };

/** Full-frame SVG with a 2D camera. Children are drawn in world coordinates. */
export const Stage: React.FC<{ cam: Cam; children: React.ReactNode; background?: string }> = ({ cam, children, background }) => (
  <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{ position: "absolute", inset: 0, background }}>
    <g
      transform={`translate(${W / 2 + (cam.shakeX ?? 0)} ${H / 2 + (cam.shakeY ?? 0)}) rotate(${cam.rot ?? 0}) scale(${cam.zoom}) translate(${-cam.x} ${-cam.y})`}
    >
      {children}
    </g>
  </svg>
);

/** A layer that moves at `factor` of camera speed (0 = fixed to screen, 1 = world). */
export const Parallax: React.FC<{ cam: Cam; factor: number; children: React.ReactNode }> = ({ cam, factor, children }) => (
  <g transform={`translate(${cam.x * (1 - factor)} ${cam.y * (1 - factor)})`}>{children}</g>
);
