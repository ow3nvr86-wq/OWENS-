import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { Bolt, BoltPose } from "../characters/Bolt";
import { exprTrack, EXPRESSIONS } from "../characters/BoltExpressions";
import { slipFall, hang, blendPose, jitter } from "../characters/BoltAnimations";
import { Stage, Cam } from "../world/Camera";
import { CourseWorld, COURSE } from "./CourseWorld";
import { Grade } from "../world/Effects";
import { HudTimer } from "../world/Overlays";
import { B, FPS, keys, ease, shake, sumShake, progress, mix, clamp01, lerpT } from "../lib/anim";
import { followCam } from "./coursePath";
import { runningPose } from "./ObstacleCourse";
import { C } from "../theme";


const S = COURSE.boltScale;
/** Bolt-local position of the right hand when the arm points straight up. */
const HAND_LOCAL = { x: 72, y: -306 };
const LIP = { x: COURSE.final[0] + 4, y: COURSE.finalTop + 6 };

/** Place Bolt so his right hand stays on the lip while he swings by `rot` degrees. */
const rootFromHand = (rot: number) => {
  const r = (rot * Math.PI) / 180;
  const hx = HAND_LOCAL.x * S;
  const hy = HAND_LOCAL.y * S;
  return { x: LIP.x - (hx * Math.cos(r) - hy * Math.sin(r)), y: LIP.y - (hx * Math.sin(r) + hy * Math.cos(r)) };
};

/** Animation clock with a held freeze for the dramatic pause. */
const animClock = (t: number) => {
  if (t < B.musicPauseStart) return t;
  if (t < B.musicPauseEnd) return B.musicPauseStart + (t - B.musicPauseStart) * 0.08;
  return t - (B.musicPauseEnd - B.musicPauseStart) * 0.92;
};

const antennaSpin = (t: number) => {
  if (t < B.slip) return 0;
  const end = B.closeUpEnd;
  if (t < end) return (t - B.slip) * 1100;
  const s0 = (end - B.slip) * 1100;
  const target = Math.ceil(s0 / 360) * 360;
  return mix(s0, target, ease.out(progress(t, end, end + 0.6)));
};

export const disasterPose = (tReal: number): BoltPose => {
  const t = animClock(tReal);
  const expr = exprTrack(tReal, [
    [14.0, "focused"],
    [B.slip - 0.08, "startled", 0.06],
    [B.slip + 0.12, "terrified", 0.1],
    [17.6, "strain", 0.15],
    [B.musicPauseStart, { ...EXPRESSIONS.terrified, lookY: 0.9, lookX: -0.3 }, 0.12],
    [B.musicPauseEnd, "strain", 0.1],
    [19.75, "determined", 0.15],
  ]);
  if (tReal < B.slip) return { ...runningPose(tReal), expr };

  // ---- slip & slow-motion fall ----
  if (tReal < B.grab) {
    const base = runningPose(B.slip);
    const k = progress(tReal, B.slip, B.grab);
    const target = rootFromHand(0);
    const x = mix(4690, target.x, ease.inOut(k));
    const y = keys(tReal, [[B.slip, COURSE.ground], [15.15, COURSE.ground - 110, ease.out], [B.grab, target.y, ease.in]]);
    let p: BoltPose = { ...base, x, y, expr, shadow: false };
    p = slipFall(p, t, clamp01((tReal - B.slip) / 0.45), 1);
    p.rot = keys(tReal, [[B.slip, 0], [15.0, -78, ease.out], [15.55, -40], [B.grab, 0, ease.out]]);
    // reach for the ledge
    const reach = progress(tReal, 15.45, B.grab);
    p.armR = { a: mix(p.armR.a, 178, ease.out(reach)), b: mix(p.armR.b, 0, reach) };
    p.handR = reach > 0.8 ? "grab" : "open";
    p.antennaSpin = antennaSpin(tReal);
    return p;
  }

  // ---- hanging by one hand ----
  const effort = keys(tReal, [[B.grab, 0], [17.5, 0.15], [18.2, 0.7], [B.musicPauseStart, 0.75], [B.pullUp, 0.8], [19.6, 1]]);
  const swingAmt = keys(tReal, [[B.grab, 1.6], [16.6, 1], [18.2, 0.5], [B.pullUp, 0.2]]);
  const jolt = tReal < B.grab + 0.4 ? Math.sin((tReal - B.grab) * 30) * Math.exp(-(tReal - B.grab) * 8) * 8 : 0;
  const rot = Math.sin(t * 4.2) * 6 * swingAmt + jolt;
  const root = rootFromHand(rot);
  let p: BoltPose = { ...runningPose(B.slip), x: root.x, y: root.y, rot: 0, lean: 0, bodyY: 0, sx: 1, sy: 1, expr, shadow: false };
  p = hang(p, t, 0, effort);
  p.rot = rot;
  p.armR = { a: 178 - effort * 6, b: 0 };
  p.antennaSpin = antennaSpin(tReal);
  p = jitter(p, t, 0.6 * (1 - effort));
  if (tReal > 18.15) {
    // second hand catches the ledge
    const g = ease.out(progress(tReal, 18.15, 18.35));
    p.armL = { a: mix(p.armL.a, 150, g), b: mix(p.armL.b, 30, g) };
    p.handL = g > 0.7 ? "grab" : "open";
  }

  // ---- pull up onto the platform ----
  if (tReal >= B.pullUp) {
    const k = progress(tReal, B.pullUp, 20.05);
    const stand: BoltPose = {
      ...p,
      x: COURSE.final[0] + 40,
      y: COURSE.finalTop,
      rot: 0,
      armR: { a: 40, b: -30 },
      armL: { a: -40, b: 30 },
      handR: "fist",
      handL: "fist",
      legL: { a: -20, b: 40 },
      legR: { a: 20, b: -40 },
      sy: 0.86,
      sx: 1.08,
      shadow: true,
    };
    const up: BoltPose = { ...p, y: p.y - 150 * S * ease.out(clamp01(k * 2)), armR: { a: 160, b: 80 }, armL: { a: 170, b: -60 } };
    p = k < 0.5 ? blendPose(p, up, ease.out(k * 2)) : blendPose(up, stand, ease.inOut((k - 0.5) * 2));
    p.rot = k < 0.5 ? p.rot : mix(18, 0, (k - 0.5) * 2);
  }
  return p;
};

/** SCENE 4 — THE NEAR DISASTER (0:14–0:20). Slip, one-hand grab, close-up, pull up. */
export const NearDisaster: React.FC = () => {
  const t = 14 + useCurrentFrame() / FPS;
  const pose = disasterPose(t);

  // head position (for the close-up)
  const r = (pose.rot * Math.PI) / 180;
  const head = { x: pose.x + Math.sin(r) * 345 * S, y: pose.y - Math.cos(r) * 345 * S };

  let cam: Cam;
  const f = followCam(t);
  const beat = t > 17.5 && t < B.musicPauseStart ? Math.max(0, Math.sin(t * Math.PI * 2.4)) ** 6 * 0.03 : 0;
  if (t < B.slip) cam = { x: f.x, y: f.y, zoom: mix(1.05, 1.12, progress(t, 14, B.slip)) };
  else if (t < B.grab) {
    const k = ease.inOut(progress(t, B.slip, B.grab));
    cam = { x: mix(f.x, pose.x + 40, k), y: mix(f.y, pose.y - 190, k), zoom: mix(1.12, 1.4, k) };
  } else if (t < B.closeUpStart) cam = { x: pose.x + 40, y: rootFromHand(0).y - 190, zoom: 1.4 };
  else if (t < B.closeUpEnd) {
    const k = ease.inOut(progress(t, B.closeUpStart, B.closeUpStart + 0.25));
    cam = { x: mix(pose.x + 40, head.x, k), y: mix(rootFromHand(0).y - 190, head.y + 40, k), zoom: mix(1.4, 2.7, k) + (t - B.closeUpStart) * 0.08 };
  } else {
    const k = ease.inOut(progress(t, B.closeUpEnd, B.closeUpEnd + 0.3));
    const pk = progress(t, B.pullUp, 20);
    const medium = { x: COURSE.final[0] + 20, y: mix(1260, 1120, pk), zoom: 1.25 + beat };
    cam = { x: mix(head.x, medium.x, k), y: mix(head.y + 40, medium.y, k), zoom: mix(2.7 + 0.1, medium.zoom, k) };
  }
  const sh = sumShake(shake(t, B.slip, 22, 0.3, "sl"), shake(t, B.grab, 40, 0.5, "gr"), shake(t, B.closeUpStart, 14, 1.3, "cu"), shake(t, 18.15, 18, 0.3, "g2"));
  const dangerShake = t > 16 && t < B.musicPauseStart ? 0.6 : 0;
  cam = { ...cam, shakeX: sh.x, shakeY: sh.y, rot: sh.r };

  const dim = t > B.slip ? lerpT(t, B.slip, B.slip + 0.2, 0, 0.32) * (t > 19.6 ? lerpT(t, 19.6, 20, 1, 0.3) : 1) : 0;
  const redPulse = t > 15.9 ? (0.5 + 0.5 * Math.sin(t * Math.PI * 4)) * (t < 19.8 ? 1 : 0.3) : 0;
  const paused = t >= B.musicPauseStart && t < B.musicPauseEnd;

  return (
    <AbsoluteFill style={{ background: C.navyDeep }}>
      <Stage cam={cam}>
        <CourseWorld t={animClock(t)} cam={cam} excite={0.3} bolt={<Bolt id="bolt-course" pose={pose} />} />
      </Stage>
      <AbsoluteFill style={{ background: `rgba(6,10,20,${dim})` }} />
      <Grade vignette={t > B.closeUpStart && t < B.closeUpEnd ? 0.85 : 0.6} red={redPulse * 0.8} />
      {paused && <AbsoluteFill style={{ background: "rgba(10,14,30,0.25)" }} />}
      <HudTimer t={t} show={1} shakeAmt={dangerShake} />
    </AbsoluteFill>
  );
};
