# Shorts Factory

2D cartoon characters composited over 3D-rendered backgrounds, cut to the voice word by word.
Output: `final.mp4` (H.264 1080x1920, 30 fps, AAC 48 kHz, about -14 LUFS) plus `thumbnail.png`.

Example episode: `episodes/hwacha_haengju/` ("How a Rocket Cart Stopped an Army", 59.7 s).

## Make a new episode: the files to swap

Copy the example folder (`cp -r episodes/hwacha_haengju episodes/<new_name>`), delete its `work/`, `audio/`,
`final.mp4` and `thumbnail.png`, then replace these four things:

| File | What it is | Notes |
|---|---|---|
| `narration.txt` | The script, one sentence or beat per line, 150-170 words | Write numbers as words ("thirty thousand"). Captions show digits through `caption_swaps`. |
| `voice.wav` | Your recorded voice (any length, any sample rate) | Optional. Drop your own file in to use it. Delete it to get the Kokoro `bm_george` voice instead. The wording must match `narration.txt`. |
| `backgrounds/*.png` | One image per location, 9:16 or larger | Any render or painting. Name it exactly as in `script.json` `bg`. An optional `<name>_fg.png` (with alpha) is drawn in front of the characters, e.g. a wall or branches. |
| `script.json` | Shots, cast, camera, effects, sound cues | See below. Each scene starts on a *cue word* from the narration, so timing follows the voice automatically. |

Then run one command:

```bash
./make_episode.sh episodes/<new_name>
```

That runs these steps in order:
1. Voice: keeps yours, or makes TTS.
2. Whisper word alignment.
3. Frame render (about 1-2 minutes).
4. Music and SFX mix.
5. Mastering, encode and thumbnail.

If you only change `script.json`, re-run steps 3-5 (`node tools/render.mjs ...`, `tools/audio.py`, `tools/finish.py`). If you only change the narration or voice, run everything again.

To make placeholder 3D backgrounds with Blender instead of supplying images, add a preset to `tools/bg_blender.py`
and run:

```bash
$BLENDER -b --factory-startup -P tools/bg_blender.py -- episodes/<name>/backgrounds <preset> --scale 0.8
```

Pass `fg=True` to `palisade()`, or tag any object with `ob['fg'] = True`, to also get the `_fg.png` layer.

## script.json

Top level:
- `title`
- `caption_y`: caption height, as a fraction of the frame (0.68).
- `caption_swaps`: spoken words mapped to on-screen text, e.g. `{"ten to one": "10:1"}`.
- `grade`: a CSS filter applied to the backgrounds.
- `thumbnail_cue`: the word whose frame becomes the thumbnail.
- `music`: `{"bpm": 104, "level_db": -20}`.
- `cast`: each character id maps to `{costume, hat, facial, mood}`. These are original parametric designs:
  - **costume:** armor_red, armor_blue, coat_green, ashigaru, samurai, peasant, overalls, vest, tunic.
  - **hat:** plume_helmet, joseon_helmet, gat, jingasa, kabuto, top_hat, flat_cap, none.
  - **facial:** any of "moustache goatee beard".

Each entry in `scenes` (a new shot every 1.5-3 s) has:
- `cue`: the first word(s) of the shot. They must appear in the narration, in order.
- `bg`: the background file.
- `bgBlur`, `bgFilter` (for example `"brightness(1.4)"`), `tint`, and `fg: false` to hide the foreground layer.
- `camera`: `{move, zoom, amount, focus:[x,y]}`. `move` is one of push, pull, pan_left, pan_right, tilt_up, tilt_down, drift or punch.
- `transition` into the next shot: `cut`, `whip` or `zoom`.
- `characters`, a list of `{id, cast, x, y, scale, action, mood, flip, prop, look, talk, move, keys}`:
  - `x, y` are the feet position, as fractions of the frame. `scale` 1 is about 420 px tall. With `y = 0.5 + 0.16*scale` the head sits at mid-frame, clear of the captions.
  - **action:** idle, point, present, cheer, crossed, shrug, flail, torch, march, run, talk.
  - **mood** (eyebrows, eyes and mouth): neutral, happy, smug, angry, determined, worried, shocked, sad, scared.
  - `talk: ["Not", "great"]` flaps the mouth from the voice amplitude between those two cue words.
  - `move: {x, from, to}` walks the character to a new x between two cue words.
  - `keys: [{cue, action, mood}]` switches pose or mood on a word.
  - Blinking, idle bob and walk cycles are automatic.
- `crowds`, a list of `{cast:[ids], count, area:[x0,y0,x1,y1], scale:[far,near], action, mood, speed, dy, wrap, wrapY, taper, flip, seed}`.
  - These draw 30-100+ marching or charging figures, sorted by depth.
  - `taper` narrows the crowd toward the horizon, and `wrapY` makes endless waves.
- `fx`, a list where each entry has `type` and `at` (a cue word):
  - `rockets`: from, to, count, spread, arc, dur, persp, fromSpread, shake.
  - `puff`, `sparks`, `impact`: x, y, r.
  - `glow`: amount.
- `sfx`, a list of `{type, at, gain}`.
  - **type:** whoosh, boing, knock, ting, gulp, tada, sting, fuse, volley, boom, charge, scramble, sneeze, drums, march, pop.
  - Whip and zoom transitions add a whoosh automatically.

## What each part does

- `tools/voice.py`: uses your `voice.wav`, otherwise Kokoro TTS of `narration.txt`.
- `tools/align.py`: runs Whisper in silence-cut windows, then aligns the result to `narration.txt`. Writes `work/words.json` (word times) and `work/amp.json` (per-frame loudness for the mouth flaps).
- `engine/`: the canvas compositor (characters.js, effects.js, compositor.js). It runs in headless Chromium.
  - Every frame is a pure function of time, so frames render in parallel and can resume (`RESUME=1`).
  - Captions are 1-2 words, Poppins ExtraBold 90 px, with a white fill, black stroke and soft shadow. Each pops in from 0.85 to 1.0 over 4 frames.
- `tools/render.mjs`: renders frames to `work/frames/`. It also takes `"0-299"` or `"10,200,450"` for test stills.
- `tools/audio.py`: synthesised march music and cartoon SFX.
  - Levels: voice at 0 dB, music about -19 dB under it (ducked while speaking), SFX about -12 dB.
- `tools/finish.py`: two-pass loudnorm to -14 LUFS / -1.5 dBTP, x264 CRF 19 (capped at 9 Mbps, so files stay under 100 MB), and the thumbnail.
- `tools/bg_blender.py`: placeholder Cycles backgrounds with sky, sun, soft shadows and depth of field.

Honesty rules for every episode:
- Check each fact in 2+ sources and record it in `sources.txt`.
- Hedge where sources disagree ("around", "up to").
- Never invent quotes or numbers.
- Characters are original stylised designs, never real people's likenesses.
