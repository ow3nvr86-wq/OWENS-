"""Configurable RSS and Atom feeds."""
from __future__ import annotations

import asyncio
import calendar
import logging
from datetime import datetime, timezone

import feedparser

from ..http import get_with_retries
from ..models import TrendItem
from ..textutil import keywords, stable_hash, strip_html
from ..timeutil import iso
from .base import Collector, CollectorContext

log = logging.getLogger(__name__)


def _entry_date(entry) -> str | None:
    for key in ("published_parsed", "updated_parsed"):
        value = entry.get(key)
        if value:
            return iso(datetime.fromtimestamp(calendar.timegm(value), timezone.utc))
    return None


class NewsRSSCollector(Collector):
    name = "news_rss"
    config_key = "news_rss"

    async def collect(self, ctx: CollectorContext) -> list[TrendItem]:
        opts = self.options(ctx.settings)
        limit = int(opts.get("limit_per_feed", 20))
        feeds = ctx.settings.collectors.feeds()

        async def one(feed) -> list[TrendItem]:
            try:
                resp = await get_with_retries(ctx.client, feed.url, retries=ctx.retries)
            except Exception as e:  # one bad feed must not drop the others
                log.warning("feed failed", extra={"feed": feed.name, "error": str(e)})
                return []
            parsed = feedparser.parse(resp.content)
            items: list[TrendItem] = []
            entries = parsed.entries[:limit]
            for position, entry in enumerate(entries):
                title = strip_html(entry.get("title", ""))
                link = entry.get("link")
                if not title or not link:
                    continue
                summary = strip_html(entry.get("summary", ""))[:600]
                items.append(TrendItem(
                    source=self.name,
                    external_id=entry.get("id") or stable_hash(feed.url, link),
                    topic=title,
                    source_url=link,
                    published_at=_entry_date(entry),
                    metrics={"position": float(position), "feed_size": float(len(entries))},
                    # Feeds carry no engagement numbers; rank is the only popularity signal.
                    primary_metric=float(len(entries) - position),
                    summary=summary,
                    keywords=keywords(f"{title} {summary}"),
                    confidence=feed.credibility,
                    raw={"publisher": feed.name, "feed_url": feed.url, "trusted": feed.trusted},
                ))
            return items

        batches = await asyncio.gather(*(one(f) for f in feeds))
        return [i for b in batches for i in b]
