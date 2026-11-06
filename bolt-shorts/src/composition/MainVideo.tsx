import React from "react";
import { AbsoluteFill, Sequence } from "remotion";
import timeline from "../timeline.json";
import { ensureFonts, C } from "../theme";
import { Hook } from "../scenes/Hook";
import { ChallengeStart } from "../scenes/ChallengeStart";
import { ObstacleCourse } from "../scenes/ObstacleCourse";
import { NearDisaster } from "../scenes/NearDisaster";
import { Victory } from "../scenes/Victory";
import { Donation } from "../scenes/Donation";
import { Captions } from "../captions/Captions";
import { AudioMix } from "../audio/AudioMix";

const SCENES: Record<string, React.FC> = {
  hook: Hook,
  start: ChallengeStart,
  obstacles: ObstacleCourse,
  disaster: NearDisaster,
  win: Victory,
  donation: Donation,
};

/** BOLT #001 — The $100,000 Challenge. 1080x1920, 30fps, 960 frames. */
export const MainVideo: React.FC<{ showCaptions?: boolean; withAudio?: boolean }> = ({ showCaptions = true, withAudio = true }) => {
  ensureFonts();
  const fps = timeline.fps;
  return (
    <AbsoluteFill style={{ background: C.navyDeep }}>
      {timeline.scenes.map((s) => {
        const Scene = SCENES[s.id];
        return (
          <Sequence key={s.id} from={Math.round(s.start * fps)} durationInFrames={Math.round((s.end - s.start) * fps)} name={s.title}>
            <Scene />
          </Sequence>
        );
      })}
      {showCaptions && <Captions />}
      {withAudio && <AudioMix />}
    </AbsoluteFill>
  );
};
