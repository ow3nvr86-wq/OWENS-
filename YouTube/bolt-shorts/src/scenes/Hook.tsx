import React from "react";
import { AbsoluteFill, random, useCurrentFrame } from "remotion";
import { Bolt, defaultPose } from "../characters/Bolt";
import { exprTrack, blink } from "../characters/BoltExpressions";
import { idle, surprised, crouch } from "../characters/BoltAnimations";
import { Stage, Cam } from "../world/Camera";
import { ArenaBackdrop, StageFloor } from "../world/Arena";
import { PrizeDisplay, TimerBoard, Bill } from "../world/Props";
import { Flash, Grade, ZoomLines } from "../world/Effects";
import { TitleSlam } from "../world/Overlays";
import { B, FPS, keys, ease, shake, sumShake, springAt, lerpT, wobble } from "../lib/anim";
import { C } from "../theme";

/** SCENE 1 — THE HOOK (0:00–0:03). Prize slam, push-in to Bolt, giant countdown appears. */
export const Hook: React.FC = () => {
  const t = useCurrentFrame() / FPS;

  // camera: open tight on the prize, rapid push-in to Bolt
  const zoom = keys(t, [[0, 1.12], [0.12, 1.12], [0.85, 1.34, ease.outExpo], [3, 1.42, ease.linear]]);
  const cy = keys(t, [[0, 700], [0.12, 700], [0.85, 1070, ease.outExpo], [3, 1080, ease.linear]]);
  const sh = sumShake(shake(t, 0, 34, 0.4, "h0"), shake(t, B.titleSlam, 22, 0.35, "h1"), shake(t, B.countdownAppear + 0.12, 16, 0.3, "h2"));
  const cam: Cam = { x: 540, y: cy, zoom, shakeX: sh.x, shakeY: sh.y, rot: sh.r };

  // Bolt
  let pose = { ...defaultPose(), x: 540, y: 1340, scale: 1 };
  pose.expr = exprTrack(t, [
    [0, "curious"],
    [0.3, "excited", 0.2],
    [B.eyesWiden, "amazed", 0.08],
    [2.15, "excited", 0.2],
    [2.5, "determined", 0.15],
  ]);
  pose.expr = { ...pose.expr, lookY: t < 2.1 ? -0.75 : pose.expr.lookY, eyeOpen: pose.expr.eyeOpen * blink(t, [1.65, 2.75]) };
  pose.headTilt = keys(t, [[0, -4], [1.0, -8], [2.1, 0], [2.6, 3]]);
  pose.turn = keys(t, [[0, 0], [2.1, 0], [2.4, 0.15]]);
  pose = idle(pose, t);
  pose = surprised(pose, t, B.eyesWiden);
  if (t > 2.3) {
    // fist pump of determination
    const k = springAt(t, 2.3, 16, 7);
    pose = { ...pose, armR: { a: 14 + k * 140, b: -14 + k * 60 }, handR: "fist" };
  }
  pose = crouch(pose, lerpT(t, 2.6, 2.95, 0, 0.6), 1);

  // money shower falling in front of the prize
  const bills = [];
  for (let i = 0; i < 26; i++) {
    const st = random(`hb${i}`) * 2.4;
    if (t < st) continue;
    const dt = t - st;
    const bx = 120 + random(`hbx${i}`) * 840 + Math.sin(dt * 3 + i) * 50;
    const by = 260 + dt * (380 + random(`hbs${i}`) * 220);
    bills.push(<Bill key={i} x={bx} y={by} rot={dt * 200 + i * 40} flip={Math.cos(dt * 6 + i)} s={0.9} />);
  }

  const prizeFlash = Math.max(0, 1 - t / 0.25) + Math.max(0, 1 - Math.abs(t - B.cashRegister) / 0.12) * 0.8;
  const boardDrop = keys(t, [[B.countdownAppear, -700], [B.countdownAppear + 0.22, 0, ease.outBack]]);
  const boardWob = wobble(t, B.countdownAppear + 0.22, 18, 6, 1);

  return (
    <AbsoluteFill style={{ background: C.navyDeep }}>
      <Stage cam={cam}>
        <ArenaBackdrop cam={cam} t={t} span={[-600, 1700]} excite={0.6} logoXs={[540]} />
        <StageFloor x0={-1000} x1={2100} y={1180} />
        <PrizeDisplay x={540} y={1180} scale={1} t={t} lit={1.1 + 0.3 * Math.sin(t * 9)} flash={prizeFlash} ledOpacity={lerpT(t, B.titleSlam, B.titleSlam + 0.15, 1, 0)} />
        {t >= B.countdownAppear && (
          <g transform={`translate(0 ${boardDrop}) rotate(${boardWob * 4} 540 520)`}>
            <path d="M 400 200 L 450 570 M 680 200 L 630 570" stroke={C.steel} strokeWidth={8} />
            <TimerBoard x={540} y={650} scale={0.8} text="30.0" flashOn={Math.floor(t * 8) % 2 === 0 || t > 2.4} />
          </g>
        )}
        {bills}
        <Bolt id="bolt-hook" pose={pose} />
      </Stage>
      <ZoomLines intensity={Math.max(0, 1 - Math.abs(t - 0.45) / 0.45)} t={t} cy={900} />
      <Grade vignette={0.5} />
      <TitleSlam t={t} t0={B.titleSlam} t1={B.countdownAppear - 0.12} y={235} burst exit="up" lines={[{ text: "$100,000", fill: C.gold, size: 156 }, { text: "CHALLENGE!", fill: C.white, size: 106 }]} />
      <Flash amount={Math.max(0, 1 - t / 0.12)} />
    </AbsoluteFill>
  );
};
