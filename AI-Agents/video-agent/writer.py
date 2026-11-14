"""The scriptwriter: ChatGPT (OpenAI API) writes each video script.

It keeps one running conversation, saved to disk, so GPT remembers every
video it has already written and every report Claude sent back. That's how
the series stays varied and how GPT knows when to write the next one.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from openai import OpenAI

GPT_MODEL = os.environ.get("GPT_MODEL", "gpt-5.5")
KEEP_MESSAGES = 30  # older history is dropped to keep requests small

INSTRUCTIONS = """You are the scriptwriter for a series of short vertical videos (TikTok, Reels, YouTube Shorts).

The series brief:
{brief}

Each time you are asked, write ONE new video script:
- A title on the first line, starting with "Title:".
- Then the voiceover, split into 4 to 8 short beats, one per line, each starting with "Beat N:".
- About 30 to 60 seconds of speech in total. Open with a hook in the first beat; end with a clear call to action.
- Write for the ear: short sentences, no stage directions, no emoji, no hashtags.

After each video is made, the video producer (Claude) will report back with what was made and notes for you. Use those notes, and never repeat a topic or hook you've already used."""


class ScriptWriter:
    def __init__(self, brief: str, state_path: Path):
        self.client = OpenAI()  # reads OPENAI_API_KEY
        self.brief = brief
        self.state_path = state_path
        self.history: list[dict] = []
        self.videos_done = 0
        if state_path.exists():
            state = json.loads(state_path.read_text())
            self.history = state.get("history", [])
            self.videos_done = state.get("videos_done", 0)

    def _save(self) -> None:
        self.state_path.write_text(json.dumps(
            {"brief": self.brief, "videos_done": self.videos_done, "history": self.history[-KEEP_MESSAGES:]},
            indent=2,
        ))

    def next_script(self) -> str:
        """Ask GPT for the next script and return it."""
        n = self.videos_done + 1
        if not self.history or self.history[-1]["role"] != "user":
            self.history.append({"role": "user", "content": f"Write the script for video #{n}."})
        # The history must start with a user turn after trimming.
        recent = self.history[-KEEP_MESSAGES:]
        while recent and recent[0]["role"] != "user":
            recent = recent[1:]
        response = self.client.responses.create(
            model=GPT_MODEL,
            instructions=INSTRUCTIONS.format(brief=self.brief),
            input=recent,
        )
        script = (response.output_text or "").strip()
        if not script:
            raise RuntimeError("ChatGPT returned an empty script.")
        self.history.append({"role": "assistant", "content": script})
        self._save()
        return script

    def report_done(self, report: str) -> None:
        """Claude's hand-off: tell GPT the video is finished and ask for the next script."""
        self.videos_done += 1
        self.history.append({
            "role": "user",
            "content": f"{report}\n\nWhen you're ready, write the script for video #{self.videos_done + 1}.",
        })
        self._save()
