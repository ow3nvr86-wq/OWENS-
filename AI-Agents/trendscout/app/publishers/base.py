"""Publisher adapters share one contract and one failure taxonomy.

The key distinction is FAILED versus UNCERTAIN. FAILED means the platform
definitely did not create the post (the connection never opened, or it
answered with a clear rejection), so retrying is safe. UNCERTAIN means the
request may have been accepted (a timeout after sending, a 5xx, a dropped
connection), so the job must be reconciled with the platform before anything
is retried.
"""
from __future__ import annotations

import os
from abc import ABC, abstractmethod
from datetime import timedelta

import httpx

from ..database import loads
from ..logging_config import scrub
from ..models import Outcome, PostMetrics, PublishResult
from ..timeutil import parse_any, utcnow


class Publisher(ABC):
    platform = ""
    required_env: tuple[str, ...] = ()
    prerequisites = ""   # shown on the dashboard and in `doctor`

    def __init__(self, env: dict[str, str] | None = None):
        self.env = env if env is not None else dict(os.environ)

    def configured(self) -> tuple[bool, str]:
        missing = [k for k in self.required_env if not self.env.get(k)]
        if missing:
            return False, "missing " + ", ".join(missing)
        return True, "credentials present (not yet verified)"

    @abstractmethod
    async def verify(self, client: httpx.AsyncClient) -> tuple[bool, str]:
        """Check the credentials against the platform without posting anything."""

    @abstractmethod
    async def publish(self, client: httpx.AsyncClient, job: dict, draft: dict) -> PublishResult:
        ...

    async def reconcile(self, client: httpx.AsyncClient, job: dict, draft: dict) -> PublishResult | None:
        """After an uncertain outcome: SUCCESS if the post exists, FAILED if it
        definitely does not, None if the platform cannot tell us."""
        return None

    async def metrics(self, client: httpx.AsyncClient, post: dict) -> PostMetrics | None:
        return None


def structure(draft: dict) -> dict:
    return loads(draft.get("structure_json"), {}) or {}


def from_exception(e: Exception, platform: str) -> PublishResult:
    if isinstance(e, (httpx.ConnectError, httpx.ConnectTimeout, httpx.PoolTimeout, httpx.UnsupportedProtocol)):
        return PublishResult(Outcome.FAILED, error=f"{platform}: could not connect ({type(e).__name__}); nothing was sent",
                             retryable=True)
    # Read/write timeouts and protocol errors happen after the request may have arrived.
    return PublishResult(Outcome.UNCERTAIN, error=f"{platform}: no definite answer ({type(e).__name__})")


def from_response(resp: httpx.Response, platform: str) -> PublishResult:
    body = scrub(resp.text[:500])
    if resp.status_code == 429:
        until = _reset_time(resp)
        return PublishResult(Outcome.FAILED, error=f"{platform}: rate limited", retryable=True, rate_limited_until=until)
    if resp.status_code in (401, 403):
        return PublishResult(Outcome.FAILED, error=f"{platform}: permission denied (HTTP {resp.status_code}); check the "
                                                   f"credentials, scopes and account eligibility. {body}")
    if resp.status_code == 408 or resp.status_code >= 500:
        return PublishResult(Outcome.UNCERTAIN, error=f"{platform}: HTTP {resp.status_code}; the post may or may not exist")
    return PublishResult(Outcome.FAILED, error=f"{platform}: rejected (HTTP {resp.status_code}): {body}")


def _reset_time(resp: httpx.Response):
    for header in ("ratelimit-reset", "x-rate-limit-reset", "x-ratelimit-reset"):
        value = resp.headers.get(header)
        if value and value.isdigit():
            n = int(value)
            # Some APIs send an epoch timestamp, others a number of seconds.
            return parse_any(n) if n > 1_000_000_000 else utcnow() + timedelta(seconds=n)
    retry = resp.headers.get("retry-after")
    if retry and retry.isdigit():
        return utcnow() + timedelta(seconds=int(retry))
    return utcnow() + timedelta(minutes=15)


class DryRunPublisher(Publisher):
    """Simulates publication. Used whenever publishing.dry_run is on, in
    offline mode and in tests; it never opens a network connection."""

    def __init__(self, platform: str):
        super().__init__({})
        self.platform = platform

    async def verify(self, client):
        return True, "dry run"

    async def publish(self, client, job, draft):
        return PublishResult(Outcome.SUCCESS, platform_post_id=f"dryrun-{job['id']}", url=None,
                             detail={"dry_run": True, "would_post": draft["post_text"]})


def all_publishers(env: dict[str, str] | None = None) -> dict[str, Publisher]:
    from .bluesky import BlueskyPublisher
    from .instagram import InstagramPublisher
    from .linkedin import LinkedInPublisher
    from .threads import ThreadsPublisher
    from .tiktok import TikTokPublisher
    from .x import XPublisher
    return {p.platform: p for p in (BlueskyPublisher(env), XPublisher(env), InstagramPublisher(env),
                                    ThreadsPublisher(env), LinkedInPublisher(env), TikTokPublisher(env))}
