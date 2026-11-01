"""The director: Claude turns GPT's script into a scene-by-scene video plan,
then writes the hand-off note that tells GPT the video is done.
"""
from __future__ import annotations

import anthropic
from pydantic import BaseModel, Field

MODEL = "claude-opus-5-5"
FALLBACK_BETA = "server-side-fallback-2026-07-01"

SYSTEM = """You are the director and producer of short vertical videos (1080x1920, 30 to 60 seconds).

A scriptwriter sends you a script. Turn it into a scene plan that the rendering code will build:
- One scene per beat of the script, 4 to 10 scenes.
- narration: the exact words the voiceover reads for that scene. Tighten the writer's wording if it helps it flow, but keep the meaning and the call to action.
- headline: the big on-screen text, 2 to 7 words, the key idea of the scene. Never just repeat the narration.
- subtext: an optional smaller line under the headline (up to 12 words), or an empty string.
- background and accent: hex colours like "#1E3A8A". Pick one palette for the whole video and vary it slightly per scene. The headline is drawn in white on the background, so backgrounds must be dark enough for white text to read clearly. The accent should stand out against the background.
- caption: a short social-media caption for posting the video, with up to 4 hashtags.
- notes_for_writer: 2 to 4 sentences of honest feedback for the scriptwriter: what worked, what you changed and why, and one idea to make the next script better."""


class Scene(BaseModel):
    narration: str
    headline: str
    subtext: str
    background: str = Field(description='Dark hex colour, e.g. "#0F172A"')
    accent: str = Field(description='Bright hex colour, e.g. "#F59E0B"')


class VideoPlan(BaseModel):
    title: str
    scenes: list[Scene]
    caption: str
    notes_for_writer: str


class Director:
    def __init__(self, effort: str = "high"):
        self.client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
        self.effort = effort

    def plan(self, script: str) -> VideoPlan:
        response = self.client.beta.messages.parse(
            model=MODEL,
            max_tokens=16000,
            system=SYSTEM,
            messages=[{"role": "user", "content": f"Here is the script:\n\n{script}"}],
            output_format=VideoPlan,
            thinking={"type": "adaptive"},
            output_config={"effort": self.effort},
            betas=[FALLBACK_BETA],
            fallbacks="default",
        )
        if response.stop_reason == "refusal":
            raise RuntimeError("Claude declined to plan this script. Try a different brief.")
        if response.stop_reason == "max_tokens" or response.parsed_output is None:
            raise RuntimeError("Claude's scene plan was cut off or unreadable.")
        plan = response.parsed_output
        if not plan.scenes:
            raise RuntimeError("Claude returned a plan with no scenes.")
        return plan

    @staticmethod
    def handoff(plan: VideoPlan, number: int, seconds: float, filename: str) -> str:
        """The message Claude sends back to ChatGPT once the video is rendered."""
        return (
            f"VIDEO #{number} IS DONE.\n"
            f"Title: {plan.title}\n"
            f"Length: {seconds:.0f} seconds, {len(plan.scenes)} scenes, saved as {filename}.\n"
            f"Headlines used: {' / '.join(s.headline for s in plan.scenes)}\n\n"
            f"Notes from Claude, the producer:\n{plan.notes_for_writer}"
        )
