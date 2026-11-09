ELON MUSK: ONE CONTINUOUS JOURNEY
A 32-second vertical Short in modern 2D motion graphics, made entirely with code: ONE CONTINUOUS SHOT, NO CUTS
==============================================================================================================

1080 x 1920 (9:16), 30 fps, 32.0 s, H.264 + AAC, -14 LUFS. Narration: Kokoro am_michael (a
modern, young American male voice), every line at his natural pace; captions and the hook icons are timed from
the speech onsets measured in the narration audio (tools/voiceover.py writes them into scene_timing.json).
Pronunciation: kokoro-onnx feeds the voice raw eSpeak phonemes, which are partly British (no 'r' in learned, Earth,
person, world's) and split the diphthongs; tools/voiceover.py converts them to the American phoneme set the voice was
trained on, says 'Elon' as EE-lon, and keeps the soft first sound of each line. Checked with an offline speech
recogniser (faster-whisper small.en): every word of every line is recognised.

HOW THE ONE SHOT IS BUILT (src/journey.py)
- The timeline has a single entry; render.py makes no transitions between clips.
- Space A is one plane: the portrait, the interface ring, the payment streams and the city road. The ring unspools
  into the streams, the streams straighten into the lane markings, and the camera travels through it all.
- A -> B: the camera dives into the car's headlight; for a few frames its light fills the frame edge to edge, and the
  camera pulls back out of the rocket's engine light. Measured on the final video, the frame-to-frame change at the
  hand-over itself is below the median motion of the film.
- B -> C: the camera pushes into one satellite, and the network grows out of its point.
- C -> D: the network's nodes fold onto the globe.
- QC: tools in the session measured every frame-to-frame difference of the final MP4; the only large values are the
  deliberate half-second light swell of the dive (no frame-to-frame jump anywhere).

FILES
  final_video.mp4, renders/final_video_no_voice.mp4, renders/preview.mp4
  script.txt (narration and the three hooks; A chosen), storyboard.txt, sources.txt, sound_design.txt, subtitles.srt
  render.py, audio.py, src/journey.py (the one shot), src/portrait.py (the illustrated portrait), src/gfx.py, src/text.py,
  src/post.py, src/core.py, tools/voiceover.py, tools/export_assets.py, assets/ (fonts, illustration sheets)

RUN
  $KOKORO_PY tools/voiceover.py ; $SHORTS_PY audio.py ; $SHORTS_PY render.py --preview ; $SHORTS_PY render.py
  $SHORTS_PY render.py --no-voice ; $SHORTS_PY tools/export_assets.py
