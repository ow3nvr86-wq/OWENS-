#!/usr/bin/env bash
# Render the whole animation in chunks (resumable: existing frames are skipped).
# Usage: BLENDER=/path/to/blender scripts/render_all.sh [first] [last]
set -euo pipefail
cd "$(dirname "$0")/.."
BLENDER=${BLENDER:-blender}
FIRST=${1:-1}
LAST=${2:-1710}
"$BLENDER" -b --factory-startup -P scripts/animation.py -- --quality final --frames "$FIRST-$LAST" --out renders/frames
