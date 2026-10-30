# Audio & SFX timing sheet

All music and sound effects are synthesised by `scripts/audio.py` (numpy/scipy). The voiceover is Piper TTS (`scripts/voiceover.py`, voice `en_US-ljspeech-high`). Times are seconds from the start of the video (30 fps → frame = t × 30 + 1).

## Voiceover

| Start | End | Line | Section | Text |
|---|---|---|---|---|
| 0.15 | 4.39 | L01 | HOOK | In 1919, a wave of molasses killed twenty-one people. |
| 4.62 | 6.23 | L02 | SETUP | Boston. January fifteenth. |
| 6.33 | 11.28 | L03 | SETUP | This tank, five stories tall, held two point three million gallons of molasses. |
| 11.41 | 12.87 | L04 | SETUP | And it leaked from day one. |
| 13.10 | 17.28 | L05 | STORY | The man in charge had no engineering experience, and skipped a proper water test. |
| 17.41 | 20.92 | L06 | STORY | When the leaks got worse, he had the tank painted brown to hide them. |
| 21.12 | 25.64 | L07 | STORY | Then, after a bitter cold snap, the temperature shot past forty degrees. |
| 25.93 | 29.82 | L08 | STORY | Around twelve forty, rivets burst out like machine-gun fire. |
| 29.92 | 31.03 | L09 | STORY | The tank split open. |
| 31.63 | 36.37 | L10 | STORY | A wave up to twenty-five feet high raced through the streets at thirty-five miles an hour, |
| 36.44 | 40.36 | L11 | STORY | knocking buildings off their foundations and slamming into the elevated railway. |
| 40.81 | 42.62 | L12 | PAYOFF | But speed wasn't the deadliest part. |
| 42.88 | 48.53 | L13 | PAYOFF | As the air froze that night, the molasses thickened. Scientists estimate at least four times. |
| 48.73 | 51.40 | L14 | PAYOFF | About half the victims died simply because they were stuck. |
| 52.00 | 56.08 | L15 | ENDING | For decades, locals said the North End smelled sweet on hot days. |
| 56.28 | 57.38 | L16 | ENDING | Could you have outrun it? |

## Shots (cuts)

| Shot | Start | End | Frames |
|---|---|---|---|
| hook | 0.00 | 4.42 | 1–133 |
| aerial | 4.42 | 6.23 | 134–187 |
| scale | 6.23 | 11.31 | 188–339 |
| leaks | 11.31 | 13.00 | 340–390 |
| cutaway | 13.00 | 17.36 | 391–521 |
| paint | 17.36 | 21.02 | 522–631 |
| thermo | 21.02 | 25.79 | 632–774 |
| rivets | 25.79 | 29.87 | 775–896 |
| burst | 29.87 | 31.53 | 897–946 |
| race | 31.53 | 36.39 | 947–1092 |
| house | 36.39 | 38.39 | 1093–1152 |
| el | 38.39 | 40.66 | 1153–1220 |
| rise | 40.66 | 42.78 | 1221–1283 |
| freeze | 42.78 | 48.63 | 1284–1459 |
| stuck | 48.63 | 51.80 | 1460–1554 |
| decades | 51.80 | 56.13 | 1555–1684 |
| end | 56.13 | 59.28 | 1685–1778 |

## Music and SFX cues

| Time | Track | Cue |
|---|---|---|
| 0.00 | MUSIC | Cold open: sub impact + low D drone |
| 0.00 | SFX | Rushing flood swelling toward camera; whoosh into the cut |
| 4.42 | MUSIC | Main theme in: D-minor ostinato (100 BPM) + pad, low intensity |
| 4.42 | SFX | Harbour wind + gulls |
| 6.83 | SFX | Low metal groan of the full tank |
| 11.31 | SFX | Molasses drips (synced to the drip animation) |
| 13.00 | SFX | Thin trickle of water (the six-inch test) |
| 17.36 | SFX | Brush strokes x4 |
| 21.02 | MUSIC | Clock ticks begin, accelerating toward the collapse |
| 26.48 | SFX | 24 rivet pings, machine-gun cadence (synced to pops) |
| 29.75 | MUSIC | Hard stop: 0.12 s of silence before the impact (dramatic pause) |
| 29.87 | MUSIC | BOOM: massive impact + low D-minor brass-like hit |
| 29.87 | SFX | Steel tearing + flood release |
| 31.53 | MUSIC | Drums in: taiko-style groove + driving ostinato |
| 36.39 | SFX | Wood splintering (house shoved off foundation) |
| 38.39 | SFX | Steel girders groaning and bending (elevated railway) |
| 40.66 | MUSIC | Drop-out: single low D + eerie high tone |
| 42.78 | MUSIC | Cold pad (Dm add9) + sparse bells; heartbeat returns in the stuck shot |
| 42.78 | SFX | Night wind + ice crackle building as the molasses freezes |
| 51.80 | MUSIC | Warm turn: F major -> Bb major pad (decades later) |
| 51.80 | SFX | Summer evening: insects, a distant gull |
| 56.13 | MUSIC | Final impact on the question, ring-out to end |

## Mix

- Voice: high-pass 80 Hz, presence lift 2–5 kHz, soft compression, level 0.95.
- Music: ducked up to −55 % under the voice (envelope follower), level 0.42.
- SFX: ducked up to −27 % under the voice, level 0.42.
- Master: soft-clip limiter, normalised to −1 dBFS, 0.6 s fade-out.

Stems: `audio/vo/voiceover.wav`, `audio/music/score.wav`, `audio/sfx/sfx.wav`; final mix `audio/mix.wav` (48 kHz stereo).
