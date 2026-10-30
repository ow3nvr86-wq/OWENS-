# Sound effects and music: Centralia

Everything below is **synthesised by code** in `animation.py --stage audio` (numpy only: filtered noise, sine
partials, envelopes, convolution reverb). No samples, no recordings, no stock sound. The narration is a synthetic
voice (Kokoro-82M, voice `bm_george`) made by `tools/voiceover.py`; music and ambience duck under it.

Files: `audio/mix_with_voice.wav` (final mix, -14 LUFS), `audio/mix_no_voice.wav` (music + SFX only, for a
voice recorded in CapCut), `audio/narration.wav` (voice only).

## Cue sheet (generated)

| Time (s) | Layer | Cue |
|---|---|---|
|   0.00 | music | A-minor drone pad (A1-E2-A2-C3); drops out for the sinkhole collapse and the beat before the title |
|   0.00 | ambience | Night wind bed (stereo, gusting); returns for the 1981 yard, the empty town and the final pull-back |
|   0.10 | voice | NARRATION: "Imagine living in a town where the ground beneath your feet was literally burning." (to 4.87 s) |
|   0.60 | sfx | Asphalt cracking: accelerating creaks over a low ground groan |
|   1.20 | music | Noise riser into 2.88 s |
|   1.60 | sfx | Fire crackle (sparse pops + hiss): the crack, the mine, the dump fire, the tunnel |
|   2.90 | ambience | Deep underground fire roar (brown noise 30-700 Hz): dive, tunnel, section, reveal |
|   2.90 | music | Whoosh-impact: the camera plunges into the burning seam |
|   5.10 | voice | NARRATION: "This is Centralia, Pennsylvania: a coal-mining town of over a thousand people." (to 10.33 s) |
|   5.20 | ambience | Birdsong chirps (1962 town, golden hour) |
|   5.40 | music | Music-box motif (C-E-D-A...) for the living town; reprised with a flattened 4th note over the demolition and the ending |
|   5.60 | ambience | Distant church bell (one toll) over the 1962 town |
|  10.60 | sfx | A 1950s car passes on Locust Avenue |
|  10.60 | voice | NARRATION: "In May 1962, a trash fire in an old mine pit most likely spread into a coal seam below." (to 17.33 s) |
|  14.20 | music | Noise riser into 15.58 s |
|  15.60 | music | Low boom: the fire reaches the coal seam |
|  17.00 | music | Hit on the cut to the cross-section |
|  17.20 | music | Heartbeat pulse (25 beats) while the fire spreads and under the reveal |
|  17.60 | voice | NARRATION: "Old mine tunnels fed it oxygen, and it crept beneath the streets." (to 21.38 s) |
|  21.75 | voice | NARRATION: "Crews dug trenches and flushed the mines. Nothing put it out." (to 25.52 s) |
|  22.00 | sfx | Slurry rushing down the flushing borehole, steam hiss where it meets the fire |
|  24.70 | music | Hit on "Nothing put it out." |
|  25.70 | sfx | Gas: thin high hiss with a slow beating tone |
|  25.80 | voice | NARRATION: "Underground, it reached over a thousand degrees. Toxic gas seeped into homes." (to 30.63 s) |
|  30.95 | voice | NARRATION: "In 1981, the ground opened beneath a twelve-year-old boy. His cousin pulled him out alive." (to 37.15 s) |
|  31.35 | sfx | Dramatic silence (0.25 s), then the ground collapses: rumble + debris; steam hiss from the hole |
|  31.60 | music | Collapse impact: the ground opens (after 0.25 s of silence) |
|  37.50 | voice | NARRATION: "Congress set aside 42 million dollars to move the town. Hundreds of homes were torn down." (to 43.29 s) |
|  38.20 | sfx | Muffled demolition thumps across the time-lapse |
|  43.40 | sfx | Steam hissing from the cracked highway |
|  43.50 | voice | NARRATION: "Today, just five people remain." (to 45.64 s) |
|  45.90 | voice | NARRATION: "From above, you'd barely know. But the fire has spread beyond the town, and could burn for another century." (to 51.86 s) |
|  46.60 | music | Noise riser into 48.58 s |
|  48.60 | music | Deep underground explosion as the camera passes below the surface |
|  53.40 | voice | NARRATION: "A whole town almost disappeared... and beneath it, the fire kept burning." (to 58.18 s) |
|  54.00 | music | Noise riser into 55.55 s |
|  55.60 | music | Final impact on the title |

## If you re-do the sound in an editor (suggestions)

- **Deep atmospheric rumble** under the whole video; let it swell at 0-3 s and when the camera goes underground (2.9 s, 48.6 s).
- **Distant wind** for the night street, the 1981 yard and the empty town.
- **Crackling fire** wherever flames are on screen (the crack, the mine, the dump, the tunnel).
- **Underground explosions / impacts** on the cuts into the ground (2.9 s, 15.6 s, 48.6 s).
- **Cinematic impacts** on "Nothing put it out." (24.7 s), the sinkhole collapse (31.6 s) and the title (55.6 s).
- **Dramatic silence**: a quarter-second of nothing before the sinkhole collapse, and a beat before the title.
- Keep the narration about 10-15 dB above everything else; YouTube Shorts plays back at about -14 LUFS.
