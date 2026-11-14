"""Hacker News via the official Firebase API (no key needed)."""
from __future__ import annotations

import asyncio

from ..http import HTTPFailure, get_with_retries
from ..models import TrendItem
from ..textutil import keywords
from ..timeutil import iso, parse_any
from .base import Collector, CollectorContext

API = "https://hacker-news.firebaseio.com/v0"
LISTS = {"top": "topstories", "best": "beststories", "new": "newstories"}


class HackerNewsCollector(Collector):
    name = "hacker_news"
    config_key = "hacker_news"

    async def collect(self, ctx: CollectorContext) -> list[TrendItem]:
        opts = self.options(ctx.settings)
        limit = int(opts.get("limit", 30))
        ids: dict[int, str] = {}
        for lst in opts.get("lists", ["top"]):
            endpoint = LISTS.get(lst)
            if not endpoint:
                continue
            resp = await get_with_retries(ctx.client, f"{API}/{endpoint}.json", retries=ctx.retries)
            for story_id in (resp.json() or [])[:limit]:
                if isinstance(story_id, int):
                    ids.setdefault(story_id, lst)

        sem = asyncio.Semaphore(10)

        async def item(story_id: int) -> dict | None:
            async with sem:
                try:
                    r = await get_with_retries(ctx.client, f"{API}/item/{story_id}.json", retries=ctx.retries)
                except HTTPFailure:
                    return None
                return r.json()

        stories = await asyncio.gather(*(item(i) for i in ids))
        out: list[TrendItem] = []
        for story in stories:
            if not isinstance(story, dict) or story.get("type") != "story" or story.get("dead") or story.get("deleted"):
                continue
            title = str(story.get("title") or "")
            if not title:
                continue
            discussion = f"https://news.ycombinator.com/item?id={story['id']}"
            score = float(story.get("score") or 0)
            comments = float(story.get("descendants") or 0)
            published = parse_any(story.get("time"))
            out.append(TrendItem(
                source=self.name,
                external_id=str(story["id"]),
                topic=title,
                source_url=story.get("url") or discussion,
                published_at=iso(published) if published else None,
                metrics={"score": score, "comments": comments},
                primary_metric=score + comments,
                summary=f"Hacker News {ids[story['id']]} story with {int(score)} points and {int(comments)} comments.",
                keywords=keywords(title),
                confidence=0.6,
                raw={"discussion_url": discussion, "list": ids[story["id"]], "by": story.get("by")},
            ))
        return out
