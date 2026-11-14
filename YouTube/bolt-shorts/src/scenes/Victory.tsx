import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { Bolt, BoltPose } from "../characters/Bolt";
import { exprTrack, blink } from "../characters/BoltExpressions";
import { jump, celebrate, idle } from "../characters/BoltAnimations";
import { Stage, Cam } from "../world/Camera";
import { CourseWorld, COURSE, BUTTON_TOP, buttonPress } from "./CourseWorld";
import { disasterPose } from "./NearDisaster";
import { ConfettiRain, Flash, Grade, ZoomLines } from "../world/Effects";
import { TitleSlam, HudTimer } from "../world/Overlays";
import { B, FPS, keys, ease, shake, sumShake, progress, mix, wobble, lerpT } from "../lib/anim";
import { C } from "../theme";

const DOME_TOP = (t: number) => BUTTON_TOP - 130 + 26 * buttonPress(t);

export const victoryPose = (t: number): BoltPose => {
  const start = disasterPose(20.05);
  const sx0 = start.x;
  let p: BoltPose = { ...start, sy: 1, sx: 1, shadow: true };
  p.expr = exprTrack(t, [
    [20, "determined"],
    [B.buttonSlam, "joyful", 0.06],
    [21.9, "excited", 0.15],
    [22.9, "joyful", 0.1],
    [24.0, "happy", 0.2],
  ]);
  p.expr = { ...p.expr, eyeOpen: p.expr.eyeOpen * blink(t, [24.4]) };
  if (t < B.onPlatform + 0.02) {
    // finish standing up from the pull-up
    const k = progress(t, 20, B.onPlatform + 0.02);
    return { ...start, sy: mix(0.86, 1, k), sx: mix(1.08, 1, k), expr: p.expr };
  }
  const t0 = B.onPlatform + 0.04;
  const t1 = B.buttonSlam;
  const k = progress(t, t0, t1);
  p.x = mix(sx0, COURSE.buttonX, ease.inOut(k));
  p.y = mix(COURSE.finalTop, DOME_TOP(t), ease.in(k));
  p.legL = { a: -3, b: 0 };
  p.legR = { a: 3, b: 0 };
  p.armL = { a: -14, b: 14 };
  p.armR = { a: 14, b: -14 };
  p.lean = 0;
  p = idle(p, t);
  p = jump(p, t, t0, t1, 170, 1);
  if (t >= t1) {
    p.y = DOME_TOP(t);
    p.shadow = false;
    // fists slam down on contact
    const slam = Math.exp(-(t - t1) * 9);
    p.armL = { a: mix(-150, -50, 1 - slam), b: -20 };
    p.armR = { a: mix(150, 50, 1 - slam), b: 20 };
    p.handL = "fist";
    p.handR = "fist";
    p = celebrate(p, t, 20.62);
    p = jump(p, t, B.celebrateJump1, B.celebrateJump1 + 0.5, 190, 1);
    p = jump(p, t, B.celebrateJump2, B.celebrateJump2 + 0.62, 280, 1);
    if (t > B.celebrateJump2 && t < B.celebrateJump2 + 0.62) p.rot = p.rot + 360 * ease.inOut(progress(t, B.celebrateJump2 + 0.05, B.celebrateJump2 + 0.57));
  }
  return p;
};

/** SCENE 5 — THE WIN (0:20–0:25). Finish button slam, timer stops, YOU WON, confetti. */
export const Victory: React.FC = () => {
  const t = 20 + useCurrentFrame() / FPS;
  const pose = victoryPose(t);
  const punch = Math.max(0, wobble(t, B.buttonSlam, 9, 4.5, 1));
  const base: Cam =
    t < B.buttonSlam
      ? { x: mix(COURSE.final[0] + 20, 5200, ease.inOut(progress(t, 20, B.buttonSlam))), y: mix(1120, 1000, progress(t, 20, B.buttonSlam)), zoom: 1.25 }
      : {
          x: keys(t, [[B.buttonSlam, 5300], [22.0, 5300], [24.4, 5460]]),
          y: keys(t, [[B.buttonSlam, 930], [22.0, 900], [24.4, 820]]),
          zoom: keys(t, [[B.buttonSlam, 1.28], [22.0, 1.22], [24.4, 0.84], [25, 0.8, ease.linear]]),
        };
  const sh = sumShake(shake(t, B.buttonSlam, 48, 0.55, "bs"), shake(t, B.celebrateJump1 + 0.5, 14, 0.25, "c1"), shake(t, B.celebrateJump2 + 0.62, 20, 0.3, "c2"));
  const cam: Cam = { ...base, zoom: base.zoom + 0.2 * punch, shakeX: sh.x, shakeY: sh.y, rot: sh.r };
  const hudShow = t < B.youWon - 0.1 ? 1 : lerpT(t, B.youWon - 0.1, B.youWon + 0.15, 1, 0);
  return (
    <AbsoluteFill style={{ background: C.navyDeep }}>
      <Stage cam={cam}>
        <CourseWorld t={t} cam={cam} excite={t > B.buttonSlam ? 1 : 0.4} bolt={<Bolt id="bolt-course" pose={pose} />} />
      </Stage>
      <ZoomLines intensity={punch} t={t} cy={900} color={C.gold} />
      <ConfettiRain t={t} t0={B.buttonSlam + 0.1} count={80} />
      <Grade vignette={0.45} warm={t > B.buttonSlam ? 0.5 : 0} />
      <HudTimer t={t} show={hudShow} />
      <TitleSlam
        t={t}
        t0={B.youWon}
        t1={24.0}
        y={420}
        burst
        burstR={360}
        exit="up"
        lines={[{ text: "YOU WON!", size: 190, fill: C.gold }]}
      />
      <Flash amount={Math.max(0, 1 - Math.abs(t - B.buttonSlam - 0.03) / 0.1) * 0.85} />
      <Flash amount={Math.max(0, 1 - Math.abs(t - B.youWon) / 0.08) * 0.5} color={C.gold} />
    </AbsoluteFill>
  );
};
