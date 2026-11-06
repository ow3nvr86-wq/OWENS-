import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { Bolt, defaultPose } from "../characters/Bolt";
import { exprTrack } from "../characters/BoltExpressions";
import { run, duck, jump } from "../characters/BoltAnimations";
import { Stage, Cam } from "../world/Camera";
import { CourseWorld, COURSE } from "./CourseWorld";
import { Dust, Grade, SpeedLines, ZoomLines } from "../world/Effects";
import { HudTimer } from "../world/Overlays";
import { B, FPS, shake, sumShake, wobble, clamp01 } from "../lib/anim";
import { runX, followCam } from "./coursePath";
import { C } from "../theme";

/** Bolt pose for the running section (shared by scenes 3 and 4 up to the slip). */
export const runningPose = (t: number) => {
  let pose = { ...defaultPose(), x: runX(t), y: COURSE.ground, scale: COURSE.boltScale };
  pose.expr = exprTrack(t, [
    [6.6, "focused"],
    [8.7, "startled", 0.08],
    [B.hammer1Duck + 0.25, "happy", 0.12],
    [10.15, "determined", 0.1],
    [10.55, "amazed", 0.1],
    [B.jumpLand + 0.05, "excited", 0.1],
    [12.25, "terrified", 0.05],
    [12.95, "focused", 0.2],
  ]);
  pose = run(pose, t, 1, 3);
  // duck under hammer 1
  const dk = clamp01(1 - Math.abs(t - B.hammer1Duck) / 0.28);
  if (dk > 0) pose = duck(pose, Math.sin((dk * Math.PI) / 2));
  // jump the moving platform
  pose = jump(pose, t, B.jumpTakeoff, B.jumpLand, 330, 1);
  // near miss: antenna clipped and flicked, eyes enormous
  if (t >= B.hammer2NearMiss) {
    const w = wobble(t, B.hammer2NearMiss, 26, 4, 1);
    pose = { ...pose, antenna: pose.antenna - 70 * w, antennaStretch: pose.antennaStretch * (1 - 0.2 * Math.abs(w)), y: pose.y + 10 * Math.abs(w) };
  }
  return pose;
};

/** SCENE 3 — THE FIRST OBSTACLE (0:08–0:14). Hammers, platform jump, near miss. */
export const ObstacleCourse: React.FC = () => {
  const t = 8 + useCurrentFrame() / FPS;
  const f = followCam(t);
  const jumpLift = t > B.jumpTakeoff && t < B.jumpLand ? Math.sin(((t - B.jumpTakeoff) / (B.jumpLand - B.jumpTakeoff)) * Math.PI) : 0;
  const punch = Math.max(0, wobble(t, B.hammer2NearMiss - 0.03, 10, 5, 1));
  const duckPunch = Math.max(0, wobble(t, B.hammer1Duck - 0.05, 10, 6, 0.6));
  const sh = sumShake(shake(t, B.hammer1Duck, 20, 0.35, "h1"), shake(t, B.jumpLand, 26, 0.35, "jl"), shake(t, B.hammer2NearMiss, 44, 0.5, "h2"));
  const cam: Cam = {
    x: f.x - punch * 120,
    y: f.y - jumpLift * 110 - punch * 30,
    zoom: f.zoom + 0.22 * punch + 0.08 * duckPunch,
    shakeX: sh.x,
    shakeY: sh.y,
    rot: sh.r + Math.sin(t * 2) * 0.6,
  };
  const pose = runningPose(t);
  return (
    <AbsoluteFill style={{ background: C.navyDeep }}>
      <Stage cam={cam}>
        <CourseWorld
          t={t}
          cam={cam}
          excite={0.7}
          bolt={
            <>
              <Dust t={t} t0={B.jumpTakeoff} x={2300} y={COURSE.ground} dir={-1} seed="jt" />
              <Dust t={t} t0={B.jumpLand} x={3000} y={COURSE.ground} dir={1} size={1.4} seed="jl" />
              <Dust t={t} t0={B.jumpLand} x={3000} y={COURSE.ground} dir={-1} size={1.4} seed="jl2" />
              <Bolt id="bolt-course" pose={pose} />
            </>
          }
        />
      </Stage>
      <SpeedLines t={t} intensity={0.75} dir={1} />
      <ZoomLines intensity={punch * 0.9} t={t} cy={820} />
      <Grade vignette={0.5} />
      <HudTimer t={t} show={1} />
    </AbsoluteFill>
  );
};
