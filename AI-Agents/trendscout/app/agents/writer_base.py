"""Shared machinery for the platform writers. Each writer gets the same
verified research and returns a structured draft for its platform."""
from __future__ import annotations

import re

from ..config import Settings
from ..llm import LLM
from ..models import Cluster, Draft, DraftOutput, Research
from ..textutil import count_chars
from . import prompts
from .researcher import research_json

_TAG = re.compile(r"^#?[\w]{2,40}$", re.UNICODE)


class PlatformWriter:
    platform = ""
    char_limit = 300
    lengths = {"short": 120, "medium": 200, "long": 280}
    guide = ""
    supports_thread = False
    needs_media = False

    def thread_allowed(self, settings: Settings) -> bool:
        return self.supports_thread and settings.platforms[self.platform].threads

    def platform_guide(self, settings: Settings) -> str:
        guide = self.guide.strip()
        if self.thread_allowed(settings):
            n = settings.platforms[self.platform].max_thread_posts
            guide += (f"\nA thread is allowed when the topic genuinely needs more room: up to {n} posts in total, "
                      f"each within {self.char_limit} characters. Most topics need a single post.")
        elif self.supports_thread:
            guide += "\nThreads are switched off: write one post and leave thread_posts empty."
        return guide

    def user_prompt(self, research: Research, settings: Settings, revision: str, human: str, insights: str = "") -> str:
        target = self.lengths[settings.content.length]
        parts = [
            f"Write a {self.platform} post. Aim for about {target} characters (hard limit {self.char_limit}).",
            "Research brief (verified claims only may be used):",
            research_json(research),
        ]
        if insights:
            parts.append(insights)
        if revision:
            parts += ["Reviewer feedback on your previous draft - address every point:", revision]
        if human:
            parts += ["Instructions from the account owner for this rewrite:", human]
        return "\n\n".join(parts)

    async def write(self, research: Research, cluster: Cluster, settings: Settings, llm: LLM,
                    revision: str = "", human: str = "", insights: str = "") -> Draft:
        out = await llm.structured(
            task=f"write:{self.platform}", model=settings.ai.model, effort=settings.ai.effort_write,
            system=prompts.writer_system(settings, self.platform_guide(settings), self.char_limit),
            prompt=self.user_prompt(research, settings, revision, human, insights), schema=DraftOutput,
            context={
                "platform": self.platform, "char_limit": self.char_limit,
                "verified_claims": [c.model_dump() for c in research.verified_claims()],
                "summary": research.output.summary, "include_links": settings.content.include_links,
                "revision_instructions": revision or human,
            },
        )
        return self.postprocess(out, cluster, settings, llm.name)

    def postprocess(self, out: DraftOutput, cluster: Cluster, settings: Settings, generated_by: str) -> Draft:
        tags: list[str] = []
        for t in out.hashtags:
            t = t.strip().replace(" ", "")
            if _TAG.match(t):
                t = t if t.startswith("#") else f"#{t}"
                if t.lower() not in {x.lower() for x in tags}:
                    tags.append(t)
        text = out.post_text.strip()
        return Draft(
            platform=self.platform, cluster_key=cluster.key, post_text=text,
            thread_posts=[p.strip() for p in out.thread_posts if p.strip()] if self.thread_allowed(settings) else [],
            carousel_slides=[s.strip() for s in out.carousel_slides if s.strip()],
            script=out.script.strip(), shot_list=[s.strip() for s in out.shot_list if s.strip()],
            media_brief=out.media_brief.strip(), source_urls=list(dict.fromkeys(out.source_urls)),
            hashtags=tags[: settings.content.max_hashtags], claims=out.claims, rationale=out.rationale,
            char_count=count_chars(text, self.platform), char_limit=self.char_limit, generated_by=generated_by,
        )


def writers_for(platforms: list[str]) -> list[PlatformWriter]:
    from ..writers import WRITERS
    return [WRITERS[p]() for p in platforms if p in WRITERS]
