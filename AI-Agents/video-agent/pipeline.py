#!/usr/bin/env python3
"""ChatGPT writes it, Claude makes it, your phone hears about it.

The loop, for each video:
  1. ChatGPT writes a script.
  2. Claude turns it into a scene-by-scene plan.
  3. The renderer records the voiceover and builds the .mp4.
  4. You get a phone notification.
  5. Claude reports back to ChatGPT ("video done, here are my notes"),
     which is ChatGPT's cue to write the next script.

Run:
    python pipeline.py --brief "wild history facts most people never learned"
    python pipeline.py --count 5 --gap 10    # 5 videos, 10 minutes apart
    python pipeline.py --forever --gap 60    # one an hour until you stop it
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

from director import Director
from notify import notify
from render import render
from writer import ScriptWriter

def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40] or "video"


def make_one(writer: ScriptWriter, director: Director, out_dir: Path, voice: str) -> Path:
    number = writer.videos_done + 1
    print(f"\n━━━ Video #{number} ━━━")

    print("✍️  ChatGPT is writing the script...")
    script = writer.next_script()
    print("   " + script.splitlines()[0])

    print("🎬 Claude is planning the scenes...")
    plan = director.plan(script)
    base = out_dir / f"{number:03d}-{slug(plan.title)}"
    base.with_suffix(".script.txt").write_text(script)
    base.with_suffix(".plan.json").write_text(json.dumps(plan.model_dump(), indent=2))
    print(f"   {plan.title}: {len(plan.scenes)} scenes")

    print("🎙️  Recording and rendering...")
    video = base.with_suffix(".mp4")
    seconds = render(plan, video, voice=voice)
    base.with_suffix(".caption.txt").write_text(plan.caption)

    notify(
        title=f"Video #{number} is ready",
        message=f"{plan.title} ({seconds:.0f}s). Saved as {video.name}",
        tags=["movie_camera", "white_check_mark"],
    )

    print("🤝 Claude is reporting back to ChatGPT for the next script...")
    writer.report_done(Director.handoff(plan, number, seconds, video.name))
    return video


def main() -> None:
    p = argparse.ArgumentParser(description="ChatGPT writes scripts, Claude makes the videos.")
    p.add_argument("--brief", help="what your content is about (asked on first run if missing, then remembered)")
    p.add_argument("--count", type=int, default=1, help="how many videos to make (default 1)")
    p.add_argument("--forever", action="store_true", help="keep making videos until you press Ctrl-C")
    p.add_argument("--gap", type=float, default=0, help="minutes to wait between videos")
    p.add_argument("--voice", default="marin", help="OpenAI voice, e.g. marin, cedar, alloy, nova")
    p.add_argument("--effort", default="high", choices=["low", "medium", "high", "xhigh", "max"],
                   help="how hard Claude thinks about each plan")
    p.add_argument("--out", default="output", help="folder for videos and the series memory")
    p.add_argument("--new-series", action="store_true", help="forget earlier videos and start over")
    args = p.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    state = out_dir / "series.json"
    if args.new_series:
        state.unlink(missing_ok=True)
    saved_brief = json.loads(state.read_text()).get("brief") if state.exists() else None
    brief = args.brief or saved_brief
    if not brief:
        if not sys.stdin.isatty():
            sys.exit('Tell me what your content is about, e.g. --brief "wild history facts".')
        print("What's your content about? Describe the topic, the vibe and who it's for.")
        brief = input("> ").strip()
        if not brief:
            sys.exit("No topic given, so nothing to make.")
    if args.brief and saved_brief and args.brief != saved_brief:
        sys.exit("This folder already holds a series with a different brief. "
                 "Use --new-series to start over, or --out to pick another folder.")

    writer = ScriptWriter(brief, state)
    director = Director(effort=args.effort)
    print(f"Series: {brief}\nVideos so far: {writer.videos_done}")

    made = 0
    try:
        while args.forever or made < args.count:
            make_one(writer, director, out_dir, args.voice)
            made += 1
            if (args.forever or made < args.count) and args.gap > 0:
                print(f"\n⏳ Next video in {args.gap:g} minutes (Ctrl-C to stop).")
                time.sleep(args.gap * 60)
    except KeyboardInterrupt:
        print("\nStopped.")
    except Exception as e:
        notify(title="Video pipeline stopped", message=f"{type(e).__name__}: {e}"[:300],
               tags=["warning"], priority=4)
        raise
    print(f"\nDone. Made {made} video(s) in {out_dir.resolve()}")


if __name__ == "__main__":
    main()
