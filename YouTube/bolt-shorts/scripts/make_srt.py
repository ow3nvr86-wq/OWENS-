#!/usr/bin/env python3
"""Build the SRT subtitle file and the narration script from src/captions/narration-cues.json."""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cues = json.load(open(os.path.join(ROOT, "src/captions/narration-cues.json")))

def ts(s):
    ms = int(round(s * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"

chunks = [c for line in cues["lines"] for c in line["chunks"]]
out = []
for i, c in enumerate(chunks):
    nxt = chunks[i + 1]["start"] if i + 1 < len(chunks) else 32.0
    end = min(c["end"] + 0.35, nxt, 32.0)  # same linger rule as the on-screen captions
    out.append(f"{i + 1}\n{ts(c['start'])} --> {ts(end)}\n{c['text'].replace('*', '')}\n")
os.makedirs(os.path.join(ROOT, "deliverables"), exist_ok=True)
open(os.path.join(ROOT, "deliverables/bolt_001_100k_challenge.srt"), "w").write("\n".join(out))

md = ["# BOLT #001 — Narration Script & Voice-Over Cues", "",
      f"**Voice:** {cues['voice']}", "",
      "**Status:** No text-to-speech provider is configured in this project, so **no narration audio was generated**. "
      "The video ships with music, SFX and burned-in captions; the voice-over slot is ready (see *Integration* below).", "",
      "| # | Scene | Start | End | Line | Delivery |", "|---|---|---|---|---|---|"]
for l in cues["lines"]:
    md.append(f"| {l['id']} | {l['scene']} | {l['start']:.2f}s | {l['end']:.2f}s | {l['text']} | {l['delivery']} |")
md += ["", "## Phrase-level cues (caption sync points)", "", "| Start | End | Phrase |", "|---|---|---|"]
for c in chunks:
    md.append(f"| {c['start']:.2f} | {c['end']:.2f} | {c['text'].replace('*', '**')} |")
md += ["", "Words in **bold** are highlighted yellow on screen.", "",
       "## Integration", "",
       "1. Record or generate the six lines, timed to the cues above, as one 32.0 s file starting at 0:00.",
       "2. Save it as `public/audio/narration/narration.wav`.",
       "3. In `src/audio/narration/config.ts` set `NARRATION_FILE = \"audio/narration/narration.wav\"`.",
       "4. Re-render: `npx remotion render MainVideo out/bolt_001_100k_challenge.mp4`. Music ducks to ~42% under each line automatically.",
       "5. If the real read drifts from these timings, edit `src/captions/narration-cues.json` (captions + SRT follow it) and re-run `python3 scripts/make_srt.py`.", ""]
open(os.path.join(ROOT, "deliverables/narration_script.md"), "w").write("\n".join(md))
print(f"{len(chunks)} subtitle cues written")
