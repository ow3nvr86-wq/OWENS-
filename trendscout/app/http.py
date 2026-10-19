"""HTTP with timeouts and bounded retries for idempotent reads.

Writes (publishing) never go through `get_with_retries`; publishers classify
their own failures because a retried POST can create a duplicate post.
"""
from __future__ import annotations

import asyncio
import logging
import random
from email.utils import parsedate_to_datetime

import httpx

from .timeutil import utcnow

log = logging.getLogger(__name__)
USER_AGENT = "TrendScout/1.0 (+https://github.com/; trend discovery bot)"
RETRY_STATUS = {408, 425, 429, 500, 502, 503, 504}


class HTTPFailure(Exception):
    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


def retry_after_seconds(resp: httpx.Response, default: float) -> float:
    value = resp.headers.get("retry-after")
    if not value:
        return default
    try:
        return max(0.0, float(value))
    except ValueError:
        try:
            return max(0.0, (parsedate_to_datetime(value) - utcnow()).total_seconds())
        except (TypeError, ValueError):
            return default


async def get_with_retries(
    client: httpx.AsyncClient, url: str, *, retries: int = 2, backoff: float = 1.0,
    max_wait: float = 30.0, **kwargs,
) -> httpx.Response:
    last: Exception | None = None
    for attempt in range(retries + 1):
        try:
            resp = await client.get(url, **kwargs)
        except (httpx.TimeoutException, httpx.TransportError) as e:
            last = e
            log.warning("GET failed", extra={"url": _safe(url), "attempt": attempt + 1, "error": type(e).__name__})
        else:
            if resp.status_code not in RETRY_STATUS:
                if resp.status_code >= 400:
                    raise HTTPFailure(f"HTTP {resp.status_code} from {_safe(url)}", resp.status_code)
                return resp
            last = HTTPFailure(f"HTTP {resp.status_code} from {_safe(url)}", resp.status_code)
            if attempt < retries:
                wait = min(max_wait, retry_after_seconds(resp, backoff * 2 ** attempt))
                await asyncio.sleep(wait)
                continue
        if attempt < retries:
            await asyncio.sleep(backoff * 2 ** attempt + random.uniform(0, 0.25))
    if isinstance(last, HTTPFailure):
        raise last
    raise HTTPFailure(f"{type(last).__name__} for {_safe(url)}")


def _safe(url: str) -> str:
    """Drop the query string from logged URLs; API keys often travel there."""
    return url.split("?", 1)[0]


def make_client(timeout: float = 15.0, transport: httpx.AsyncBaseTransport | None = None) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        timeout=httpx.Timeout(timeout, connect=min(10.0, timeout)),
        headers={"User-Agent": USER_AGENT},
        follow_redirects=True,
        transport=transport,
        limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
    )
