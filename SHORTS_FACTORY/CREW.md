# The crew

Four agents make each episode. Their definitions are in `.claude/agents/`. They work in this order, and each one
hands a finished set of files to the next.

| Order | Agent | Owns | Hands over |
|---|---|---|---|
| 1 | `script-writer` | Research, the story, `narration.txt`, `sources.txt`, the shot list | A script with every fact checked, plus a beat list with a cue word for each shot |
| 2 | `camera-man` | The backgrounds (`backgrounds/*.png`, `_fg.png`) and the camera block of every scene in `script.json` | Locations rendered, and each shot framed with its move, focus and transition |
| 3 | `animator` | The cast, characters, crowds, effects and poses in `script.json`, plus the engine (`engine/*.js`) and the frame render | Every frame rendered, with test stills checked |
| 4 | `editor` | Voice, alignment, music and sound effects, mastering, `final.mp4`, the thumbnail, QC and delivery | The finished Short, committed and pushed, plus a description |

The voice has to exist before any timing work. When the user records their own `voice.wav`, it comes after the
script and before the camera man. The editor runs `tools/voice.py` and `tools/align.py` as soon as the script is
locked, and runs the sound and finishing steps at the end.

## Rules every crew member follows

- **Spec:** 9:16, 1080x1920, 30 fps, H.264 + AAC, under 100 MB, about -14 LUFS.
- **Truth:** check every fact in 2+ credible sources. Never present speculation as fact. Never invent quotes, documents or statistics.
- **People:** use stylised original characters only. Never use a real victim's likeness, and never copy an existing show's characters.
- **Narrator:** the user's `voice.wav` when they supply one. Otherwise Kokoro `bm_george`.
- **Look-dev first:** check test stills on a contact sheet before any long render.
- **Rendering:** run long renders as tracked background tasks. Never run two renders, or a render and an edit, at the same time.
- **Git:** commit and push after each finished stage, to the session's branch. Use no AI model names in any repo file.
- **Sound:** sound is only checked by loudness and timing, because nobody on the crew can listen to audio. Say so when delivering.
