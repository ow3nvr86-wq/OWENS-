WHAT IF YOU WERE TRAPPED IN MINECRAFT? - a 60 fps cartoon Short in the style of "The War Lost to Birds"

final_video.mp4                   1080x1920, 60 fps, 42.0 s, H.264 (CRF 18, 10 Mbps cap) + AAC 192k, 31 MB,
                                  -14.6 LUFS, true peak -1.2 dBFS; word-by-word captions + the item counter burned in
renders/final_video_no_voice.mp4  music + SFX only, no captions (-14.7 LUFS)
QA: ffprobe ok, no frozen spans >= 0.4 s, no black frames (the last word is followed by a deliberate cut to black
in the final 0.08 s), captions built from the narration's own word times (50 chunks; 64 / 150 / 10 as digits).

HOW IT WAS MADE
  narration  the user's ElevenLabs recording (audio/vo.mp3), unchanged; word times: work/words.json
  engine     web/ = the cartoon engine from CARTOON_THE_WAR_LOST_TO_BIRDS (three.js toon shading, ink outlines,
             depth of field, canvas-drawn bean-head cards), now driven in seconds at 60 fps (web/story.js)
  world      web/world.js: original 16x16 pixel textures (grass, dirt, stone, log, leaves, planks, cobble, wool),
             1 m blocks; the tree whose logs pop out (the leafy top stays floating), the mountain with mineable
             blocks, the house that is slapped together block by block, the bedroom with the one missing block,
             the 150-tonne weight, the update notes. Characters: an original player and an original glowing-eyed
             'Herobrine' card - no Mojang art, characters, textures, logos or music.
  smoothness 60 fps; eased moves, squash-and-pop on blocks and the door, blinks hide expression changes, walks are
             paced to the stride, calm camera drift. (Sub-frame motion blur was left out: at ~2.5 s per 3D frame it
             would have quadrupled a 1.8-hour render.)
  captions   tools/captions.py (Anton, uppercase, white with black outline, active word amber; the stone item
             counter top-right while mining)
  sound      audio.py (synthesised playful score -> tense sunset -> music box -> silence on the eyes -> sting;
             ~60 cartoon SFX on the action beats), music ducked under the voice, SFX ~0.38 of the voice.
             finish.sh masters and encodes (the main mix used a 0.66 limiter ceiling to land at -14.6 LUFS / -1.2 dBTP).
  Claude cannot listen to audio: the sound was checked by levels, loudness and timing only.

RUN IT
  SCALE=0.5 node render.mjs build/stills "0,600,1200,2200" && python3 sheet.py build/stills build/sheet.jpg
  RESUME=1 node render.mjs frames "0-2521"                   # ~1.8 h on 4 cores; resumable
  $SHORTS_PY audio.py && $SHORTS_PY tools/captions.py frames build/frames_cap && bash finish.sh

RENDER TIMES: full render ~1 h 50 min (in two runs - the container restarted at frame 1,644 and the render resumed);
  one second re-rendered after QA (67 frames, 2.6 min); captions 1 min 45 s; encode ~3 min.

stick_figure_version/ holds the earlier stick-figure attempt (not used).
