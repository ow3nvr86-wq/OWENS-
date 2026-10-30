---
name: make-3d-short
description: Research a topic and produce a complete, fully code-generated 3D animated YouTube Short (1080x1920, 30 fps, 45-60 s) - verified research with sources, voiceover script, storyboard, procedural Blender (bpy) scene and animation, optional physics simulation, synthesized music/SFX, animated captions, and a final MP4. Use this skill whenever the user asks for a YouTube Short, TikTok/Reel, vertical video, explainer animation, "3D animated video about X", or sends a topic and wants it turned into an animated short - even if they don't say "Blender" or "Short" explicitly. Also use it when they want to change the voice, music, captions or shots of an existing short in this repo.
---

# Make a code-generated 3D Short

You are producing an educational 3D-animated Short where *everything* is made with code: 3D world, animation, physics, captions, music, SFX and narration. There are two reference implementations in this repo: `youtube_short_molasses/` ("The Wave of Molasses", 59 s: multi-script pipeline with a PIL post stage) and `Dyatlov_Pass/` (60 s: one self-contained `animation.py` with render/audio/edit stages, the edit done in Blender's Video Sequencer, timing from `scene_timing.json`; use it when the user wants a single Blender script that renders the final video). Read its `README.md` first and reuse its scripts as your starting template - they already solve the hard plumbing (timeline-driven cuts, frame handlers, event export, ducking, captions, delivery encode). Copy them into a new project folder and adapt; don't rewrite from scratch.

## Toolchain (cloud sessions)

The repo's SessionStart hook (`.claude/hooks/session-start.sh`) installs everything into `/opt/shorts` and exports:
- `$BLENDER` - Blender 4.2.3 (headless Cycles)
- `$SHORTS_PY` - Python venv with numpy, scipy, pillow, piper-tts
- `$PIPER_VOICES` - narrator voices cleared for commercial use
- `$KOKORO_PY`, `$KOKORO_DIR` - Kokoro-82M TTS (Apache-2.0), much more natural than Piper

If the variables are missing, run the hook script yourself (it is idempotent). The machine is 4 CPU cores and **no GPU** - this drives the render budget below.

## Pipeline

Work through these stages in order and don't stop after the storyboard - the deliverable is the finished MP4.

1. **Research** (`research/sources.md`). Pick the most surprising, visual angle. Verify every on-screen number in 2+ sources (WebSearch/WebFetch); where sources disagree, phrase it honestly ("up to", "around", "estimated"). Keep a table: claim -> value used -> sources -> notes. Note facts you cut. Never present speculation as fact.
2. **Script** (`scripts/script.json` + `storyboard/voiceover_script.md`). Hook (0-3 s) / setup (to ~12 s) / story (to ~40 s) / payoff (to ~55 s) / ending question. ~150-165 words. Captions can spell numbers as digits while the narration spells them out (see `captions` map in the reference script.json).
3. **Voiceover** (`scripts/voiceover.py`). Synthesize per line, trim silence, write `build/timeline.json`. **Every later stage reads this timeline**, so do it before any animation work; cuts are derived from real line timings, never guessed. Check total duration: narration + ~1.6 s end hold must stay <= 60 s. Tune with `--length-scale` and the per-line `pause` values.
4. **Physics (optional but powerful)**. If the topic has a physical event (flood, collapse, explosion, orbit, crowd), simulate it in numpy and stream the result into Blender each frame (see `simulate_flood.py`: 2D shallow water, rigid debris advected by the flow). Real simulation beats hand-keyed motion and is a great talking point. Document any visual exaggeration.
5. **3D scene** (`scripts/animation.py`). Procedural everything: bmesh geometry, node-based materials, cameras on keyframed rigs with Track-To targets, one camera per shot bound via timeline markers, a `frame_change_pre` handler for data-driven motion, keyframed `hide_render` for per-shot visibility, an ENV node group for globally animated material values (night, frost, paint wipe...). Export cue times and 3D->screen anchor points with `--export-events` so audio and graphics sync exactly.
6. **Look-dev loop**. Render one 270x480 preview still per shot (`--quality preview --stills ...`), assemble a contact sheet, *look at it*, fix, repeat. Then render 3-4 stills at final settings before committing hours to the full render. This loop caught most problems in the reference project - don't skip it.
7. **Full render**. Resumable chunks (`scripts/render_all.sh A B`, `use_overwrite=False`). Run each chunk with `run_in_background` (max 2 h per command); check a few finished frames through post after the first chunk.
8. **Audio** (`scripts/audio.py`). Synthesized score (pads, ostinato, drums, risers, impacts) and SFX timed from `build/events.json`; music ducked under the voice; strategic silence before the big impact. Writes stems, `audio/mix.wav` and `audio/timing_sheet.md`.
9. **Post** (`scripts/post.py`). Upscale, grade, vignette, grain, transitions (flash/whip/dip), word-by-word captions, stat graphics, encode with audio.
10. **QC on the actual MP4**: ffprobe (1080x1920, 30 fps, duration), a contact sheet of decoded frames across every shot, captions matching narration, EBU R128 loudness ~-14 LUFS. Then commit and push, and send the MP4 to the user (SendUserFile).

Deliverable folder layout (one folder per video, e.g. `youtube_short_<slug>/`): `research/`, `storyboard/`, `scripts/`, `audio/{vo,music,sfx}`, `assets/fonts/`, `renders/` (MP4 committed, `frames/` git-ignored), `build/` (git-ignored), `README.md` with rendering instructions and honesty notes, `requirements.txt`.

## Defaults and preferences

- **Narrator**: the user prefers a **male** voice and found Piper voices too robotic. Default to **Kokoro `bm_george`** (British male, Apache-2.0) via `$KOKORO_PY` (see `Dyatlov_Pass/tools/voiceover.py`, `--engine kokoro`); other good Kokoro males: `am_michael`, `am_fenrir`, `am_onyx`, `bm_fable`. Kokoro reads slower than Piper, so give lines roomier slots. Piper fallbacks: `en_US-joe-medium` (CC0); alternatives `en_US-bryce-medium`, `en_US-john-medium`, `en_US-norman-medium` (public domain). `en_US-ljspeech-high` (female, public domain) was used for the molasses video. Never use `en_US-ryan-*` - its dataset is CC BY-NC-SA (non-commercial), a problem for monetized videos. Check any other voice's MODEL_CARD license first.
- **Captions**: Anton, uppercase, white with black outline + soft shadow, active word in amber, max 3 words / 17 chars per chunk, centred ~64% down the frame (clear of Shorts UI at bottom and right).
- **Graphics**: big Anton numbers in amber with a short tag underneath; period/date tags in a serif on cream. Keep top graphics above y~600 px and captions around y~1235 px.
- **Delivery**: H.264 CRF 19 capped at 9 Mbps (keeps files < 100 MB for GitHub), AAC 192k 48 kHz, `loudnorm=I=-14:TP=-1.5`, `+faststart`.

## Hard-won lessons

Read `references/lessons.md` before building the scene - it lists the specific failures from the first video and their fixes (render budget numbers, Blender 4.2 API traps, materials that read as chrome, cameras that end up underwater, keyframe collisions, caption carry-over, etc.). The short version:

- **Budget the render first.** On 4 CPU cores Cycles at 540x960, 8 spp + OIDN costs ~8.5 s/frame by day and ~15 s at night -> ~5 h for 1,780 frames. Render at 50 % and upscale 2x in post; captions are drawn natively at 1080x1920 so text stays sharp. EEVEE via software GL is *slower* here - don't use it.
- **Bump nodes and heavy procedural shaders dominate render time** - keep bump only where the camera gets close.
- **Tell the user the timeline** (hours, not minutes) when the full render starts, and keep committing/pushing finished stages so nothing is lost.
- **Honesty**: if visuals exaggerate the physics or the layout is illustrative, say so in the README and research notes. Stylized mannequins for people; never depict real victims' likenesses.

## When the user asks for changes to an existing video

Figure out the cheapest stage that has to re-run:
- Voice swap with the same pacing -> regenerate VO, time-stretch each line into its existing slot if needed (ffmpeg `atempo` within ~0.9-1.1), re-run `audio.py` and `post.py` (~30 min). If the new voice is much slower, re-timing forces a full re-render - tell the user before doing that.
- Captions / graphics / grade / transitions -> `post.py` only (~15 min).
- Music / SFX -> `audio.py` + `post.py`.
- Anything visible in 3D (shots, materials, lighting, camera) -> re-render the affected frame ranges only (`render_all.sh A B` after deleting those frames), then post.
