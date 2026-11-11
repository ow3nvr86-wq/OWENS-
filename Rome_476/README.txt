ROME NEVER FELL IN 476
A 32-second vertical Short in 2D historical documentary animation, made entirely with code
==========================================================================================

1080 x 1920 (9:16), 30 fps, 32.0 s, H.264 + AAC, -14 LUFS. Loops: the last frame matches the first.
Narration: Kokoro-82M am_michael (Apache-2.0) at 1.19x. Real maps: Natural Earth coastlines; the Roman Empire of AD 117
and the Roman roads from the Ancient World Mapping Center (ODbL).

FILES
  final_video.mp4                   the Short
  renders/final_video_no_voice.mp4  music and effects only, no narration or captions
  script.txt, storyboard.txt, sources.txt, sound_design.txt, subtitles.srt, scene_timing.json
  render.py      timeline, the shatter and ink-bleed transitions, finishing, titles, captions, encode
  audio.py       synthesised war drums, drones, brass, choir and every effect on its word; ducking; -14 LUFS
  src/rome.py    the scenes; src/figs.py the legionary, Trajan, soldiers, legion icons, Constantinople
  src/mapdata.py real map data: projection, AD 117 and AD 395 extents, the West/East line of 395, roads
  src/text.py    word-by-word captions, title slams, map labels; src/core.py, src/post.py the 2D engine
  tools/voiceover.py  narration; tools/words.py word timings (offline speech recogniser); tools/timing.py builds
                      scene_timing.json and the captions from the word timings
  assets/map/    ne_50m_land.geojson, roman_empire_ce_117_extent.geojson, roads.geojson, AWMC_LICENSE.txt
  assets/fonts/  Cinzel, IM Fell English SC, Anton (SIL OFL)

RUN
  $KOKORO_PY tools/voiceover.py               # audio/narration.wav, build/vo_lines.json
  <python with faster-whisper> -I tools/words.py   # build/words.json (word timings)
  python3 tools/timing.py                     # scene_timing.json, build/vo_timing.json, subtitles.srt
  $SHORTS_PY audio.py                         # mixes and sound_design.txt
  $SHORTS_PY render.py --stills 1.5,6,12,20   # look-dev stills
  $SHORTS_PY render.py                        # final_video.mp4 (about 5-8 minutes on 4 cores)
  $SHORTS_PY render.py --no-voice             # renders/final_video_no_voice.mp4
Requirements: Python 3 with numpy, scipy, pillow, pycairo, shapely; ffmpeg; kokoro-onnx; faster-whisper (word timing).

QC (on the final MP4): duration, size and frame rate; loudness; a frame contact sheet; the narration transcribed back
by the speech recogniser; the first and last frames compared for the loop.

LICENCES
- Code, illustrations, music and sound: made for this repository. Narration voice: Kokoro-82M (Apache-2.0).
- Map data: Natural Earth (public domain); AWMC geodata (ODbL 1.0, see assets/map/AWMC_LICENSE.txt).
- Fonts: SIL Open Font License (assets/fonts/OFL-*.txt).
