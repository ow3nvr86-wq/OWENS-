#!/usr/bin/env bash
# One command from script to finished Short:  ./make_episode.sh episodes/<name>
# Needs in the episode folder: narration.txt, script.json, backgrounds/*.png  (voice.wav optional: Kokoro TTS if missing)
set -euo pipefail
EP="${1:?usage: ./make_episode.sh episodes/<name>}"; cd "$(dirname "$0")"
KOKORO_PY="${KOKORO_PY:-/opt/shorts/kokoro-venv/bin/python}"; SHORTS_PY="${SHORTS_PY:-/opt/shorts/venv/bin/python}"
WHISPER_PY="${WHISPER_PY:-/opt/shorts/chatterbox-venv/bin/python}"
echo "1/5 voice";      "$KOKORO_PY" tools/voice.py "$EP"
echo "2/5 alignment";  "$WHISPER_PY" tools/align.py "$EP"
echo "3/5 frames";     RESUME="${RESUME:-0}" node tools/render.mjs "$EP" all
echo "4/5 sound";      "$SHORTS_PY" tools/audio.py "$EP"
echo "5/5 finish";     "$SHORTS_PY" tools/finish.py "$EP"
echo "done: $EP/final.mp4 and $EP/thumbnail.png"
