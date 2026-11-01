# Sound effects and music: The Zodiac Killer

Everything below is **synthesised by code** in `animation.py --stage audio` (numpy only: filtered noise, sine
partials, envelopes, convolution reverb). No samples, no recordings, no stock sound. The narration is a synthetic
voice (Kokoro-82M, voice `bm_george`) made by `tools/voiceover.py`; music and ambience duck under it.

Files: `audio/mix_with_voice.wav` (final mix, -14 LUFS), `audio/mix_no_voice.wav` (music + SFX only, for a
voice recorded in CapCut), `audio/narration.wav` (voice only).

## Cue sheet (generated)

| Time (s) | Layer | Cue |
|---|---|---|
|   0.00 | music | Dark drone pad in B-flat minor; it drops out for a beat before the 2020 decode |
|   0.00 | ambience | Night city: low wind and a distant traffic rumble (out when we go inside) |
|   0.15 | voice | NARRATION: "One of America's most mysterious killers sent coded messages to newspapers, challenged police, and disappeared without ever being conclusively identified." (to 9.89 s) |
|   0.40 | ambience | A foghorn out on the bay (two-tone, far away) |
|   0.90 | music | Sparse piano-like notes over the hook; reprised for the investigation and the ending |
|   1.80 | ambience | A distant police siren somewhere across the city |
|   3.60 | music | Noise riser into 5.68 s |
|   5.70 | music | Deep impact on the title THE ZODIAC KILLER |
|   6.30 | ambience | A foghorn out on the bay (two-tone, far away) |
|   9.15 | sfx | Footsteps on wet pavement, echoing, as the figure walks off |
|  10.15 | voice | NARRATION: "Northern California, the late 1960s." (to 12.90 s) |
|  13.10 | voice | NARRATION: "In 1968 and '69, five people were killed. Two more survived." (to 17.87 s) |
|  13.60 | sfx | Police car rolling past on wet asphalt: engine and tyre hiss swell as it passes the camera |
|  17.95 | sfx | Clock ticking (1 per second) whenever we are in the investigation room |
|  17.95 | music | Low hit on the cut into the investigation room |
|  17.95 | music | Low muted pulse (eighth notes, 92 bpm) building through the letters and ciphers |
|  17.95 | ambience | Room tone: the hum of the desk lamp, air, distant street through the window |
|  18.10 | voice | NARRATION: "Then came the letters, from someone calling himself the Zodiac." (to 21.70 s) |
|  18.25 | sfx | Typewriter keys (a short burst) |
|  18.90 | sfx | A letter slides across the desk (paper on wood) |
|  21.90 | voice | NARRATION: "They were signed with a strange crossed-circle symbol. And some were written in code." (to 26.74 s) |
|  26.95 | voice | NARRATION: "A schoolteacher and his wife cracked the first cipher within a week. It gave no name." (to 31.68 s) |
|  27.10 | sfx | Three sheets of paper slide together |
|  28.60 | sfx | Typewriter keys (a short burst) |
|  31.85 | voice | NARRATION: "But a second cipher, 340 symbols long, stayed unsolved for 51 years, until codebreakers cracked it in 2020." (to 40.32 s) |
|  31.85 | sfx | Soft paper clicks as the cipher tiles land; a rippling run of flips at the decode |
|  35.50 | music | Noise riser into 37.64 s |
|  37.70 | music | Impact as the 340 cipher flips to its solution (after a beat of silence) |
|  40.50 | voice | NARRATION: "It mocked the police, but revealed nothing about who wrote it." (to 43.70 s) |
|  41.00 | music | Low hit with the NO NAME stamp |
|  41.00 | sfx | Rubber stamp thump: NO NAME |
|  43.95 | voice | NARRATION: "Detectives compared handwriting, fingerprints, and later DNA. Suspects were investigated. No one was ever charged." (to 51.52 s) |
|  51.75 | voice | NARRATION: "Decades later, the Zodiac Killer's identity remains unknown. And one of America's most infamous mysteries is still unsolved." (to 59.75 s) |
|  52.60 | sfx | The lights go out one by one: switch clicks, the desk lamp buzzes and dies |
|  53.60 | music | Noise riser into 55.28 s |
|  55.30 | music | Final impact on IDENTITY UNKNOWN |

## If you re-do the sound in an editor (suggestions)

- **Typewriter keys**: short bursts in the investigation room (18 s) and when the 408 solution is typed (28.6 s).
- **Paper movement**: the letter sliding across the desk (18.9 s), the three cipher parts sliding together (27.1 s).
- **Distant police sirens** in the hook (from 1.8 s), far away and wet with reverb; the police car itself passes silently with its red light (13.6-18 s).
- **Low cinematic rumbling / drone** under everything, swelling into the 2020 decode and the ending.
- **Clock ticking** whenever we are inside the investigation room; let it be the last thing heard as the lights go out.
- **Atmospheric suspense music**: a dark minor drone and a low pulse that tightens through the cipher section.
- **Dramatic pauses**: drop everything for ~0.3 s before the 340 cipher flips to its solution (37.7 s), and let the final line land over near-silence.
- Keep the narration about 10-15 dB above everything else; YouTube Shorts plays back at about -14 LUFS.
