# Sleep videos

Ambient sleep videos for YouTube (1920x1080, 24 fps), generated entirely in
code: no stock footage, no licensed audio, so there are no copyright claims.

## Rainy Night

A lake at night in light rain. A low moon behind drifting, moonlit clouds,
faint twinkling stars, misty mountains, a pine shoreline and a small cabin
with a warm, flickering window and chimney smoke. The lake mirrors it all
with gentle ripples, a shimmering moon path and rings where the rain lands.
The audio is synthesized rain: a low brown-noise rumble, a pink-noise rain
body that slowly swells, a fine distant hiss and three kinds of droplets.

```bash
python3 rainy_night.py still 300     # quick preview of one frame
python3 rainy_night.py loop          # render the 60 s seamless loop
python3 rainy_night.py extend 2m     # test: loop it to 2 minutes
python3 rainy_night.py extend 1h     # 1 hour
python3 rainy_night.py extend 10h    # a full night
```

`extend` doesn't re-render. It copies the video stream and re-loops the
audio from the WAV, so a 10-hour file takes minutes. Long versions get a
10 s fade-in and a 30 s fade-out.

Files land in `output/` (git-ignored, videos are large).

### Why it loops without a seam
- Audio is built in the frequency domain over exactly one loop length, so the
  waveform is periodic. Droplets are placed with circular convolution.
- Every slow swell is a sine with a whole number of cycles per loop.
- Clouds, mist, smoke and water waves are tileable noise that moves exactly
  a whole number of tiles per loop; stars twinkle and the window flickers at
  whole-number rates; rain rings are born on a clock that wraps.
- Rain scrolls a whole number of screen heights per loop.

Requires: python3, numpy, Pillow, ffmpeg.
