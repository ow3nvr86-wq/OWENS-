#!/bin/bash
# Resumable full render of all 3D frames (existing frames are skipped). Usage: ./render_all.sh [A B]
cd "$(dirname "$0")"
A=${1:-1}; B=${2:-1590}; STEP=200
BLENDER=${BLENDER:-blender}
for ((s=A; s<=B; s+=STEP)); do
  e=$((s+STEP-1)); [ $e -gt $B ] && e=$B
  echo "=== chunk $s-$e $(date +%T)"
  "$BLENDER" -b --factory-startup -P animation.py -- --quality final --frames $s-$e 2>&1 | grep -E "^Time|rendering shot|Error|Traceback"
done
echo "=== ALL DONE $(date +%T)"
