# Dyatlov Pass: a code-generated cinematic 3D YouTube Short

A 60-second vertical dark-history Short about the 1959 Dyatlov Pass incident. The whole video is generated with code by one Blender (bpy) script, `animation.py`:

- **World:** the mountains, forest, rocks, tent, gear, footprints and the nine hikers.
- **Motion and effects:** the snow and wind, and the avalanche simulation.
- **Look:** the lighting, fog and grade.
- **Edit:** the titles, captions, transitions and film grain.
- **Sound:** the music and sound effects.
- **Encode:** the final MP4.

No models, footage, stock, templates or audio samples were downloaded. The only external assets are two open-licence fonts (`assets/fonts/`, SIL OFL).

**Final video:** `renders/dyatlov_pass_final.mp4`
- 1080×1920 (9:16), 30 fps, 60.0 s, H.264 + AAC.
- Narration by a synthetic male voice (Piper `en_US-joe-medium`, CC0).
- Burned-in captions.

**For CapCut:** `renders/dyatlov_pass_no_voice.mp4` is the same video with music and SFX only and no narration captions. The titles and on-screen facts are kept. Add your own AI voiceover from `narration.txt` and let CapCut auto-caption it; `subtitles.srt` is also provided.

## Folder layout

```
Dyatlov_Pass/
├── animation.py          ← the complete Blender script: 3D scene, animation, render, audio, edit, encode
├── narration.txt         ← narration script, scene by scene, with start times
├── subtitles.srt         ← subtitles timed to the narration
├── scene_timing.md       ← timing sheet: scenes, shots, frames, narration, on-screen text, events
├── scene_timing.json     ← the timing system (single source of truth read by everything)
├── README.md
├── tools/voiceover.py    ← Piper TTS narration + generates narration.txt / subtitles.srt / scene_timing.md
├── render_all.sh         ← resumable chunked render of all 3D frames
├── audio/                ← narration.wav, mix_with_voice.wav, mix_no_voice.wav, timing_sheet.md
├── assets/fonts/         ← Anton, Old Standard TT (SIL Open Font License)
└── renders/
    ├── dyatlov_pass_final.mp4
    └── dyatlov_pass_no_voice.mp4
```

`build/` (photos, map, simulation cache, timings) and `renders/frames/` are generated and git-ignored.

## The five scenes

| Scene | Time | What you see |
|---|---|---|
| 1. The hook | 0–6 s | Aerial descent over a moonlit Ural range and forest, down to nine hikers on skis; low tracking shot beside them with moon shadows, wind and snow. |
| 2. The discovery | 6–17 s | The half-collapsed, snow-covered tent. A dolly along the slashed canvas. Footprints leading down to the forest. |
| 3. Mystery and theories | 17–29 s | Investigator's desk (map, archive photos, case file, "CASE CLOSED" stamp). A rocket trail and glowing orbs over the ridge, labelled **THEORY** and **SPECULATION, NOT EVIDENCE**. |
| 4. The avalanche theory | 29–44 s | A cut-away of the slope: the platform is dug, the tent pitched, and wind-blown snow builds up above the cut. A slab releases and the slab simulation pushes the tent down. Labelled **SIMULATION, NOT FOOTAGE**. |
| 5. The ending | 44–60 s | Back to the tent in falling snow. A crane pulls away up the mountain and fades to black. Then **DYATLOV PASS / WHAT REALLY HAPPENED?**, then fade out. |

`scene_timing.md` has every shot, frame range, narration line and on-screen text.

## How it is built (all in `animation.py`)

- **Terrain:** a 250,000-vertex polar-grid mesh centred on the camp, fine near the tent (centimetres) and coarse at 30 km. Heights come from a vectorised numpy Perlin / ridged-noise height function: a summit dome, an open east slope, a forested valley about 1.5 km below and distant ranges. The camp sits on a dug platform.
- **Forest and rocks:** about 230,000 snow-laden spruce instances, plus 800 rocks, scattered below a noisy tree line with Geometry Nodes.
- **Tent:** a 1959-style canvas ridge tent built as a procedural cloth surface:
  - one end still standing and the other collapsed;
  - a snow load that is heavier uphill;
  - lens-shaped cuts in the downslope wall;
  - gear around it: skis, poles, boots, an ice axe, a flashlight, a jacket.
- **Footprints:** nine lines of prints (about 2,100 meshes) running from the tent downhill.
- **Hikers:** nine articulated figures built procedurally:
  - **Clothing:** period winter gear (anoraks with hoods or knitted caps, mittens, canvas rucksacks with bed-rolls).
  - **Equipment:** wooden skis and poles.
  - **Motion:** a ski-walking cycle with leg kinematics. The hips are lifted so the skis follow the slope.
  - **Lamps:** three of them carry lamps.
- **Snow and wind:** a deterministic particle system of up to 14,000 flakes, each a streak stretched along its velocity. Positions are a pure function of time, so any frame can be rendered independently. Wind, turbulence, box size and flake size are set per shot. The wind-loading shot uses a surface "saltation" mode where the snow skims down the slope.
- **Avalanche:** a discrete-element simulation in numpy, run once and cached:
  - **Slab:** 90 blocks bonded to their neighbours by springs. Bonds break at random strain limits, so the slab fractures irregularly.
  - **Contact:** the blocks rest on the slope profile with Coulomb friction, and the weak layer lets go at the release time.
  - **Tent:** the roof pushes back softly and collapses under the measured load.
  - **Snow dust:** thrown up wherever fast blocks hit something.
  - **Timing:** the tent-impact time from the simulation drives the impact sound and the flash.
- **Desk:** a wooden desk under a banker's lamp, all made by the script:
  - **Map:** a topographic map painted from the same height function (contours, forest, river, route, tent mark).
  - **Photos:** three black-and-white "archive photos" rendered from this 3D scene.
  - **Documents:** typed text objects for the case file.
- **Cameras:** one keyframed rig per shot, all with Track-To targets:
  - an aerial descent;
  - tracking, dolly and crane moves;
  - slow push-ins;
  - an orbit and handheld-style shake at the slab impact.

  Most use depth of field. Cameras are framed for 9:16, and timeline markers switch them at the cuts.
- **Lighting and look:** a moon sun-lamp and a separate moon disc. Light direction, strength, fog and exposure are keyed per shot. The sky is a dark gradient, and the stars are on a dome visible only to the camera. The compositor adds distance fog from the mist pass, moonbeams from the Sun Beams node, fog glow and a cold lift/gamma/gain grade, under AgX.
- **Edit:** done in the Video Sequence Editor:
  - **Picture:** the 540×960 frames are upscaled 2× with a bicubic filter, plus a vignette and animated film grain.
  - **Transitions:** dips to black between scenes, a white flash at the slab release and a softer one at the impact, and a fade to black.
  - **Text:** animated titles, labels and captions with outline, shadow and fades.
  - **Output:** H.264, 8 Mbps (capped at 9 Mbps), AAC 192 kbps 48 kHz, `+faststart`.
- **Audio:** synthesised with numpy and loudness-normalised to −14 LUFS with ffmpeg:
  - **Ambience:** gusty stereo wind and howl.
  - **Score:** a D-minor drone pad, a heartbeat pulse, a music-box motif, low booms on the cuts, and noise risers.
  - **Effects:** ski crunches, canvas flutter, paper, the stamp, the rocket rumble and orb hum, shovel scrapes, the slab crack (after 0.14 s of silence), the slide rumble and the impact thud.
  - **Ducking:** music and wind duck under the narration.
  - `audio/timing_sheet.md` lists every cue.

## Rendering instructions

Requirements: Blender 4.2 LTS (tested with 4.2.3) and ffmpeg. The voiceover helper also needs Python 3.10 or later with `numpy` and `piper-tts`, plus the voice model `en_US-joe-medium` from huggingface.co/rhasspy/piper-voices. In this repo's Claude Code cloud sessions the SessionStart hook installs all of these and exports `$BLENDER`, `$SHORTS_PY` and `$PIPER_VOICES`.

```bash
cd Dyatlov_Pass
# 1. narration + subtitles + timing docs (optional: skip if you record the voice in CapCut)
$SHORTS_PY tools/voiceover.py                      # or: --no-tts for estimated timings without a voice
# 2. look-dev stills (270x480), then the full 3D render (resumable, ~13 s/frame on 4 CPU cores)
$BLENDER -b --factory-startup -P animation.py -- --quality preview --stills 60,240,600,840,1300
BLENDER=$BLENDER ./render_all.sh 1 1590
# 3. music + SFX + mixes
$BLENDER -b --factory-startup -P animation.py -- --stage audio
# 4. edit + encode
$BLENDER -b --factory-startup -P animation.py -- --stage edit                 # renders/dyatlov_pass_final.mp4
$BLENDER -b --factory-startup -P animation.py -- --stage edit --no-voice      # renders/dyatlov_pass_no_voice.mp4
```

`--stage all` runs render, audio and edit in one go. `--save-blend PATH` saves the generated scene for inspection in the Blender UI.

### Timing system: matching your own voiceover

Every time in the video comes from `scene_timing.json`:
- scene and shot boundaries;
- narration line start times;
- title times;
- animation events (dig, tent pitch, wind load, slab release, sky lights, fade).

If you record a different voiceover (for example in CapCut) and a line lands somewhere else, change the times there. Then re-run `tools/voiceover.py`, which updates `narration.txt`, `subtitles.srt` and `scene_timing.md`, and re-render the affected frames and the edit. A camera cut or event moves with the JSON, not with hand-edited keyframes.

### Render budget

This video was rendered on a cloud machine with 4 CPU cores and no GPU:
- **3D render:** Cycles at 540×960, 8 adaptive samples and OpenImageDenoise. That took about 12–15 s per frame, so about 6 hours for the 1,590 3D frames (0–53 s).
- **End card (53–60 s):** drawn in the edit.
- **Upscale and text:** the edit upscales to 1080×1920, and all text is drawn natively at 1080×1920, so it stays sharp.

On a GPU machine, set `resolution_percentage` for `'final'` to 100 in `setup_render()` and raise the samples.

## Facts used, and sources

| Claim in the video | Source(s) | Notes |
|---|---|---|
| February 1959; nine hikers in the northern Urals; none survived | Wikipedia (Dyatlov Pass incident); Advanced Science News / EPFL (2021) | Ten set out; Yuri Yudin turned back on 28 Jan with knee/joint pain (shown on the desk notes). |
| Tent found 26 Feb 1959, half torn down and covered in snow, cut open from the inside | Wikipedia (quoting searcher Mikhail Sharavin and the investigation) | |
| Footprints in socks, a single shoe or barefoot, leading downhill (~1.5 km) toward the forest | Wikipedia | Narration says "in socks or bare feet"; on-screen "TRACKS LED ~1.5 KM DOWNHILL". |
| 1959 verdict: "a compelling natural force"; case closed May 1959 | Wikipedia | Desk documents are an illustrative reconstruction in English, not copies of the real files. |
| Theories: weapons tests; strange lights in the sky | Wikipedia (orange spheres reported in the night sky by another group and by witnesses around Ivdel, Feb–Mar 1959; military-test theories) | Shown **only** as labelled speculation. |
| 2020: Russian prosecutors attributed the deaths to an avalanche | TASS; RBTH; RFE/RL (July 2020) | "Not everyone is convinced": the relatives' lawyer rejected the finding (RBTH). |
| 2021 study: delayed slab avalanche; slope cut for the tent plus wind-blown snow; release hours later | Gaume & Puzrin, *Communications Earth & Environment* 2, 10 (2021), doi:10.1038/s43247-020-00081-8; EPFL / Advanced Science News coverage | Authors: the theory is "plausible", "no one really knows what happened that night". Coverage says release was at least ~9 h after the cut. The video says "may have". |

Sources:
- https://en.wikipedia.org/wiki/Dyatlov_Pass_incident
- https://www.nature.com/articles/s43247-020-00081-8 (Gaume & Puzrin 2021, open access)
- https://infoscience.epfl.ch/entities/publication/cc46c95a-9cd5-4748-ac51-5e4094128089
- https://www.advancedsciencenews.com/researchers-shed-light-on-the-1959-dyatlov-pass-incident/
- https://tass.com/emergencies/1177345
- https://www.rbth.com/history/332434-official-cause-of-death-of-the-dyatlov-group
- https://www.rferl.org/a/russian-officials-reportedly-close-investigation-into-mysterious-1959-hiking-disaster-dyatlov/30722068.html

## Honesty notes

- **Theories are labelled as theories.** The rocket trail and orange orbs are on screen with "THEORY" and "SPECULATION, NOT EVIDENCE". They are not presented as events that happened.
- **The avalanche scene is an illustration.**
  - It is labelled "SIMULATION, NOT FOOTAGE".
  - The cut-away slope, its angle (24°) and the slab size are illustrative and chosen for clarity, not the study's measured values.
  - The block simulation shows the *mechanism* of the hypothesis (cut, wind loading, delayed slab release, impact on the tent). It is not the study's model.
- **The scene is not a reconstruction.**
  - The terrain is procedural, not a survey of Kholat Syakhl.
  - The tent's size and the positions of the cuts, gear and footprints are illustrative.
  - The night-time hiking in scene 1 is artistic: the group pitched the tent in the evening of 1 February.
  - The moon disc is placed for composition in the opening shot.
- **No injuries or deaths are depicted.** The hikers are anonymous, stylised figures with no likenesses of the real people, and nobody is shown in the avalanche scene.
- **Nothing was recorded.** The narration is a synthetic voice (Piper TTS), and all music and effects are synthesised.

## Licences

- **Code:** as for this repository.
- **Fonts:** Anton and Old Standard TT are under the SIL Open Font License 1.1 (texts in `assets/fonts/`). DejaVu Sans Mono is bundled with Blender and used for the typed documents.
- **Voice:** Piper `en_US-joe-medium`, CC0. The model isn't redistributed here.
