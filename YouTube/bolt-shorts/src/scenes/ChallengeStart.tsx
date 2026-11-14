import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { Bolt, defaultPose } from "../characters/Bolt";
import { exprTrack, blink } from "../characters/BoltExpressions";
import { idle, crouch, windUp, run, lookAround, surprised } from "../characters/BoltAnimations";
import { Stage, Cam } from "../world/Camera";
import { CourseWorld, COURSE } from "./CourseWorld";
import { Dust, Grade, SpeedLines, Whip, Flash } from "../world/Effects";
import { TitleSlam, HudTimer } from "../world/Overlays";
import { B, FPS, keys, ease, shake, sumShake, lerpT, mix, progress } from "../lib/anim";
import { runX, followCam } from "./coursePath";
import { C } from "../theme";

/** SCENE 2 — THE CHALLENGE BEGINS (0:03–0:08). Floor opens, pan across course, 3-2-1-GO, launch. */
export const ChallengeStart: React.FC = () => {
  const t = 3 + useCurrentFrame() / FPS;

  // ---- camera ----
  let cam: Cam;
  const f = followCam(t);
  if (t < B.panStart) {
    cam = { x: 560, y: 1060, zoom: 1.15 };
  } else if (t < B.panEnd) {
    const k = ease.inOut(progress(t, B.panStart, B.panEnd));
    cam = { x: mix(560, 5500, k), y: mix(1060, 960, Math.sin(k * Math.PI) * 0.6 + k * 0.4), zoom: mix(1.15, 0.62, Math.min(1, k * 3)) };
  } else if (t < B.panEnd + 0.15) {
    const k = ease.inOut(progress(t, B.panEnd, B.panEnd + 0.15));
    cam = { x: mix(5500, 580, k), y: mix(960, 1075, k), zoom: mix(0.62, 1.22, k) };
  } else if (t < B.launch) {
    cam = { x: 580, y: 1075, zoom: lerpT(t, B.panEnd + 0.15, B.launch, 1.22, 1.32, ease.linear) };
  } else {
    const k = ease.inOut(progress(t, B.launch, B.launch + 0.6));
    cam = { x: mix(580, f.x, k), y: mix(1075, f.y, k), zoom: mix(1.32, f.zoom, k) };
  }
  const sh = sumShake(shake(t, B.floorOpen, 24, 0.5, "fo"), shake(t, B.go, 26, 0.35, "go"), shake(t, B.launch, 30, 0.35, "la"));
  cam = { ...cam, shakeX: sh.x, shakeY: sh.y, rot: sh.r };

  // ---- Bolt ----
  let pose = { ...defaultPose(), x: 540, y: COURSE.ground, scale: COURSE.boltScale };
  pose.expr = exprTrack(t, [
    [3, "excited"],
    [B.floorOpen + 0.05, "startled", 0.08],
    [3.9, "curious", 0.2],
    [B.panEnd + 0.1, "determined", 0.1],
    [B.go, "focused", 0.1],
  ]);
  pose.expr = { ...pose.expr, eyeOpen: pose.expr.eyeOpen * blink(t, [4.95]) };
  pose = idle(pose, t);
  pose = surprised(pose, t, B.floorOpen + 0.05);
  pose = lookAround(pose, t, 3.5, 4.7);
  if (t >= B.panEnd && t < B.launch) {
    pose = crouch(pose, lerpT(t, B.panEnd + 0.1, B.beep3, 0, 1), 1);
    // lean deeper on each beep
    const beepLean = [B.beep3, B.beep2, B.beep1].reduce((a, bt) => a + (t > bt ? Math.exp(-(t - bt) * 8) * 6 : 0), 0);
    pose = { ...pose, lean: pose.lean + beepLean };
  }
  if (t >= B.go && t < B.launch) {
    pose = windUp(pose, t, lerpT(t, B.go, B.go + 0.12, 0, 1), 1);
  }
  if (t >= B.launch) {
    pose = { ...pose, x: runX(t) };
    pose = run(pose, t, 1, 3);
  }

  const speed = t > B.launch ? lerpT(t, B.launch, B.launch + 0.3, 0, 1) : 0;
  const whip = t > B.panEnd - 0.02 && t < B.panEnd + 0.2 ? Math.sin(progress(t, B.panEnd - 0.02, B.panEnd + 0.2) * Math.PI) : 0;

  return (
    <AbsoluteFill style={{ background: C.navyDeep }}>
      <Stage cam={cam}>
        <CourseWorld
          t={t}
          cam={cam}
          excite={0.5}
          bolt={
            <>
              <Dust t={t} t0={B.go + 0.05} x={540} y={COURSE.ground} dir={-1} seed="w1" />
              <Dust t={t} t0={B.go + 0.3} x={540} y={COURSE.ground} dir={-1} seed="w2" />
              <Dust t={t} t0={B.launch} x={560} y={COURSE.ground} dir={-1} size={1.6} seed="w3" />
              <Bolt id="bolt-course" pose={pose} />
            </>
          }
        />
      </Stage>
      <SpeedLines t={t} intensity={speed * 0.8} dir={1} />
      <Whip amount={whip} t={t} dir={-1} />
      <Grade vignette={0.5} />
      <HudTimer t={t} show={lerpT(t, 3.0, 3.3, 0, 1, ease.outBack)} />
      <TitleSlam t={t} t0={B.beep3} t1={B.beep2 - 0.05} y={720} lines={[{ text: "3", size: 300, fill: C.white }]} rotate={-6} />
      <TitleSlam t={t} t0={B.beep2} t1={B.beep1 - 0.05} y={720} lines={[{ text: "2", size: 300, fill: C.yellow }]} rotate={5} />
      <TitleSlam t={t} t0={B.beep1} t1={B.go - 0.05} y={720} lines={[{ text: "1", size: 300, fill: C.orange }]} rotate={-4} />
      <TitleSlam t={t} t0={B.go} t1={B.go + 0.75} y={630} burst burstR={300} lines={[{ text: "GO!", size: 290, fill: "#5CF08A" }]} rotate={-6} />
      <Flash amount={Math.max(0, 1 - (t - 3) / 0.1) * 0.9} />
    </AbsoluteFill>
  );
};
