#!/usr/bin/env bash
# Finish: one linear gain to -14 LUFS + a -1 dBFS peak limiter on the whole mix, encode H.264 CRF 17 + AAC,
# then QA (freeze / black / loudness) and a QA contact sheet.   bash finish.sh "The War Lost to Birds"
set -euo pipefail
cd "$(dirname "$0")"
TITLE="${1:-The War Lost to Birds}"
CAPS="${CAPS:-build/frames_cap}"          # captioned frames for the main video (tools/captions.py)
N=$(ls frames/f*.jpg | wc -l)
mkdir -p out renders
lufs() { ffmpeg -nostats -i "$1" -af ebur128 -f null - 2>&1 | awk '/Summary/{s=1} s&&/ I:/{print $2; exit}'; }
master() {   # $1 raw wav -> $2 mastered wav: one linear gain + a -3 dBFS peak limiter (headroom for AAC overshoot);
  local I G I2 k                                                # the gain is refined until the limited mix sits on -14 LUFS
  I=$(lufs "$1"); G=$(python3 -c "print(round(-14.0 - ($I), 2))")
  for k in 1 2 3 4; do
    ffmpeg -v error -y -i "$1" -af "volume=${G}dB,alimiter=limit=0.708:attack=3:release=60:level=false" -ar 48000 -c:a pcm_s24le "$2"
    I2=$(lufs "$2")
    python3 -c "import sys; sys.exit(0 if abs(-14.0 - ($I2)) <= 0.1 else 1)" && break
    G=$(python3 -c "print(round($G + (-14.0 - ($I2)) * 1.15, 2))")
  done
  echo "  $1: $I LUFS -> gain $G dB -> $I2 LUFS"
}
encode() {   # $1 audio -> $2 mp4 [$3 frames dir]
  ffmpeg -v error -y -framerate 30 -i "${3:-frames}/f%04d.jpg" -i "$1" -map 0:v -map 1:a -frames:v "$N" \
    -c:v libx264 -preset slow -crf 17 -maxrate 14M -bufsize 28M -pix_fmt yuv420p -profile:v high -r 30 \
    -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart -metadata title="$TITLE" "$2"
}
echo "mastering"; master audio/mix_raw.wav audio/mix_final.wav; master audio/bed_raw.wav audio/bed_final.wav
echo "encoding $N frames"; if [ -d "$CAPS" ] && [ "$(ls "$CAPS"/f*.jpg | wc -l)" = "$N" ]; then encode audio/mix_final.wav final_video.mp4 "$CAPS"; else encode audio/mix_final.wav final_video.mp4; fi; encode audio/bed_final.wav renders/final_video_no_voice.mp4
echo "QA"
for f in final_video.mp4 renders/final_video_no_voice.mp4; do
  echo "== $f  $(du -h "$f" | cut -f1)"
  ffprobe -v error -show_entries stream=codec_name,width,height,r_frame_rate,nb_frames -show_entries format=duration -of compact "$f"
  ffmpeg -nostats -i "$f" -af ebur128=peak=true -f null - 2>&1 | awk '/Summary/{s=1} s&&(/ I:/||/Peak:/){print "  " $0}'
done
ffmpeg -nostats -i final_video.mp4 -vf "freezedetect=n=-60dB:d=0.4,blackdetect=d=0.1:pix_th=0.05" -an -f null - 2>&1 | grep -E "freeze_|black_" | sed 's/^/  /' || echo "  no frozen spans >= 0.4 s, no black frames"
ffmpeg -v error -y -i final_video.mp4 -vf "select='not(mod(n\,30))',scale=216:384,tile=7x6" -frames:v 1 -vsync 0 out/qa_sheet.jpg
echo "wrote out/qa_sheet.jpg"
