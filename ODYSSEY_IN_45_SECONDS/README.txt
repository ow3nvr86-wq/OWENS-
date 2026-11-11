THE ODYSSEY IN 45 SECONDS - a stick-figure Short retelling Christopher Nolan's The Odyssey (2026). SPOILERS.

final_video.mp4                   1080x1920, 30 fps, 42.9 s, H.264 (CRF 18, 9 Mbps cap) + AAC 192k, 49.5 MB,
                                  -14.2 LUFS, true peak -1.8 dBFS. Captions are drawn into the frames.
renders/final_video_no_voice.mp4  music + SFX only on the same frames (captions included), -14.4 LUFS, peak -1.4 dBFS
QA: ffprobe ok; no frozen spans >= 0.4 s; the only black frames are the deliberate cut to black after "him" (42.73 s).

HOW IT WAS MADE (stick-figure skill; its engine wasn't supplied, so a 2D canvas engine was written to its spec)
  narration   the user's ElevenLabs recording (audio/vo.mp3, "Ryan Kurk - Pleasant and Smooth"), used unchanged
  timing      tools/word_timing.py (Whisper word times aligned to script.txt: 100 % word match) + tools/refine_timing.py
              -> work/words.json; every shot starts ~2 frames before its word
  engine      web/lib.js (easing, keyframes, ink shapes), web/chars.js (stick rig with big white heads and faces,
              helmets, beards, hoods; the Cyclops, ghosts, pigs, the sacred cow, Sirens), web/env.js (sky, sea, ships,
              islands, burning Troy, the cave, the underworld, storm, palace hall), web/shots.js (22 shots in narration
              seconds), web/main.js (camera with handheld drift, whip transitions with motion blur, flashes, vignette,
              grain, 1-2 word lowercase Poppins Bold captions ~70 % down)
  render      node render.mjs frames "0-1287"   (headless Chromium, ~4 min for all frames)
  sound       audio.py: plucked lyre underscore in a Greek-sounding mode, ducked under the voice (~15 dB below it);
              ~60 synthesised SFX placed on the word times (stab, zap, ghosts, chomps, clang, boulders, poofs, oinks,
              the Sirens' song, a moo, thunder, harp, clock ticks, crowd, door, bow creaks and twang, record scratch on
              "The twist?", war horns, the final hit) at ~0.38 of the voice level. finish.sh: one gain to -14 LUFS +
              a peak limiter, encode, QA.
  Claude cannot listen to audio: the sound was checked by levels, loudness and timing only.

RUN IT
  node render.mjs build/stills/a "0,138,498,1272" && python3 sheet.py build/stills/a build/stills/sheet.jpg
  node render.mjs frames "0-1287"
  $SHORTS_PY audio.py && bash finish.sh

RENDER TIMES (4 CPU cores): stills ~5 s per pass; full render 234 s; audio 3 s; finish ~3 min.

HONESTY / RIGHTS
  Plot beats are from the film's coverage (sources.txt). All characters are original stick-figure designs of the
  myth's characters - no actor likenesses, no film footage, posters or logos. Fonts: Poppins (SIL OFL,
  web/fonts/OFL-poppins.txt).
