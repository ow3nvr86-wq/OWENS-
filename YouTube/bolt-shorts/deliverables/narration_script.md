# BOLT #001 — Narration Script & Voice-Over Cues

**Voice:** Original energetic narrator: clear, expressive, conversational, fast but understandable. Not an imitation of any real person.

**Status:** No text-to-speech provider is configured in this project, so **no narration audio was generated**. The video ships with music, SFX and burned-in captions; the voice-over slot is ready (see *Integration* below).

| # | Scene | Start | End | Line | Delivery |
|---|---|---|---|---|---|
| n1 | hook | 0.25s | 2.90s | This robot has 30 seconds to win ONE HUNDRED THOUSAND DOLLARS! | Punchy hook, rising excitement, hit 'ONE HUNDRED THOUSAND DOLLARS' hard. |
| n2 | start | 3.10s | 5.05s | All he has to do is survive the obstacle course! | Quick, playful, slight dare in the voice. Finish before the countdown beeps at 5.15s. |
| n3 | obstacles | 8.30s | 11.40s | He dodged the hammers, jumped the platforms... | Fast, rhythmic, riding the percussion. Trail off on 'platforms...' into the near-miss. |
| n4 | disaster | 14.30s | 18.30s | But with seconds left... HE ALMOST LOST EVERYTHING! | Drop to a tense near-whisper on 'But with seconds left...', then explode on 'HE ALMOST LOST EVERYTHING!'. Silence 18.4-18.9s. |
| n5 | win | 20.75s | 23.40s | AND HE DID IT! ONE HUNDRED THOUSAND DOLLARS! | Full celebration, big smile in the voice, shouted over the fanfare. |
| n6 | donation | 25.30s | 30.40s | But Bolt didn't keep a single dollar. He donated ALL of it to help others. | Warm, sincere, slower. Small pause before 'He donated', land 'ALL of it' with heart. |

## Phrase-level cues (caption sync points)

| Start | End | Phrase |
|---|---|---|
| 0.25 | 0.85 | THIS ROBOT HAS |
| 0.85 | 1.35 | **30 SECONDS** |
| 1.35 | 1.65 | TO WIN |
| 1.65 | 2.90 | **ONE HUNDRED THOUSAND DOLLARS!** |
| 3.10 | 3.85 | ALL HE HAS TO DO |
| 3.85 | 4.30 | IS SURVIVE |
| 4.30 | 5.05 | THE OBSTACLE COURSE! |
| 8.30 | 8.90 | HE DODGED |
| 8.90 | 9.60 | THE HAMMERS, |
| 10.00 | 10.50 | JUMPED |
| 10.50 | 11.40 | THE PLATFORMS... |
| 14.30 | 15.00 | BUT WITH |
| 15.00 | 15.75 | SECONDS LEFT... |
| 16.60 | 17.25 | HE **ALMOST** |
| 17.25 | 18.30 | **LOST EVERYTHING!** |
| 20.75 | 21.60 | AND **HE DID IT!** |
| 21.80 | 23.40 | **ONE HUNDRED THOUSAND DOLLARS!** |
| 25.30 | 26.20 | BUT BOLT DIDN'T KEEP |
| 26.20 | 27.00 | A SINGLE DOLLAR. |
| 28.20 | 29.50 | HE **DONATED ALL OF IT** |
| 29.50 | 30.40 | TO HELP OTHERS. |

Words in **bold** are highlighted yellow on screen.

## Integration

1. Record or generate the six lines, timed to the cues above, as one 32.0 s file starting at 0:00.
2. Save it as `public/audio/narration/narration.wav`.
3. In `src/audio/narration/config.ts` set `NARRATION_FILE = "audio/narration/narration.wav"`.
4. Re-render: `npx remotion render MainVideo out/bolt_001_100k_challenge.mp4`. Music ducks to ~42% under each line automatically.
5. If the real read drifts from these timings, edit `src/captions/narration-cues.json` (captions + SRT follow it) and re-run `python3 scripts/make_srt.py`.
