"""Reddit via the official OAuth API (application-only "client credentials").

Create a "script" or "web" app at https://www.reddit.com/prefs/apps and set
REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET and a descriptive REDDIT_USER_AGENT
(Reddit requires "platform:app-id:version (by /u/username)").
"""
from __future__ import annotations

import logging

from ..http import HTTPFailure, get_with_retries
from ..models import TrendItem
from ..textutil import keywords
from ..timeutil import hours_since, iso, parse_any
from .base import Collector, CollectorContext, NotConfigured

log = logging.getLogger(__name__)
TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
API = "https://oauth.reddit.com"


class RedditCollector(Collector):
    name = "reddit"
    config_key = "reddit"

    async def _token(self, ctx: CollectorContext, client_id: str, secret: str, ua: str) -> str:
        resp = await ctx.client.post(
            TOKEN_URL, data={"grant_type": "client_credentials"}, auth=(client_id, secret),
            headers={"User-Agent": ua},
        )
        if resp.status_code in (401, 403):
            raise NotConfigured(f"Reddit rejected the app credentials (HTTP {resp.status_code})")
        resp.raise_for_status()
        token = resp.json().get("access_token")
        if not token:
            raise HTTPFailure("Reddit token response had no access_token")
        return token

    async def collect(self, ctx: CollectorContext) -> list[TrendItem]:
        client_id = ctx.env.get("REDDIT_CLIENT_ID", "")
        secret = ctx.env.get("REDDIT_CLIENT_SECRET", "")
        ua = ctx.env.get("REDDIT_USER_AGENT", "")
        if not (client_id and secret and ua):
            raise NotConfigured("set REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET and REDDIT_USER_AGENT")
        token = await self._token(ctx, client_id, secret, ua)
        headers = {"Authorization": f"Bearer {token}", "User-Agent": ua}
        opts = self.options(ctx.settings)
        limit = min(100, int(opts.get("limit", 25)))
        out: list[TrendItem] = []
        for sub in opts.get("subreddits", ["popular"]):
            try:
                resp = await get_with_retries(
                    ctx.client, f"{API}/r/{sub}/hot", params={"limit": limit, "raw_json": 1},
                    headers=headers, retries=ctx.retries,
                )
            except HTTPFailure as e:
                log.warning("subreddit failed", extra={"subreddit": sub, "error": str(e)})
                continue
            out.extend(self._parse(resp.json(), sub))
            remaining = resp.headers.get("x-ratelimit-remaining")
            if remaining is not None and float(remaining) < 2:
                log.warning("reddit rate limit nearly exhausted; stopping early",
                            extra={"reset_seconds": resp.headers.get("x-ratelimit-reset")})
                break
        return out

    def _parse(self, payload: dict, sub: str) -> list[TrendItem]:
        out: list[TrendItem] = []
        for child in (payload.get("data") or {}).get("children", []):
            d = child.get("data") or {}
            if d.get("over_18") or d.get("stickied") or not d.get("title"):
                continue
            created = parse_any(d.get("created_utc"))
            age = hours_since(created) or 0.0
            score = float(d.get("score") or 0)
            comments = float(d.get("num_comments") or 0)
            permalink = f"https://www.reddit.com{d.get('permalink', '')}"
            link = d.get("url_overridden_by_dest") or d.get("url") or permalink
            out.append(TrendItem(
                source=self.name,
                external_id=str(d.get("id")),
                topic=d["title"],
                source_url=link if str(link).startswith("http") else permalink,
                published_at=iso(created) if created else None,
                metrics={"score": score, "comments": comments, "upvote_ratio": float(d.get("upvote_ratio") or 0),
                         "velocity": score / max(age, 0.5)},
                primary_metric=score + 2 * comments,
                summary=(d.get("selftext") or "")[:400] or f"Popular in r/{d.get('subreddit', sub)}.",
                keywords=keywords(d["title"]),
                confidence=0.4,
                raw={"subreddit": d.get("subreddit", sub), "permalink": permalink, "domain": d.get("domain")},
            ))
        return out
