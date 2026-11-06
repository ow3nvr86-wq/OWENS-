#!/usr/bin/env bash
# Final FFmpeg mastering pass for YouTube Shorts:
#  - limited-range yuv420p H.264 (Remotion's JPEG frames come out full-range)
#  - audio peak-limited to -1.5 dBFS (Remotion's mix can touch 0 dBFS)
#  - hard trim of BOTH streams to exactly 32.000 s (AAC padding otherwise adds ~21 ms)
set -euo pipefail
IN=${1:-out/bolt_001_100k_challenge.mp4}
OUT=${2:-deliverables/bolt_001_100k_challenge.mp4}
mkdir -p "$(dirname "$OUT")"
ffmpeg -y -v error -i "$IN" \
  -vf "scale=in_range=full:out_range=tv,format=yuv420p" \
  -c:v libx264 -preset slow -crf 19 -profile:v high -level 4.2 -r 30 -g 30 \
  -color_range tv -colorspace bt709 -color_primaries bt709 -color_trc bt709 \
  -af "volume=-0.5dB,alimiter=limit=0.84:attack=3:release=60:level=disabled,atrim=0:32,asetpts=PTS-STARTPTS" \
  -c:a aac -b:a 192k -ar 48000 \
  -t 32 -movflags +faststart "$OUT"
# Extract the audio mix as a standalone WAV as well (music + SFX, no narration)
ffmpeg -y -v error -i "$OUT" -vn -c:a pcm_s16le -t 32 "${OUT%.mp4}_audio_mix.wav"
echo "mastered -> $OUT"
