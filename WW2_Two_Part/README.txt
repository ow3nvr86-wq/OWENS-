WORLD WAR II IN TWO PARTS
Two vertical Shorts in clean 2D motion graphics over real maps, made entirely with code
========================================================================================
Part 1: How Hitler Took Europe (1939-1941)    part1/final_video.mp4   1080x1920, 30 fps, 37.5 s, -14 LUFS
Part 2: How It All Fell Apart (1942-1945)     part2/final_video.mp4   1080x1920, 30 fps, 38.5 s, -14 LUFS

Each part is ONE CONTINUOUS SHOT over the map: the camera never cuts. It flies between the places in the story,
territory floods with colour as it is taken, arrows and armour move with the words, and whip-pans (with motion blur
from the camera's own speed) carry it between fronts.

VOICEOVER
The narration is the supplied recording (partN/voiceover/). tools/voice_prep.py only shortens pauses longer than
0.4 s and sets the level. tools/words.py then times every word with an offline speech recogniser, corrected against
the pauses in the audio, and tools/timing_p1.py places every camera move, flood, arrow, title, caption and sound on
the word it belongs to.

Part 1 uses the supplied recording. No recording arrived for Part 2, so it is narrated by the channel's narrator
George (Kokoro-82M bm_george, Apache-2.0; tools/george_vo.py) and then goes through exactly the same steps; a supplied
recording dropped into part2/voiceover/ would replace it.

THE MAP
Coastlines and countries: Natural Earth 1:50m (public domain). The borders of September 1939 are built from them by
tools/build_map.py with historical lines drawn by hand from the positions of border towns: Germany of 1939 (with
Austria, the Czech lands, East Prussia, Danzig and its eastern territories), Poland's 1921 borders, the German-Soviet
line of 28 Sept 1939, the Vichy demarcation line of June 1940, and the front line of early December 1941. They are
approximate (to about 20-30 km), which is finer than a phone screen shows.
Colours: red = Germany and the territory it occupied; dark red with stripes = Axis allies and Vichy France;
blue = Britain and France at war with Germany; slate = everyone else.

FILES
  script_part1.txt, script_part2.txt, sources.txt
  part1/final_video.mp4, part1/final_video_no_voice.mp4, part1/sound_design.txt, part1/subtitles.srt,
  part1/scene_timing.json, part1/captions.txt, part1/voiceover/ (the supplied recording), part1/audio/
  part2/ (the same set of files for Part 2)
  render.py, audio.py, src/part1.py and src/part2.py (the shots), src/common.py, src/mapdata.py, src/text.py, src/core.py, src/post.py
  tools/build_map.py, tools/voice_prep.py, tools/words.py, tools/timing_p1.py, tools/timing_p2.py, tools/george_vo.py
  assets/map/ww2_map.json, assets/fonts/ (Inter, Anton; SIL OFL)

RUN
  $SHORTS_PY tools/voice_prep.py part1
  <python with faster-whisper> -I tools/words.py part1
  python3 tools/timing_p1.py
  $SHORTS_PY audio.py part1
  $SHORTS_PY render.py part1 [--stills 1,9,20 | --no-voice]
Requirements: Python 3 with numpy, scipy, pillow, pycairo (shapely only to rebuild the map); ffmpeg.

PART 2 ON THE MAP
- Hitler's Europe at its peak (November 1942): the front on the Don, at Stalingrad and in the Caucasus.
- Stalingrad: the Soviet pincers of Operation Uranus (19-23 Nov 1942) meet at Kalach behind the German 6th Army,
  which surrenders on 31 Jan - 2 Feb 1943.
- The Pacific: the limit of Japan's conquests in 1942 (dashed) and the two American drives (central and south-west).
- D-Day: the five beaches (Utah, Omaha, Gold, Juno, Sword), snapped to the map's coastline.
- The fronts closing on Germany are schematic: a beachhead growing from Normandy, the advance up Italy, and the Soviet
  front sweeping in from the east; liberated or Allied-held ground is shown in blue.
- Hiroshima (6 Aug) and Nagasaki (9 Aug) are shown only as a flash and a widening ring.
- The last image: 85 dots, one for each million of the estimated 70-85 million dead (70 solid, 15 outlined).

ACCURACY NOTES
- Every narrated claim is sourced in sources.txt.
- On-screen additions: Britain and France declared war on 3 Sept 1939; France's campaign ran 10 May - 22 June 1940;
  Barbarossa began 22 June 1941; Pearl Harbor, 7 Dec 1941.
- The opening "two years later" map shows December 1941. Eastern Poland is shown passing to the USSR in 1939.
- Arrows are schematic (army-group directions), not unit movements. The carrier route to Hawaii is approximate.
