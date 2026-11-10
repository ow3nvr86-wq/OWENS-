THE WAR LOST TO BIRDS - a code-made cartoon Short (Emu War, Western Australia, 1932)

final_video.mp4                 1080x1920, 30 fps, 1256 frames, 41.87 s, H.264 CRF 17 + AAC 192k, 43 MB, captions burned in,
                                -14.2 LUFS integrated, true peak -1.4 dBFS
renders/final_video_no_voice.mp4  the same cut with music and SFX only, no captions (-14.2 LUFS, peak -0.3 dBFS)
QA: no frozen spans >= 0.4 s, no black frames (ffmpeg freezedetect / blackdetect); out/qa_sheet.jpg

HOW IT WAS MADE (cartoon-audio-short skill; the skill's kit was not supplied, so the engine was written for this video)
  narration      the user's ElevenLabs recording (audio/voice_user.mp3), used unchanged - the picture is timed to it
  timing         tools/word_timing.py (Whisper small.en word timestamps aligned to script.txt) + tools/refine_timing.py
                 (snaps phrase ends to the real pauses) -> work/words.json, work/phrases.json
  plan           work/PLAN.md (= storyboard.txt): 13 shots, one row per shot with frames, words, light, camera, SFX
  engine         web/main.js   three.js r160 in headless Chromium (CPU WebGL via SwiftShader): toon materials with a
                               2-step gradient, colour pass (4x MSAA) -> normal/depth pass -> ink (near side of depth
                               jumps + normal creases, never on cards) + grade -> depth of field (48-tap gather with a
                               per-sample CoC test)
                 web/world.js  the farm, wheat field, windmill, gum trees, army truck, Lewis guns, crate tower, camp map
                               table, Defence office desk and the casings mountain - primitives + painted canvas textures
                 web/cast.js   the bean-head characters and the emus, drawn on canvas with plum outlines (cards)
                 web/story.js  every shot as a pure function of the frame (cameras, cast, props, light, effects)
                 web/motion.js easing, springs, camera keys with creep and kicks, idle life, blinks
                 web/paint.js  painted textures (dirt, wheat, corrugated iron, planks, signs, clouds)
  render         render.mjs (Playwright -> frames/f0000.jpg ...; RESUME=1 continues an interrupted render)
  sound          audio.py (synthesised march + SFX stems) -> mix.py (level lock) -> finish.sh (master, encode, QA)
                 see sound_design.txt

RUN IT
  node render.mjs stills/a "0,300,700,1250" && python3 sheet.py stills/a stills/sheet.jpg     # look-dev stills
  SCALE=0.5 node render.mjs stills/half "0-60"                                              # half-size preview
  RESUME=1 node render.mjs frames "0-1255"                                                  # full render
  $SHORTS_PY audio.py && $SHORTS_PY mix.py audio/voice_user.mp3 audio/music.wav audio/sfx.wav
  bash finish.sh "The War Lost to Birds"

RENDER TIMES (4 CPU cores, no GPU)
  look-dev stills (about 90 frames over 6 passes)   ~4 min of rendering
  full render, 1256 frames at 1080x1920              2634 s = 44 min (0.6-4.8 s a frame)
  audio stems ~1 s; mix ~10 s; captions ~1.3 min; finish (mastering, two encodes, QA) ~2.5 min

AUDIO LEVELS (mix.py, measured)
  music -6.02 dB vs the voice's gated RMS (50 %); SFX -6.02 dB (50 %), SFX peak 0.65 x the voice peak.
  No ducking or compression; one linear gain to -14 LUFS plus a -3 dBFS peak limiter on the whole mix.
  Claude cannot listen to audio: the sound was checked by measured levels, loudness and timing only.

HONESTY
  Facts are in sources.txt (each checked in 2+ sources). The farm, people, letters, map, desk and the emu in the hat
  are illustrative; the notepad shows the major's own claimed figures (9,860 rounds, 986 emus).

CAPTIONS (added on request)
  tools/captions.py burns word-by-word captions onto the rendered frames (build/frames_cap): Anton, uppercase, white with
  a black outline and soft shadow, the spoken word in amber, max 3 words / 17 characters per chunk (each spoken phrase
  split into balanced chunks), about 64 % down; 80 % down while a readable prop fills the frame (gate sign, letters,
  map, notepad, desk). Numbers are shown as digits (1932, 20,000, 2, 10,000, 10). Timing from work/words.json; the
  chunk list is in work/caption_chunks.json. Check: all 109 caption words match the narration. subtitles.srt is still
  provided for YouTube closed captions.
  Re-run:  $SHORTS_PY tools/captions.py && bash finish.sh "The War Lost to Birds"   (~1.5 min + ~2.5 min)

LICENCES
  Code, drawings, textures and synthesised audio: made for this repository. three.js r160: MIT (web/vendor/THREE_LICENSE.txt).
  Fonts: Anton, Covered By Your Grace, Courier Prime - SIL Open Font License (web/fonts/OFL-*.txt).
  Narration: the user's own ElevenLabs recording.
