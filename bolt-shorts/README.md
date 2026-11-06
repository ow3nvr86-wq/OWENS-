# BOLT — Animated YouTube Shorts

Remotion + SVG production for **BOLT**, the recurring robot character.
Episode 001: **The $100,000 Challenge** (32 s, 1080×1920, 30 fps, 960 frames).

## Commands

```bash
npm install
python3 -m pip install numpy scipy pillow   # audio synthesis + QC tools
python3 scripts/build_audio.py              # synthesise score + SFX (original, deterministic)
python3 scripts/make_srt.py                 # SRT + narration script from the cue sheet
npx remotion studio                         # preview / scrub
npx remotion render MainVideo out/bolt_001_100k_challenge.mp4
npx remotion still Thumbnail out/bolt_001_thumbnail.png
npx remotion still BoltReference public/characters/bolt-reference.png
node scripts/stills.mjs <outDir> 1.0 9.0 20.5   # QC frames at given seconds
```

`remotion.config.ts` points Remotion at the pre-installed Chromium headless shell; change
`setBrowserExecutable` (or delete it to let Remotion download one) on another machine.

## Architecture

```
src/
  timeline.json                single source of truth: scene ranges, story beats, challenge clock
  theme.ts                     palette + font loading
  lib/anim.ts                  keyframes, springs, wobble, camera shake, timer mapping
  characters/
    Bolt.tsx                   THE character rig — every scene renders this component
    BoltExpressions.ts         15 reusable facial states + blending + blink
    BoltAnimations.ts          idle, walk, run, jump, duck, slipFall, hang, lookAround,
                               surprised, celebrate, wave, windUp, crouch, pressRight, jitter
    BoltReferenceSheet.tsx     model sheet rendered from the rig
  world/                       Camera/Parallax, Arena (MEGA DASH! show identity), Props
                               (prize vault, timer, hammers, pits, bridge, buttons), Effects
                               (confetti, speed/zoom lines, dust, flash, hearts, whip),
                               Community (center, people, supplies), Overlays (titles, HUD timer)
  scenes/
    Hook.tsx  ChallengeStart.tsx  ObstacleCourse.tsx  NearDisaster.tsx  Victory.tsx  Donation.tsx
    CourseWorld.tsx  coursePath.ts   one continuous obstacle-course set shared by scenes 2–5
  captions/  narration-cues.json  subtitles.ts  Captions.tsx
  audio/     sfxTimeline.ts  AudioMix.tsx  narration/config.ts
  composition/  MainVideo.tsx  Thumbnail.tsx
scripts/  build_audio.py  make_srt.py  stills.mjs  contact_sheet.py
public/   characters/bolt-reference.png  fonts/  audio/{music,sound-effects,narration}/
```

### Scene timing

| # | Scene | Time | Frames | Key beats |
|---|---|---|---|---|
| 1 | The Hook | 0:00–0:03 | 0–89 | impact 0.00 · title slam 0.40 · cash ring 0.45 · eyes widen + antenna spring 0.95 · countdown board drops 1.90 |
| 2 | The Challenge Begins | 0:03–0:08 | 90–239 | floor opens 3.05 · pan across course 3.35–4.85 · beeps 5.15/5.45/5.75 · GO + clock starts 6.05 · launch 6.60 |
| 3 | The First Obstacle | 0:08–0:14 | 240–419 | ducks hammer 9.00 · jump 10.35→11.00 over moving platform · hammer clips antenna 12.40 |
| 4 | The Near Disaster | 0:14–0:20 | 420–599 | onto bridge 14.15 · slip 14.55 (slow-mo) · one-hand grab 15.90 · close-up 16.2–17.5 · dead-air pause 18.4–18.9 · pull-up 19.0 |
| 5 | The Win | 0:20–0:25 | 600–749 | button slam + clock stops at 00.3 · 20.45 · YOU WON! 20.90 · celebration jumps 21.35 / 23.10 |
| 6 | The Unexpected Ending | 0:25–0:32 | 750–959 | looks at money 25.0 · at community 25.8 · back 26.95 · smiles 27.3 · DONATE 27.9 · transfer 28.0–29.3 · $100,000 DONATED! 29.35 · wave 30.15 · THE REAL WINNER 30.7 |

The on-screen challenge clock is cartoon time: 30.0 → 5.0 over the run, slows during the
slip, then ticks in real time to 00.3 (`timer.keys` in `timeline.json`).

### Asset inventory

All visual assets are vector code; all audio is synthesised by `scripts/build_audio.py`.

| Asset | Source | License |
|---|---|---|
| Bolt character | `src/characters/Bolt.tsx` (original) | project-owned |
| Arena, props, people, effects | `src/world/*.tsx` (original) | project-owned |
| Show identity "MEGA DASH!" | `src/world/Arena.tsx` (original) | project-owned |
| Score `public/audio/music/bolt_score.wav` | synthesised, 120 BPM, 6 sections | project-owned |
| 38 SFX `public/audio/sound-effects/*.wav` | synthesised | project-owned |
| Luckiest Guy (titles) | Fontsource 5.1.0 | SIL OFL 1.1 (`public/fonts/LICENSE-luckiest-guy.txt`) |
| Montserrat 900 (captions) | Fontsource 5.1.0 | SIL OFL 1.1 (`public/fonts/LICENSE-montserrat.txt`) |
| Remotion 4.0.536 | npm | Remotion license (free for individuals/small teams; companies may need a license) |

### Narration

No TTS provider is configured, so no voice-over is generated. Script, timings and the
integration steps are in `deliverables/narration_script.md`; the slot is
`src/audio/narration/config.ts`.
