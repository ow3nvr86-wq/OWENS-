import React from "react";
import { C } from "../theme";
import { B, springAt, clamp01 } from "../lib/anim";
import { Cam } from "../world/Camera";
import { ArenaBackdrop } from "../world/Arena";
import { Track, FoamHammer, FoamPit, MovingPlatform, Bridge, BigButton, StartPad, PrizeDisplay } from "../world/Props";
import { Confetti } from "../world/Effects";

/** Course layout (world units). One continuous set used by scenes 2-5. */
export const COURSE = {
  ground: 1320,
  boltScale: 0.8,
  startPad: [300, 760] as const,
  track1: [760, 2330] as const,
  hammer1: { x: 1650, y: 420, len: 500, amp: 55, period: 1.5, hit: B.hammer1Duck, dir: 1 },
  pit1: [2330, 2950] as const,
  platform1X: 2640,
  track2: [2950, 4450] as const,
  hammer2: { x: 3600, y: 380, len: 420, amp: 60, period: 1.4, hit: B.hammer2NearMiss, dir: -1 },
  pit2: [4450, 4980] as const,
  bridge: [4480, 4880] as const,
  finalTop: 1290,
  final: [4980, 5900] as const,
  buttonX: 5300,
  prizeX: 5640,
};

/** Pedestal top of the finish button; dome top = this - 130 (+26 when pressed). */
export const BUTTON_TOP = COURSE.finalTop - 190;

export const hammerAngle = (t: number, h: typeof COURSE.hammer1) =>
  h.dir * h.amp * Math.sin(((2 * Math.PI) / h.period) * (t - h.hit));

export const platform1Y = (t: number) => 1300 - 150 * Math.cos(((2 * Math.PI) / 1.6) * (t - 10.67));

export const bridgeShift = (t: number) => {
  const base = 40 * Math.sin(t * 2.4);
  // sudden jerk that causes the slip
  const jerk = t > B.slip - 0.08 ? -70 * Math.exp(-4 * (t - (B.slip - 0.08))) * Math.min(1, (t - (B.slip - 0.08)) / 0.08) : 0;
  return base + jerk;
};

export const buttonPress = (t: number) => (t < B.buttonSlam ? 0 : 1 - Math.max(0, Math.sin((t - B.buttonSlam) * 30)) * Math.exp(-(t - B.buttonSlam) * 10) * 0.3);

/** When each course element rises out of the opened floor (staggered with the pan). */
const riseTime = (x: number) => Math.max(B.floorOpen + 0.05, B.panStart + ((x - 540) / 4760) * 1.5 - 0.35);
const rise = (t: number, x: number) => {
  const t0 = riseTime(x);
  if (t < t0) return 1100;
  return (1 - springAt(t, t0, 11, 5.5)) * 1100;
};

export const CourseWorld: React.FC<{ t: number; cam: Cam; bolt: React.ReactNode; fg?: React.ReactNode; excite?: number }> = ({ t, cam, bolt, fg, excite = 0 }) => {
  const G = COURSE.ground;
  const opened = t >= B.floorOpen;
  const winT = B.buttonSlam;
  const won = t >= winT;
  return (
    <g>
      <ArenaBackdrop cam={cam} t={t} span={[-1000, 7000]} excite={excite} logoXs={[540, 2400, 4300, 6200]} />

      {/* deep stage void revealed when the floor opens */}
      <rect x={760} y={G} width={6000} height={1400} fill="#0B1220" />

      {/* prize waiting at the finish */}
      <g transform={`translate(0 ${rise(t, COURSE.prizeX)})`}>
        <PrizeDisplay
          x={COURSE.prizeX}
          y={COURSE.finalTop}
          scale={0.82}
          t={t}
          lit={won ? 1.3 + 0.3 * Math.sin(t * 10) : 0.5}
          flash={won ? Math.max(0, 1 - (t - winT) * 3) : 0}
        />
      </g>

      {/* hammers drop from the ceiling rigs */}
      <FoamHammer x={COURSE.hammer1.x} y={COURSE.hammer1.y} length={COURSE.hammer1.len} angle={hammerAngle(t, COURSE.hammer1)} color={C.pink} drop={rise(t, COURSE.hammer1.x)} />
      <FoamHammer x={COURSE.hammer2.x} y={COURSE.hammer2.y} length={COURSE.hammer2.len} angle={hammerAngle(t, COURSE.hammer2)} color={C.purple} drop={rise(t, COURSE.hammer2.x)} />

      {/* pits */}
      <g transform={`translate(0 ${rise(t, COURSE.pit1[0])})`}>
        <FoamPit x0={COURSE.pit1[0]} x1={COURSE.pit1[1]} y={G + 260} t={t} />
      </g>
      <g transform={`translate(0 ${rise(t, COURSE.pit2[0])})`}>
        <FoamPit x0={COURSE.pit2[0]} x1={COURSE.pit2[1]} y={G + 300} t={t} slime />
      </g>

      {/* moving platform over pit 1 */}
      <g transform={`translate(0 ${rise(t, COURSE.platform1X)})`}>
        <MovingPlatform x={COURSE.platform1X} y={platform1Y(t)} w={190} color={C.orange} />
      </g>

      {/* tracks */}
      <StartPad x0={COURSE.startPad[0]} x1={COURSE.startPad[1]} y={G} />
      <Track x0={COURSE.track1[0]} x1={COURSE.track1[1]} y={G} color={C.teal} rise={rise(t, 1200)} />
      <Track x0={COURSE.track2[0]} x1={COURSE.track2[1]} y={G} color={C.orange} rise={rise(t, 3400)} />

      {/* moving bridge */}
      <g transform={`translate(${bridgeShift(t)} ${rise(t, COURSE.bridge[0])})`}>
        <Bridge x0={COURSE.bridge[0]} x1={COURSE.bridge[1]} y={G} tilt={Math.sin(t * 3.1) * 2} />
      </g>

      {/* final platform + finish button */}
      <g transform={`translate(0 ${rise(t, COURSE.final[0] + 200)})`}>
        <Track x0={COURSE.final[0]} x1={COURSE.final[1]} y={COURSE.finalTop} color={C.purple} thickness={140} />
        <BigButton x={COURSE.buttonX} y={BUTTON_TOP} press={buttonPress(t)} label="FINISH" glow={won ? 1 : 0.4 + 0.3 * Math.sin(t * 8)} />
      </g>

      {/* closed floor hatch: trapdoor panels swing down when the floor opens */}
      {Array.from({ length: 14 }).map((_, i) => {
        const x0 = 760 + i * 380;
        const t0 = Math.max(B.floorOpen, riseTime(x0) - 0.25);
        const k = opened ? clamp01((t - t0) / 0.3) : 0;
        if (k >= 1) return null;
        return (
          <g key={i} transform={`rotate(${k * 95} ${x0} ${G})`}>
            <rect x={x0} y={G} width={380} height={44} fill={C.steelDark} stroke={C.navy} strokeWidth={6} />
            <path d={`M ${x0 + 30} ${G + 22} L ${x0 + 350} ${G + 22}`} stroke={C.yellow} strokeWidth={8} strokeDasharray="30 20" />
          </g>
        );
      })}

      {bolt}

      {/* finish-line confetti cannons */}
      <Confetti t={t} t0={winT + 0.05} x={COURSE.buttonX - 340} y={COURSE.finalTop - 20} count={80} spread={0.6} power={1700} seed="cA" />
      <Confetti t={t} t0={winT + 0.05} x={COURSE.buttonX + 420} y={COURSE.finalTop - 20} count={80} spread={0.6} power={1700} seed="cB" />
      <Confetti t={t} t0={B.celebrateJump2 - 0.2} x={COURSE.buttonX} y={COURSE.finalTop - 600} count={60} spread={1.6} power={900} seed="cC" />

      {/* stage-front apron hides substructure */}
      <rect x={-2000} y={G + 640} width={10000} height={2000} fill="#0A0F1A" />
      {fg}
    </g>
  );
};
