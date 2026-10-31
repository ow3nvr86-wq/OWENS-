# Sound effects and music: Lake Nyos

Everything below is **synthesised by code** in `animation.py --stage audio` (numpy only: filtered noise, sine
partials, envelopes, convolution reverb). No samples, no recordings, no stock sound. The narration is a synthetic
voice (Kokoro-82M, voice `bm_george`) made by `tools/voiceover.py`; music and ambience duck under it.

Files: `audio/mix_with_voice.wav` (final mix, -14 LUFS), `audio/mix_no_voice.wav` (music + SFX only, for a
voice recorded in CapCut), `audio/narration.wav` (voice only).

## Cue sheet (generated)

| Time (s) | Layer | Cue |
|---|---|---|
|   0.00 | music | Cold D-minor drone pad (D2-A2-D3-F3); cut to silence just before the eruption and before the title |
|   0.00 | ambience | Night insects (crickets) in the hook and at the lake |
|   0.00 | ambience | Wind through the mountain valleys (stereo, gusting); out underwater |
|   0.15 | voice | NARRATION: "Imagine an entire village being overcome by an invisible cloud... without anyone knowing what was happening." (to 6.19 s) |
|   6.10 | ambience | Water lapping at the lake |
|   6.35 | voice | NARRATION: "This is Lake Nyos, in northwest Cameroon: a calm crater lake on an old volcano." (to 11.15 s) |
|   6.40 | music | Sparse piano-like motif (D-F-A-G#), reprised over the aftermath and the ending |
|   9.80 | music | Noise riser into 11.18 s |
|  11.20 | music | Plunge: sub-boom as the camera goes under the surface |
|  11.20 | sfx | Splash and bubble rush as the camera goes under |
|  11.20 | ambience | Underwater ambience: muffled deep rumble, slow bubble pops (also seep, column, final) |
|  11.35 | voice | NARRATION: "But two hundred metres down, it was hiding something." (to 14.56 s) |
|  14.60 | sfx | Faint fizzing trickle from the springs on the lake floor |
|  14.75 | voice | NARRATION: "Carbon dioxide from magma seeped into the lake's bottom water." (to 18.51 s) |
|  18.85 | voice | NARRATION: "The weight of the lake kept it dissolved, like a sealed bottle of soda." (to 22.82 s) |
|  23.15 | voice | NARRATION: "Then, on the night of August 21st, 1986, the lake overturned... and the gas burst free." (to 29.64 s) |
|  23.40 | sfx | Deep rumbling and bubbling grows under the lake |
|  24.40 | music | Noise riser into 25.95 s |
|  25.70 | sfx | Dramatic silence (0.3 s), then the burst: roaring column of water and gas, surge crashing on the shore |
|  26.00 | music | Eruption impact: the gas bursts free (after 0.3 s of silence) |
|  29.80 | sfx | A soft, low rushing (the cloud pouring down the valley; the real gas was silent) |
|  29.80 | music | Low hit on the cut to the cloud pouring over the rim |
|  29.95 | voice | NARRATION: "A cloud of carbon dioxide, heavier than air, spilled over the rim and down the valleys." (to 35.52 s) |
|  30.00 | music | Heartbeat under the spreading cloud; it slows and fades once the cloud reaches the village |
|  35.85 | voice | NARRATION: "It pushed the oxygen away. In the villages below, people rapidly lost consciousness. Many never woke up." (to 42.62 s) |
|  37.89 | sfx | Small soft puffs: oil lamps guttering out one by one |
|  37.89 | ambience | The insects fall silent as the cloud reaches the village (no birds or insects were seen for 48 h) |
|  43.00 | music | Soft, deep hit on "About 1,746 people died" |
|  43.15 | voice | NARRATION: "About 1,746 people died, along with thousands of animals." (to 48.24 s) |
|  48.40 | sfx | The degassing fountain: hissing spray falling back on the water |
|  48.55 | voice | NARRATION: "Scientists called it a limnic eruption. Today, pipes vent the gas from the deep." (to 53.06 s) |
|  53.40 | voice | NARRATION: "The most terrifying part? The danger was completely invisible." (to 57.35 s) |
|  55.60 | music | Noise riser into 57.38 s |
|  57.40 | music | Final impact on the title |

## If you re-do the sound in an editor (suggestions)

- **Low cinematic rumbling** under the whole video, swelling as the lake starts to overturn (24-26 s).
- **Wind through mountain valleys** for the village, the lake at night and the empty valley at dawn.
- **Underwater ambience** and **deep water movement** for the dive, the lake floor, the rising column and the ending.
- **Dramatic cinematic impacts** on the plunge (11.2 s), the eruption (26.0 s, after a beat of silence) and the title (57.4 s).
- **Subtle atmospheric music**: a cold minor drone with a sparse piano line; let it drop out completely before the eruption.
- **Silence as a sound effect**: the night insects stop when the cloud reaches the village. The real gas made no sound.
- Keep the narration about 10-15 dB above everything else; YouTube Shorts plays back at about -14 LUFS.
