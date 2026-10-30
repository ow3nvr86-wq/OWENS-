#!/bin/bash
# SessionStart hook for Claude Code cloud sessions: installs the toolchain used to make the
# code-generated 3D YouTube Shorts (see youtube_short_molasses/README.md).
#   - Blender 4.2 LTS (headless rendering with Cycles)     -> $BLENDER
#   - Python venv with numpy/scipy/pillow/piper-tts       -> $SHORTS_PY
#   - Piper voices cleared for commercial use              -> $PIPER_VOICES
#   - Kokoro-82M TTS (Apache-2.0, more natural narration)  -> $KOKORO_PY, $KOKORO_DIR
# Idempotent: every step is skipped when its result is already present.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

TOOLS=/opt/shorts
BLENDER_VER=4.2.3
BLENDER_DIR="$TOOLS/blender-$BLENDER_VER-linux-x64"
VENV="$TOOLS/venv"
VOICES="$TOOLS/piper-voices"
REQS="$CLAUDE_PROJECT_DIR/youtube_short_molasses/requirements.txt"
mkdir -p "$TOOLS" "$VOICES"

# Blender (Cycles CPU rendering works headless; libegl1 is only needed for EEVEE)
if [ ! -x "$BLENDER_DIR/blender" ]; then
  echo "Installing Blender $BLENDER_VER..." >&2
  curl -sSfL "https://download.blender.org/release/Blender4.2/blender-$BLENDER_VER-linux-x64.tar.xz" \
    | tar -xJ -C "$TOOLS"
fi

# Python tools
if [ ! -x "$VENV/bin/python" ]; then
  python3 -m venv "$VENV"
fi
"$VENV/bin/pip" install -q --disable-pip-version-check -r "$REQS"

# Narrator voices: all trained on public-domain or CC0 data (safe for monetised videos).
# Avoid en_US-ryan (CC BY-NC-SA dataset).
fetch_voice() {  # $1 = locale/name/quality, e.g. en_US/joe/medium
  local loc name q file
  IFS=/ read -r loc name q <<< "$1"
  file="${loc}-${name}-${q}"
  for ext in onnx onnx.json; do
    if [ ! -s "$VOICES/$file.$ext" ]; then
      curl -sSfL -o "$VOICES/$file.$ext.part" \
        "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/$loc/$name/$q/$file.$ext"
      mv "$VOICES/$file.$ext.part" "$VOICES/$file.$ext"
    fi
  done
}
for v in en_US/ljspeech/high en_US/joe/medium en_US/bryce/medium en_US/john/medium en_US/norman/medium; do
  fetch_voice "$v"
done

# Kokoro-82M (Apache-2.0): a more natural-sounding narrator than Piper. Separate venv so its
# dependencies can't disturb the main one. Default Dyatlov Pass narrator: bm_george.
KVENV="$TOOLS/kokoro-venv"
KDIR="$TOOLS/kokoro"
mkdir -p "$KDIR"
if [ ! -x "$KVENV/bin/python" ]; then
  python3 -m venv "$KVENV"
fi
"$KVENV/bin/pip" install -q --disable-pip-version-check kokoro-onnx==0.6.1 soundfile
for f in kokoro-v1.0.onnx voices-v1.0.bin; do
  if [ ! -s "$KDIR/$f" ]; then
    curl -sSfL -o "$KDIR/$f.part" \
      "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/$f"
    mv "$KDIR/$f.part" "$KDIR/$f"
  fi
done

{
  echo "export BLENDER=\"$BLENDER_DIR/blender\""
  echo "export SHORTS_PY=\"$VENV/bin/python\""
  echo "export PIPER_VOICES=\"$VOICES\""
  echo "export KOKORO_PY=\"$KVENV/bin/python\""
  echo "export KOKORO_DIR=\"$KDIR\""
} >> "$CLAUDE_ENV_FILE"
