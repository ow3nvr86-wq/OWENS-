# BOLT #001 — "The $100,000 Challenge" · Production Report

## Deliverables (`YouTube/bolt-shorts/deliverables/`)

| File | What it is |
|---|---|
| `bolt_001_100k_challenge.mp4` | Final Short: H.264 High / yuv420p, 1080×1920, 30 fps, **960 frames, 32.000 s**, AAC 48 kHz stereo |
| `bolt_001_100k_challenge.srt` | 21 phrase-level subtitle cues (same timings as the burned-in captions) |
| `bolt_001_100k_challenge_audio_mix.wav` | Final audio mix (score + SFX), 32.0 s |
| `bolt_001_thumbnail.png` | 1080×1920 cover / thumbnail |
| `bolt_reference_sheet.png` | Bolt model sheet rendered from the production rig |
| `narration_script.md` | Narration script, delivery notes, timestamped cues, voice-over integration steps |
| **No narration audio** | No TTS provider is configured in this project, so none was generated (see below) |

Source code, scene timing and asset inventory: `YouTube/bolt-shorts/README.md`.

## Important notes for review

1. **No approved Bolt reference image existed in the project.** I searched the repo, its full git history (both branches) and the filesystem. Bolt was built from the written spec instead: small robot, large rounded-square teal head, two glowing amber eyes, small digital mouth, one short crooked antenna, compact body, short articulated arms, short mechanical legs, bright orange feet, orange glowing chest light. The rig is one component, `src/characters/Bolt.tsx`. `public/characters/bolt-reference.png` was rendered *from* that rig, so it documents the design; it does not come from an approved source. If an approved image exists elsewhere, add it and the rig can be matched to it in one file. Every scene updates automatically.
2. **The narration is not voiced.** As instructed, I did not substitute a stand-in voice. The captions carry the story on their own, and the music is mixed at full level. When a voice-over is added, one config line turns it on and the music ducks under each line automatically.
3. **The captions follow the narration *cue sheet*, not recorded audio**, because none exists. Cue timings are set so that no line overlaps a key SFX hit, such as the countdown beeps or the button slam. If a real read drifts, edit `src/captions/narration-cues.json`; the captions and SRT both follow it.

## Quality-control results

| Check | Result |
|---|---|
| Bolt reference used / consistent | One rig renders every shot, so design drift is impossible by construction. Per-scene stills reviewed: same proportions, colours, antenna and face throughout. Only pose and expression change |
| 1080×1920 vertical | ✅ ffprobe |
| 30 fps | ✅ `r_frame_rate=30/1` |
| Exactly 32 s | ✅ video 32.000 s / 960 decoded frames; audio 32.000 s (the raw Remotion AAC ran 32.021 s; trimmed in mastering) |
| Smooth transitions | Scenes 2→5 are one continuous set with a tracking camera; the other cuts use flash or whip-pan transitions |
| Caption sync | Word-by-word reveal timed to the cue sheet; keywords highlighted in yellow |
| Narration volume | N/A (no voice). The music-ducking path is implemented for when one is added |
| Music / SFX balance | −13.7 LUFS integrated, peak −1.2 dBFS (raw mix hit 0 dBFS; limited in mastering). Music is fully silent 18.4–18.9 s for the dramatic pause |
| Platform-UI safe area | Captions sit at y 1340–1520, above the ~380 px bottom overlay. Titles and the HUD timer are at y 160–620, inside the side margins. Bolt's face is never under a caption |
| No blank frames / glitches / missing assets | ✅ `blackdetect`: none; `freezedetect` (≥0.5 s): none; all 38 SFX files present for their cues |
| Donation ending readable | Bolt looks at the money, then at the community center, then back; smiles; presses DONATE. The prize counter drains $100,000 → $0 as bills fly to the community center. Supplies appear, people cheer, "$100,000 DONATED!", wave, "THE REAL WINNER ❤" |
| File opens and plays | ✅ fully decoded by ffmpeg end to end |

## Creative summary

- **Show identity:** an original challenge show called **"MEGA DASH!"** with a lightning-dash logo, bulb-lit signage, crowd stands and sweeping spotlights. It borrows no real creator's branding, logo, voice or scenes.
- **Hook (0–3 s):** opens on the prize vault with an impact. Rapid push-in to Bolt, a "$100,000 CHALLENGE!" slam, money rain, his eyes widen and the antenna springs, then the 30.0 board drops in.
- **Course:** the floor trapdoors swing open and the course rises out in sync with a fast pan. 3-2-1-GO, a spinning-feet wind-up, and launch. He ducks a foam hammer, leaps a bobbing platform, and a second hammer clips his antenna.
- **Near disaster:** the moving bridge jerks and he slips in slow motion with the antenna spinning wildly. He catches the ledge with one hand. Then a terrified close-up, red danger pulse, heartbeat and dead-air pause, and a pull-up as the clock ticks 4… 3… 2… 1.
- **Win:** he leaps onto the finish button and the clock stops at **00.3**. "YOU WON!", confetti cannons, a fanfare, and a celebratory flip.
- **Twist:** the donation sequence described above, with the score turning warm and uplifting.

## Audio

Everything is original and synthesized deterministically by `scripts/build_audio.py`, with no samples. The 120 BPM score is built so scene cuts land on beats, in six sections: hook stabs and riser, driving start groove, full-percussion run, suspense drop (drone, heartbeat, rising tone, silence, snare roll), C-major fanfare, and warm pads with piano. There are 38 SFX, including beeps, buzzer, whooshes, footsteps, servos, boing, impacts, ping, squeak, clang, alarm, crowd cheers, confetti pops, coin stream and chimes.

## Rebuild

```bash
cd bolt-shorts && npm install
python3 scripts/build_audio.py && python3 scripts/make_srt.py
npx remotion render MainVideo out/bolt_001_100k_challenge.mp4
./scripts/master.sh            # -> deliverables/bolt_001_100k_challenge.mp4
npx remotion still Thumbnail deliverables/bolt_001_thumbnail.png
```
Render time is about 2 minutes on 4 cores.
