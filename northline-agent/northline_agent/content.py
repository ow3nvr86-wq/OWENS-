"""Asks Claude to write the day's three slideshow posts."""

import json

import anthropic
from pydantic import BaseModel

from .config import Config


class Slide(BaseModel):
    headline: str
    body: str


class Post(BaseModel):
    pillar: str
    hook: str
    slides: list[Slide]
    cta: Slide
    caption: str
    hashtags: list[str]
    tiktok_title: str


class DayPlan(BaseModel):
    posts: list[Post]


_SLIDE_SCHEMA = {
    "type": "object",
    "properties": {
        "headline": {"type": "string", "description": "Big text on the slide. 2-8 words."},
        "body": {"type": "string", "description": "Supporting line under the headline. At most 30 words. Empty string if none."},
    },
    "required": ["headline", "body"],
    "additionalProperties": False,
}

_SCHEMA = {
    "type": "object",
    "properties": {
        "posts": {
            "type": "array",
            "description": "Exactly three posts, in the order they will go out.",
            "items": {
                "type": "object",
                "properties": {
                    "pillar": {"type": "string", "description": "Which content pillar this post belongs to."},
                    "hook": {"type": "string", "description": "Cover slide text that stops the scroll. At most 10 words."},
                    "slides": {"type": "array", "items": _SLIDE_SCHEMA, "description": "The middle slides, after the cover."},
                    "cta": _SLIDE_SCHEMA,
                    "caption": {"type": "string", "description": "Post caption, 1-4 short lines, no hashtags."},
                    "hashtags": {"type": "array", "items": {"type": "string"}, "description": "4-8 hashtags including the leading #."},
                    "tiktok_title": {"type": "string", "description": "Short TikTok title, at most 80 characters."},
                },
                "required": ["pillar", "hook", "slides", "cta", "caption", "hashtags", "tiktok_title"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["posts"],
    "additionalProperties": False,
}


def _system_prompt(cfg: Config) -> str:
    b = cfg.brand
    products = "\n".join(f"- {p}" for p in b.get("products") or []) or "- (none listed yet: keep product mentions general)"
    pillars = "\n".join(f"- {p}" for p in b["content_pillars"])
    rules = "\n".join(f"- {r}" for r in b.get("rules") or [])
    return f"""You are the social media lead for {b['name']} ({b['handle']}), writing photo-slideshow posts
that go out identically on TikTok, Instagram and Facebook.

What we sell: {b['what_we_sell'].strip()}
Audience: {b['audience'].strip()}
Voice: {b['voice'].strip()}
Store: {b['store_url']}

Products:
{products}

Content pillars:
{pillars}

Rules:
{rules}

How a good slideshow works here: the cover hook makes a specific promise, each middle slide delivers
one idea someone can use or feel, and the last slide points to {b['store_url']} or asks people to follow.
Write text that reads well in huge type on a phone: short, concrete, no emoji on slides."""


def generate_day(cfg: Config, date_label: str, recent_hooks: list[str]) -> DayPlan:
    n_min, n_max = cfg.schedule["slides_min"], cfg.schedule["slides_max"]
    avoid = "\n".join(f"- {h}" for h in recent_hooks[-30:]) or "- (nothing yet)"
    user = f"""Write the three posts for {date_label}.

Each post has a cover hook, {n_min - 2} to {n_max - 2} middle slides, and a closing call-to-action slide,
so {n_min} to {n_max} images in total. Use a different content pillar for each post.

Recent hooks. Don't repeat these or their angles:
{avoid}"""

    client = anthropic.Anthropic(api_key=cfg.secrets.anthropic_api_key)
    response = client.beta.messages.create(
        model=cfg.model,
        max_tokens=16000,
        system=_system_prompt(cfg),
        messages=[{"role": "user", "content": user}],
        output_config={"effort": "medium", "format": {"type": "json_schema", "schema": _SCHEMA}},
        betas=["server-side-fallback-2026-07-01"],
        extra_body={"fallbacks": "default"},
    )
    if response.stop_reason == "refusal":
        raise RuntimeError(f"Claude declined to write today's posts: {response.stop_details}")
    if response.stop_reason == "max_tokens":
        raise RuntimeError("Claude's answer was cut off before it finished.")

    text = next(b.text for b in response.content if b.type == "text")
    plan = DayPlan.model_validate(json.loads(text))
    _normalise(plan, cfg)
    return plan


def _normalise(plan: DayPlan, cfg: Config) -> None:
    """Keeps the plan inside what the schema can't enforce and the platforms allow."""
    if len(plan.posts) < 3:
        raise RuntimeError(f"Expected 3 posts, got {len(plan.posts)}")
    del plan.posts[3:]
    max_middle = cfg.schedule["slides_max"] - 2
    for post in plan.posts:
        del post.slides[max_middle:]
        if not post.slides:
            raise RuntimeError(f"Post '{post.hook}' has no middle slides")
        tags = [t if t.startswith("#") else f"#{t}" for t in post.hashtags]
        for tag in cfg.brand.get("hashtags_always") or []:
            if tag.lower() not in (t.lower() for t in tags):
                tags.append(tag)
        post.hashtags = tags[:10]
        post.tiktok_title = post.tiktok_title[:89]
