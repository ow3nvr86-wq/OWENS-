#!/bin/bash
# Resumable full render in chunks (existing frames are skipped).
#   ./render_all.sh [final|preview] [A] [B]
# final   -> renders/frames/          (540x960; upscaled 2x in the edit)
# preview -> renders/preview_frames/  (270x480, 4 samples)
set -u
cd "$(dirname "$0")"
Q=${1:-final}
A=${2:-1}
B=${3:-1782}
OUT=renders/frames
[ "$Q" = preview ] && OUT=renders/preview_frames
BL=${BLENDER:-/opt/shorts/blender-4.2.3-linux-x64/blender}
mkdir -p "$OUT"
# a frame cut off by an interrupted render (no PNG end marker) is deleted so it gets rendered again
last=$(ls "$OUT"/f_*.png 2>/dev/null | tail -1)
if [ -n "$last" ] && ! tail -c 12 "$last" | grep -q IEND; then echo "removing partial $last"; rm -f "$last"; fi
for ((s=A; s<=B; s+=200)); do
  e=$((s+199)); [ $e -gt $B ] && e=$B
  echo "=== chunk $s-$e $(date +%T)"
  "$BL" -b --factory-startup -P animation.py -- --quality "$Q" --frames "$s-$e" --out "$OUT" 2>&1 | grep -E "^Time|rendering shot|Error|Traceback"
done
echo "=== ALL DONE $(date +%T)"
