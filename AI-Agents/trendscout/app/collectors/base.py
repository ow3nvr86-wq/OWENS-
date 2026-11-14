from __future__ import annotations

import asyncio
import logging
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import httpx

from ..config import Settings
from ..models import TrendItem

log = logging.getLogger(__name__)


class NotConfigured(Exception):
    """The source needs credentials or settings that are not present."""


@dataclass
class CollectorContext:
    settings: Settings
    client: httpx.AsyncClient
    env: dict[str, str] = field(default_factory=lambda: dict(os.environ))

    @property
    def retries(self) -> int:
        return self.settings.collectors.retries


class Collector(ABC):
    name: str = ""
    config_key: str = ""

    def options(self, settings: Settings) -> dict:
        return getattr(settings.collectors, self.config_key)

    def enabled(self, settings: Settings) -> bool:
        return bool(self.options(settings).get("enabled", False))

    @abstractmethod
    async def collect(self, ctx: CollectorContext) -> list[TrendItem]:
        ...


@dataclass
class CollectorReport:
    name: str
    status: str            # ok | skipped | failed | disabled
    count: int = 0
    seconds: float = 0.0
    message: str = ""


async def run_collectors(collectors: list[Collector], ctx: CollectorContext) -> tuple[list[TrendItem], list[CollectorReport]]:
    """Run every enabled collector concurrently. A failure in one source is
    recorded in its report and never stops the others."""

    async def one(c: Collector) -> tuple[list[TrendItem], CollectorReport]:
        if not c.enabled(ctx.settings):
            return [], CollectorReport(c.name, "disabled")
        start = time.monotonic()
        try:
            items = await c.collect(ctx)
        except NotConfigured as e:
            log.info("collector skipped", extra={"collector": c.name, "reason": str(e)})
            return [], CollectorReport(c.name, "skipped", message=str(e))
        except Exception as e:  # noqa: BLE001 - isolation is the point
            log.warning("collector failed", extra={"collector": c.name, "error": f"{type(e).__name__}: {e}"})
            return [], CollectorReport(c.name, "failed", seconds=time.monotonic() - start, message=f"{type(e).__name__}: {e}")
        valid = [i for i in items if i.topic]
        return valid, CollectorReport(c.name, "ok", len(valid), time.monotonic() - start)

    results = await asyncio.gather(*(one(c) for c in collectors))
    items = [i for batch, _ in results for i in batch]
    return items, [r for _, r in results]


def all_collectors() -> list[Collector]:
    from .google_trends import GoogleTrendsCollector
    from .hacker_news import HackerNewsCollector
    from .news_rss import NewsRSSCollector
    from .reddit import RedditCollector
    from .x_trends import XTrendsCollector
    from .youtube import YouTubeCollector
    return [HackerNewsCollector(), NewsRSSCollector(), GoogleTrendsCollector(), RedditCollector(),
            YouTubeCollector(), XTrendsCollector()]
