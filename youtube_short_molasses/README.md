# The Wave of Molasses: a code-generated 3D YouTube Short

A 59-second vertical Short about the 1919 Boston Molasses Flood. All of it was made with code: the 3D world, the animation, the flood physics, the captions and graphics, the music, the sound effects and the narration. No models, footage, templates or audio samples were downloaded. The only external assets are two open-licence fonts (SIL OFL, in `assets/fonts/`).

**Final video:** `renders/the_wave_of_molasses.mp4` (1080×1920, 9:16, 30 fps, H.264 + AAC 48 kHz)

## Folder layout

```
youtube_short_molasses/
├── README.md                     ← this file (includes rendering instructions)
├── research/sources.md           ← research report, fact table, sources, honesty notes
├── storyboard/
│   ├── voiceover_script.md       ← final VO script with measured timings
│   └── storyboard.md             ← scene-by-scene storyboard (shots, cameras, graphics, transitions)
├── scripts/
│   ├── script.json               ← VO lines, pauses and caption spellings (single source of truth)
│   ├── voiceover.py              ← Piper TTS → audio/vo/*.wav + build/timeline.json
│   ├── layout.py                 ← shared 1919 waterfront layout (used by the sim and by Blender)
│   ├── simulate_flood.py         ← 2D shallow-water dam-break simulation → build/flood_sim.npz
│   ├── animation.py              ← complete Blender (bpy) scene, animation and render script
│   ├── render_all.sh             ← resumable chunked render helper
│   ├── audio.py                  ← synthesised score + SFX + mix → audio/*.wav + timing sheet
│   └── post.py                   ← upscale, grade, transitions, captions, graphics, encode → MP4
├── audio/
│   ├── vo/                       ← per-line voiceover + voiceover.wav
│   ├── music/score.wav           ← synthesised score stem
│   ├── sfx/sfx.wav               ← synthesised sound-effects stem
│   ├── mix.wav                   ← final mix
│   └── timing_sheet.md           ← audio and SFX timing sheet (VO, cuts, every music/SFX cue)
├── assets/fonts/                 ← Anton, Old Standard TT (SIL Open Font License)
├── renders/                      ← final MP4 (frames/ is git-ignored)
└── build/                        ← generated data: timeline.json, events.json, flood_sim.npz (git-ignored)
```

## Pipeline

1. **Research**: `research/sources.md`.
2. **Voiceover**: `voiceover.py` synthesises each line and measures its length. Every later stage reads `build/timeline.json`, so the shot cuts follow the real narration.
3. **Physics**: `simulate_flood.py` runs a second-order MUSCL/HLL finite-volume shallow-water solver on a 1 m grid:
   - Molasses: 8,700 m³ released instantly from the 90 ft × 50 ft tank. Buildings act as walls, molasses that reaches the harbour sinks, and there is turbulent bed friction plus a laminar viscous drag whose viscosity rises ×4 into the night.
   - Objects carried along: debris is advected by the flow, and the wooden house is pushed by the simulated drag.
   - Elevated railway: the momentum hitting its columns drives how far the girders bend.
4. **3D**: `animation.py` builds everything procedurally in Blender 4.2:
   - Streets and city: cobbles, granite, brick facades with lit windows, the elevated railway, harbour, piers, a schooner and the Old North Church steeple.
   - The tank: 16 riveted panels with about 6,400 instanced rivets, a brown paint wipe and leak streaks.
   - Props and people: debris, vehicles, articulated mannequins and a thermometer.
   - Shots: 17 keyframed camera rigs.
   - Animation: a frame handler streams the simulation into the molasses mesh every frame.
   - Look: lighting from a Nishita sky plus sun, moon and gas lamps; compositor mist and glare.
5. **Audio**: `audio.py` synthesises the D-minor score (pads, ostinato, taiko-style drums, risers, impacts) and every effect. The rivet pings and drips use the exact animation event times from `build/events.json`. Music is ducked under the voice, and a soft limiter brings the master to −1 dBFS.
6. **Post**: `post.py` turns the frames into the finished video:
   - upscales to 1080×1920, grades the frames, and adds vignette and film grain;
   - adds the flash, dip-to-black, whip and shake transitions;
   - draws the word-by-word captions and the stat graphics (the 50 FT bracket is locked to the tank by 3D projection);
   - encodes with ffmpeg.

## Rendering instructions

Requirements:
- Blender 4.2 LTS (tested with 4.2.3) and ffmpeg.
- Python 3.10 or later with `numpy scipy pillow piper-tts`.
- The Piper voice `en_US-ljspeech-high` (`.onnx` and `.onnx.json` from huggingface.co/rhasspy/piper-voices). It was trained on the public-domain LJ Speech dataset.

```bash
cd youtube_short_molasses
python -m venv .venv && .venv/bin/pip install numpy scipy pillow piper-tts

# 1. narration and timeline
.venv/bin/python scripts/voiceover.py --model /path/to/en_US-ljspeech-high.onnx
# 2. flood physics (~1 min)
.venv/bin/python scripts/simulate_flood.py
# 3. cue/anchor export, then the 3D render (1,778 frames)
blender -b --factory-startup -P scripts/animation.py -- --export-events
BLENDER=blender scripts/render_all.sh 1 1778          # resumable; re-run to continue
# 4. score, SFX and mix
.venv/bin/python scripts/audio.py
# 5. post-production and encode
.venv/bin/python scripts/post.py                       # → renders/the_wave_of_molasses.mp4
```

Useful options:
- `animation.py -- --quality preview --stills 70,880,1440` renders 270×480 framing checks.
- `--save-blend build/scene.blend` saves the generated scene so you can inspect it in the Blender UI.
- `post.py --stills 290,700` writes finished frames to `build/post/` for checking.

### Render budget and resolution

This video was rendered on a cloud machine with 4 CPU cores and no GPU:
- **Cycles render:** 540×960, 8 adaptive samples, OpenImageDenoise, about 8.7 s per frame (about 4.3 hours for 1,778 frames).
- **Upscale:** `post.py` upscales 2× with Lanczos and an unsharp mask. Captions and graphics are drawn natively at 1080×1920, so the text is fully sharp.

On a GPU machine, change `resolution_percentage` for `'final'` in `setup_render()` to `100` (and raise `samples`) to render natively at 1080×1920. `post.py` then skips nothing; the resize becomes a no-op.

## Honesty notes

- The narration quotes historical estimates: "up to 25 ft", "35 mph", and "at least four times" thicker (2016 APS study). The simulation is a simplified model. It produces about 15 ft and 24 mph in the street, so the wave shots steepen the leading edge and exaggerate height by up to 1.5× to match the eyewitness estimates. The details are in `research/sources.md`.
- The street layout is illustrative, not a survey of 1919 Commercial Street.
- The figures are anonymous, stylised mannequins.
- The voice is synthetic (Piper TTS), and all music and effects are synthesised. Nothing was recorded.

## Licences

- Code: as for this repository.
- Fonts: Anton and Old Standard TT, SIL Open Font License 1.1 (licence texts in `assets/fonts/`).
- Voice: Piper `en_US-ljspeech-high`, trained on the public-domain LJ Speech dataset. I switched from `en_US-ryan-high` because that voice's training data is CC BY-NC-SA, which is non-commercial. The model isn't redistributed here.
