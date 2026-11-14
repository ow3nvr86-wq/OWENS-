import React from "react";
import { Audio, Sequence, staticFile, useVideoConfig } from "remotion";
import { SFX } from "./sfxTimeline";
import { NARRATION_FILE } from "./narration/config";
import { NARRATION_LINES } from "../captions/subtitles";

/** Music gain at time t. Ducks under narration lines when a voice-over is present. */
export const musicGain = (t: number, narration: boolean) => {
  const base = 0.62;
  if (!narration) return base;
  let duck = 1;
  for (const l of NARRATION_LINES) {
    const a = l.start - 0.12;
    const b = l.end + 0.15;
    if (t >= a - 0.1 && t <= b + 0.2) {
      const k = t < a ? (a - t) / 0.1 : t > b ? (t - b) / 0.2 : 0;
      duck = Math.min(duck, 0.42 + 0.58 * Math.min(1, k));
    }
  }
  return base * duck;
};

export const AudioMix: React.FC = () => {
  const { fps } = useVideoConfig();
  const narration = NARRATION_FILE !== null;
  return (
    <>
      <Audio src={staticFile("audio/music/bolt_score.wav")} volume={(f) => musicGain(f / fps, narration)} />
      {SFX.map((c, i) => (
        <Sequence key={i} from={Math.round(c.time * fps)} layout="none" name={`sfx:${c.file}`}>
          <Audio src={staticFile(`audio/sound-effects/${c.file}.wav`)} volume={c.vol * (narration ? 0.8 : 1)} />
        </Sequence>
      ))}
      {NARRATION_FILE && <Audio src={staticFile(NARRATION_FILE)} volume={1} />}
    </>
  );
};
