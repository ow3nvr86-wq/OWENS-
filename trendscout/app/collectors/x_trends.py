"""Optional X trends adapter (GET /2/trends/by/woeid/:woeid).

Only works on an X API tier that includes the trends endpoint; an HTTP 403
is reported as an access-tier problem rather than retried.
"""
from __future__ import annotations

from ..http import HTTPFailure, get_with_retries
from ..models import TrendItem
from ..textutil import keywords
from .base import Collector, CollectorContext, NotConfigured

API = "https://api.x.com/2/trends/by/woeid/{woeid}"


class XTrendsCollector(Collector):
    name = "x_trends"
    config_key = "x_trends"

    async def collect(self, ctx: CollectorContext) -> list[TrendItem]:
        token = ctx.env.get("X_BEARER_TOKEN", "")
        if not token:
            raise NotConfigured("set X_BEARER_TOKEN (needs an X API tier with trends access)")
        woeid = int(self.options(ctx.settings).get("woeid", 1))
        try:
            resp = await get_with_retries(ctx.client, API.format(woeid=woeid), retries=ctx.retries,
                                          headers={"Authorization": f"Bearer {token}"})
        except HTTPFailure as e:
            if e.status in (401, 403):
                raise NotConfigured(f"X refused trends access (HTTP {e.status}); check the API tier and token") from e
            raise
        out: list[TrendItem] = []
        for position, t in enumerate(resp.json().get("data", [])):
            name = t.get("trend_name") or ""
            if not name:
                continue
            count = t.get("tweet_count")
            out.append(TrendItem(
                source=self.name,
                external_id=f"{woeid}:{name.lower()}",
                topic=name,
                source_url=f"https://x.com/search?q={name.replace('#', '%23').replace(' ', '%20')}",
                metrics={"post_count": float(count)} if count else {"position": float(position)},
                primary_metric=float(count) if count else float(50 - position),
                summary=f"Trending on X ({count} posts)." if count else "Trending on X.",
                keywords=keywords(name),
                confidence=0.25,  # a hashtag is a pointer, never evidence
                raw={"woeid": woeid},
            ))
        return out
