import React from "react";
import { AbsoluteFill, random, useCurrentFrame } from "remotion";
import { Bolt, BoltPose, defaultPose } from "../characters/Bolt";
import { exprTrack, blink, EXPRESSIONS } from "../characters/BoltExpressions";
import { idle, wave, pressRight } from "../characters/BoltAnimations";
import { Stage, Cam, Parallax } from "../world/Camera";
import { ArenaBackdrop, StageFloor } from "../world/Arena";
import { PrizeDisplay, BigButton, Bill, Coin } from "../world/Props";
import { CommunityCenter, Person, SupplyBox, Table } from "../world/Community";
import { Grade, Hearts, Whip, Flash, Confetti } from "../world/Effects";
import { TitleSlam } from "../world/Overlays";
import { B, FPS, keys, ease, progress, mix, lerpT, shake, sumShake, clamp01, springAt } from "../lib/anim";
import { C } from "../theme";

const FLOOR = 1300;
const PRIZE_X = 330;
const BOLT_X = 790;
const BTN_X = 1000;
const BTN_S = 0.7;
const CENTER_X = 3000;
const S = 0.85;

/** Camera shots for the donation ending (whip pans between stage and community center). */
const SHOTS: { t: number; cam: Cam }[] = [
  { t: 25.0, cam: { x: 640, y: 1000, zoom: 1.02 } },
  { t: 25.75, cam: { x: 680, y: 1005, zoom: 1.1 } },
  { t: 26.02, cam: { x: CENTER_X, y: 960, zoom: 0.95 } },
  { t: 26.9, cam: { x: CENTER_X - 40, y: 965, zoom: 1.02 } },
  { t: 27.12, cam: { x: 830, y: 1010, zoom: 1.3 } },
  { t: 28.0, cam: { x: 840, y: 1010, zoom: 1.36 } },
  { t: 28.2, cam: { x: 640, y: 960, zoom: 0.85 } },
  { t: 28.85, cam: { x: CENTER_X - 120, y: 930, zoom: 0.8 } },
  { t: 29.05, cam: { x: CENTER_X, y: 960, zoom: 0.92 } },
  { t: 29.95, cam: { x: CENTER_X, y: 940, zoom: 1.0 } },
  { t: 30.15, cam: { x: BOLT_X + 10, y: 1020, zoom: 1.5 } },
  { t: 32.0, cam: { x: BOLT_X + 10, y: 1010, zoom: 1.62 } },
];

const camAt = (t: number): Cam => {
  for (let i = 1; i < SHOTS.length; i++) {
    const a = SHOTS[i - 1];
    const b = SHOTS[i];
    if (t <= b.t) {
      const k = progress(t, a.t, b.t);
      const e = b.t - a.t < 0.3 ? ease.inOut(k) : i === SHOTS.length - 1 ? k : ease.inOut(k);
      return { x: mix(a.cam.x, b.cam.x, e), y: mix(a.cam.y, b.cam.y, e), zoom: mix(a.cam.zoom, b.cam.zoom, e) };
    }
  }
  return SHOTS[SHOTS.length - 1].cam;
};

const whipAmount = (t: number) => {
  const whips: [number, number][] = [[25.75, 26.02], [26.9, 27.12], [29.95, 30.15]];
  for (const [a, b] of whips) if (t > a && t < b) return Math.sin(progress(t, a, b) * Math.PI);
  return 0;
};

export const donationPose = (t: number): BoltPose => {
  let p: BoltPose = { ...defaultPose(), x: BOLT_X, y: FLOOR, scale: S };
  p.expr = exprTrack(t, [
    [25, { ...EXPRESSIONS.excited, lookX: -0.95, lookY: -0.35 }],
    [B.lookCommunity, { ...EXPRESSIONS.thoughtful, lookX: 1, lookY: 0 }, 0.15],
    [B.lookBack, { ...EXPRESSIONS.thoughtful, lookX: -0.9, lookY: -0.3, brow: -6 }, 0.12],
    [B.smile, { ...EXPRESSIONS.soft, lookX: -0.4 }, 0.3],
    [27.7, { ...EXPRESSIONS.happy, lookX: 0.6 }, 0.15],
    [28.1, "joyful", 0.15],
    [B.wave - 0.1, "warmSmile", 0.2],
  ]);
  p.expr = { ...p.expr, eyeOpen: p.expr.eyeOpen * blink(t, [26.6, 27.45, 31.25]) };
  p.turn = keys(t, [[25, -0.5], [B.lookCommunity, -0.5], [B.lookCommunity + 0.15, 0.65], [B.lookBack, 0.65], [B.lookBack + 0.15, -0.45], [27.6, -0.2], [27.75, 0.45], [28.3, 0.3], [B.wave, 0]]);
  p.headTilt = keys(t, [[25, -6], [B.lookCommunity + 0.2, 4], [B.lookBack, 4], [B.smile, -2], [B.smile + 0.35, 8], [27.6, 0], [B.wave, 6]]);
  p = idle(p, t);
  // press the DONATE button
  const press = keys(t, [[27.6, 0], [B.donatePress, 1, ease.inOut], [28.25, 1], [28.5, 0]]);
  if (press > 0) p = pressRight(p, press);
  // little happy bounce after donating
  if (t > 28.2 && t < B.wave) p = { ...p, bodyY: p.bodyY - Math.abs(Math.sin(t * 9)) * 10, antenna: p.antenna + Math.sin(t * 9) * 14 };
  p = wave(p, t, B.wave, t > 31.5 ? lerpT(t, 31.5, 31.85, 1, 0.25) : 1);
  return p;
};

/** SCENE 6 — THE UNEXPECTED ENDING (0:25–0:32). The money goes to the community center. */
export const Donation: React.FC = () => {
  const t = 25 + useCurrentFrame() / FPS;
  const sh = sumShake(shake(t, B.donatePress, 18, 0.3, "dp"), shake(t, B.donatedText, 14, 0.3, "dt"));
  const base = camAt(t);
  const cam: Cam = { ...base, shakeX: sh.x, shakeY: sh.y, rot: sh.r };
  const pose = donationPose(t);

  const transfer = progress(t, B.transferStart, B.transferEnd);
  const fill = 1 - ease.inOut(transfer);
  const amount = 100000 * fill;
  const arrived = progress(t, 28.75, 29.6);
  const warm = lerpT(t, 28.8, 29.8, 0, 1);
  const btnPress = keys(t, [[27.8, 0], [B.donatePress, 1, ease.in], [28.3, 1], [28.5, 0.2]]);

  // money stream: bills and coins arc from the prize to the community center
  const stream = [];
  for (let i = 0; i < 70; i++) {
    const st = B.transferStart + (i / 70) * (B.transferEnd - B.transferStart - 0.3);
    const dur = 0.95;
    if (t < st || t > st + dur + 0.05) continue;
    const k = progress(t, st, st + dur);
    const p0 = { x: PRIZE_X + (random(`p0x${i}`) - 0.5) * 300, y: 900 + random(`p0y${i}`) * 200 };
    const p2 = { x: CENTER_X - 300 + random(`p2x${i}`) * 600, y: 1080 + random(`p2y${i}`) * 120 };
    const c1 = { x: (p0.x + p2.x) / 2, y: 420 - random(`c1${i}`) * 260 };
    const u = ease.inOut(k);
    const x = (1 - u) ** 2 * p0.x + 2 * (1 - u) * u * c1.x + u * u * p2.x;
    const y = (1 - u) ** 2 * p0.y + 2 * (1 - u) * u * c1.y + u * u * p2.y;
    stream.push(
      i % 3 === 0 ? (
        <Coin key={i} x={x} y={y} spin={t * 14 + i} r={38} />
      ) : (
        <Bill key={i} x={x} y={y} rot={t * 300 + i * 50} flip={Math.cos(t * 10 + i)} s={1.9} />
      ),
    );
  }

  // community center crowd and supplies
  const people = [
    { x: CENTER_X - 400, i: 0 },
    { x: CENTER_X - 260, i: 1, kid: true },
    { x: CENTER_X - 150, i: 2 },
    { x: CENTER_X + 170, i: 3 },
    { x: CENTER_X + 290, i: 4, kid: true },
    { x: CENTER_X + 410, i: 5 },
    { x: CENTER_X - 520, i: 6, kid: true },
    { x: CENTER_X + 540, i: 7 },
  ];
  const boxes: { x: number; kind: "food" | "box" | "water" | "apple"; d: number; y?: number }[] = [
    { x: CENTER_X - 170, kind: "apple", d: 0.0, y: FLOOR - 94 },
    { x: CENTER_X, kind: "food", d: 0.1, y: FLOOR - 94 },
    { x: CENTER_X + 170, kind: "water", d: 0.2, y: FLOOR - 94 },
    { x: CENTER_X - 640, kind: "box", d: 0.3 },
    { x: CENTER_X + 640, kind: "food", d: 0.35 },
    { x: CENTER_X - 760, kind: "water", d: 0.45 },
    { x: CENTER_X + 770, kind: "box", d: 0.5 },
  ];
  const cheer = lerpT(t, 28.9, 29.2, 0, 1);

  return (
    <AbsoluteFill style={{ background: C.navyDeep }}>
      <Stage cam={cam}>
        {/* arena side (stage) */}
        <ArenaBackdrop cam={cam} t={t} span={[-1200, 1700]} excite={0.4} warm={warm * 0.5} logoXs={t < 30 ? [520] : []} />
        {/* outdoor side: warm evening sky behind the community center */}
        <Parallax cam={cam} factor={0.3}>
          <defs>
            <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0" stopColor="#FFB26B" />
              <stop offset="0.6" stopColor="#FFD9A0" />
              <stop offset="1" stopColor="#FFE9C4" />
            </linearGradient>
          </defs>
          <rect x={1450} y={-2000} width={6000} height={5000} fill="url(#sky)" />
          <circle cx={2520} cy={420} r={150} fill="#FFF3C8" opacity={0.9} />
          {[0, 1, 2].map((k) => (
            <g key={k} transform={`translate(${1900 + k * 520 + Math.sin(t * 0.5 + k) * 20} ${250 + k * 90})`} opacity={0.9}>
              <ellipse rx={120} ry={40} fill={C.white} />
              <ellipse cx={-60} cy={-20} rx={60} ry={40} fill={C.white} />
              <ellipse cx={50} cy={-28} rx={70} ry={48} fill={C.white} />
            </g>
          ))}
        </Parallax>
        {/* arena exit wall + doorway between the two areas */}
        <rect x={1560} y={-1500} width={90} height={2800} fill={C.navyMid} stroke={C.navy} strokeWidth={8} />
        <rect x={1575} y={-1500} width={18} height={2800} fill={C.teal} opacity={0.7} />
        {/* ground */}
        <StageFloor x0={-1200} x1={1600} y={FLOOR} />
        <rect x={1600} y={FLOOR} width={3000} height={900} fill="#7BB86A" />
        <rect x={1600} y={FLOOR} width={3000} height={24} fill="#5E9A50" />
        <rect x={1600} y={FLOOR + 70} width={3000} height={120} fill="#C9C1B4" />
        {/* trees */}
        {[1950, 4050].map((tx, k) => (
          <g key={k} transform={`translate(${tx} ${FLOOR})`}>
            <rect x={-22} y={-260} width={44} height={260} fill="#8A5A2B" stroke={C.navy} strokeWidth={6} />
            <circle cy={-330} r={130} fill="#5DBB73" stroke={C.navy} strokeWidth={8} />
            <circle cx={-70} cy={-270} r={80} fill="#4FA865" stroke={C.navy} strokeWidth={6} />
          </g>
        ))}

        <CommunityCenter x={CENTER_X} y={FLOOR} t={t} glow={warm} />
        <Table x={CENTER_X} y={FLOOR} w={600} />
        {boxes.map((b, k) => {
          const pop = t < 28.8 + b.d ? 0 : springAt(t, 28.8 + b.d, 18, 7);
          return <SupplyBox key={k} x={b.x} y={b.y ?? FLOOR} kind={b.kind} pop={Math.max(0, pop)} />;
        })}
        {people.map((pp, k) => (
          <Person key={k} x={pp.x} y={FLOOR + 10} i={pp.i} kid={pp.kid} t={t} cheer={cheer} hope={lerpT(t, 26.2, 26.8, 0, 1)} face={pp.x < CENTER_X ? 1 : -1} s={0.95} />
        ))}
        <Hearts t={t} t0={29.0} x={CENTER_X} y={900} count={14} spread={1000} seed="cc" />
        <Confetti t={t} t0={29.3} x={CENTER_X} y={700} count={70} spread={1.7} power={1100} seed="dc" />

        {/* stage: prize + Bolt + DONATE button */}
        <PrizeDisplay x={PRIZE_X} y={FLOOR} scale={0.8} t={t} lit={0.9 + 0.3 * Math.sin(t * 6)} fill={fill} amount={amount} label={transfer > 0.98 ? "DONATED!" : "GRAND PRIZE"} />
        <BigButton x={BTN_X} y={FLOOR - 190 * BTN_S} scale={BTN_S} press={btnPress} color="#3FCF6E" dark="#23914A" label="DONATE" glow={0.5 + 0.5 * Math.sin(t * 7)} />
        <Bolt id="bolt-donate" pose={pose} />
        <Hearts t={t} t0={B.donatePress} x={BTN_X - 40} y={1050} count={6} spread={200} seed="bh" />
        <Hearts t={t} t0={B.realWinner} x={BOLT_X} y={760} count={10} spread={500} seed="fh" />

        {stream}
      </Stage>
      <Whip amount={whipAmount(t)} t={t} dir={t < 26.5 ? 1 : -1} />
      <Grade vignette={0.4} warm={0.35 + warm * 0.65} />
      <TitleSlam t={t} t0={B.donatedText} t1={29.98} y={420} burst exit="pop" lines={[{ text: "$100,000", size: 170, fill: C.gold }, { text: "DONATED!", size: 150, fill: "#5CF08A" }]} />
      <TitleSlam t={t} t0={B.realWinner} t1={32.5} y={300} exit="none" rotate={-3} lines={[{ text: "THE REAL", size: 130, fill: C.white }, { text: "WINNER", size: 165, fill: C.gold }]} heart />
      <Flash amount={Math.max(0, 1 - (t - 25) / 0.12) * 0.9} />
      <Flash amount={Math.max(0, 1 - Math.abs(t - B.donatePress) / 0.1) * 0.35} color={C.gold} />
    </AbsoluteFill>
  );
};
