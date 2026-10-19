"""Google Trends "trending now" RSS feed.

Google publishes no official trends API; the RSS feed is the public,
documented-by-use interface. It can change or disappear, so parsing is
defensive and a missing feed only produces a skipped/failed report.
"""
from __future__ import annotations

import re

from defusedxml import ElementTree as ET

from ..http import get_with_retries
from ..models import TrendItem
from ..textutil import keywords, strip_html
from ..timeutil import iso, parse_any
from .base import Collector, CollectorContext

FEED = "https://trends.google.com/trending/rss?geo={geo}"
HT = "{https://trends.google.com/trending/rss}"


def parse_traffic(value: str | None) -> float | None:
    if not value:
        return None
    m = re.match(r"([\d.,]+)\s*([KkMm]?)", value.strip())
    if not m:
        return None
    number = float(m.group(1).replace(",", ""))
    return number * {"k": 1e3, "m": 1e6}.get(m.group(2).lower(), 1)


class GoogleTrendsCollector(Collector):
    name = "google_trends"
    config_key = "google_trends"

    async def collect(self, ctx: CollectorContext) -> list[TrendItem]:
        geo = str(self.options(ctx.settings).get("geo", "US"))
        resp = await get_with_retries(ctx.client, FEED.format(geo=geo), retries=ctx.retries)
        root = ET.fromstring(resp.content)
        out: list[TrendItem] = []
        for item in root.iter("item"):
            title = (item.findtext("title") or "").strip()
            if not title:
                continue
            traffic = parse_traffic(item.findtext(f"{HT}approx_traffic"))
            news = []
            for n in item.findall(f"{HT}news_item"):
                news.append({
                    "title": strip_html(n.findtext(f"{HT}news_item_title") or ""),
                    "url": (n.findtext(f"{HT}news_item_url") or "").strip(),
                    "source": (n.findtext(f"{HT}news_item_source") or "").strip(),
                })
            news = [n for n in news if n["url"].startswith(("http://", "https://"))]
            published = parse_any(item.findtext("pubDate"))
            summary = "; ".join(f"{n['title']} ({n['source']})" for n in news[:3])
            out.append(TrendItem(
                source=self.name,
                external_id=f"{geo}:{title.lower()}:{published.date() if published else ''}",
                topic=title,
                source_url=news[0]["url"] if news else f"https://trends.google.com/trending?geo={geo}",
                published_at=iso(published) if published else None,
                metrics={"approx_traffic": traffic} if traffic is not None else {},
                primary_metric=traffic,
                summary=summary or f"Trending Google search in {geo}.",
                keywords=keywords(f"{title} {summary}"),
                # A search term alone says little; the attached news items carry the substance.
                confidence=0.5 if news else 0.3,
                raw={"region": geo, "news_items": news, "approx_traffic": item.findtext(f"{HT}approx_traffic")},
            ))
        return out
