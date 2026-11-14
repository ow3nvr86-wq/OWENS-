"""YouTube Data API v3. Needs YOUTUBE_API_KEY (Google Cloud console ->
enable "YouTube Data API v3" -> create an API key).

Quota: videos.list costs 1 unit, search.list costs 100 (default quota is
10,000 units/day). The mostPopular chart is not available for every
region/category pair; a 400/404 there is logged and the run carries on.
"""
from __future__ import annotations

import logging

from ..http import HTTPFailure, get_with_retries
from ..models import TrendItem
from ..textutil import keywords
from ..timeutil import ago, iso, parse_any
from .base import Collector, CollectorContext, NotConfigured

log = logging.getLogger(__name__)
API = "https://www.googleapis.com/youtube/v3"


class YouTubeCollector(Collector):
    name = "youtube"
    config_key = "youtube"

    async def collect(self, ctx: CollectorContext) -> list[TrendItem]:
        key = ctx.env.get("YOUTUBE_API_KEY", "")
        if not key:
            raise NotConfigured("set YOUTUBE_API_KEY")
        opts = self.options(ctx.settings)
        limit = min(50, int(opts.get("limit", 25)))
        videos: dict[str, dict] = {}

        params = {"part": "snippet,statistics", "chart": "mostPopular", "maxResults": limit,
                  "regionCode": opts.get("region", "US"), "key": key}
        if opts.get("category_id"):
            params["videoCategoryId"] = str(opts["category_id"])
        try:
            resp = await get_with_retries(ctx.client, f"{API}/videos", params=params, retries=ctx.retries)
            for v in resp.json().get("items", []):
                videos[v["id"]] = {**v, "_via": "mostPopular"}
        except HTTPFailure as e:
            if e.status in (401, 403):
                raise NotConfigured(f"YouTube rejected the API key or quota is exhausted (HTTP {e.status})") from e
            log.warning("youtube mostPopular unavailable for this region/category",
                        extra={"status": e.status, "region": params["regionCode"]})

        queries = [q for q in opts.get("search_queries", []) if q]
        if queries:
            ids: list[str] = []
            for q in queries:
                try:
                    r = await get_with_retries(ctx.client, f"{API}/search", retries=ctx.retries, params={
                        "part": "id", "type": "video", "order": "viewCount", "maxResults": 10, "q": q,
                        "publishedAfter": ago(hours=48), "regionCode": opts.get("region", "US"), "key": key,
                    })
                except HTTPFailure as e:
                    log.warning("youtube search failed", extra={"query": q, "status": e.status})
                    continue
                ids += [i["id"]["videoId"] for i in r.json().get("items", []) if i.get("id", {}).get("videoId")]
            new_ids = [i for i in dict.fromkeys(ids) if i not in videos]
            if new_ids:
                r = await get_with_retries(ctx.client, f"{API}/videos", retries=ctx.retries, params={
                    "part": "snippet,statistics", "id": ",".join(new_ids[:50]), "key": key})
                for v in r.json().get("items", []):
                    videos[v["id"]] = {**v, "_via": "search"}

        return [self._item(v) for v in videos.values() if v.get("snippet", {}).get("title")]

    def _item(self, v: dict) -> TrendItem:
        sn, st = v.get("snippet", {}), v.get("statistics", {})
        views = float(st.get("viewCount") or 0)
        likes = float(st.get("likeCount") or 0)
        comments = float(st.get("commentCount") or 0)
        published = parse_any(sn.get("publishedAt"))
        desc = (sn.get("description") or "")[:500]
        metrics = {"views": views, "likes": likes, "comments": comments}
        return TrendItem(
            source=self.name,
            external_id=v["id"],
            topic=sn["title"],
            source_url=f"https://www.youtube.com/watch?v={v['id']}",
            published_at=iso(published) if published else None,
            metrics=metrics,
            primary_metric=views,
            summary=f"YouTube video by {sn.get('channelTitle', 'unknown channel')}. {desc}",
            keywords=keywords(f"{sn['title']} {' '.join(sn.get('tags', [])[:10])}"),
            confidence=0.35,
            raw={"channel": sn.get("channelTitle"), "via": v.get("_via"), "category_id": sn.get("categoryId")},
        )
