from __future__ import annotations

import asyncio
from pathlib import Path

import httpx
import pytest

from app.config import Env, load_settings
from app.database import Database
from app.fixtures import offline_transport
from app.llm import SimulatedLLM
from app.models import Outcome, PublishResult
from app.pipeline import Pipeline
from app.publishers.base import Publisher


def run(coro):
    return asyncio.run(coro)


class NoNetwork(httpx.MockTransport):
    """Fails any request a test did not expect, so nothing can reach the internet."""

    def __init__(self):
        super().__init__(lambda r: (_ for _ in ()).throw(AssertionError(f"unexpected network call: {r.url}")))


@pytest.fixture
def settings():
    s = load_settings(Path(__file__).resolve().parent.parent / "config" / "trendscout.toml")
    # Tests run at any time of day; keep the publishing window open around the clock.
    s.schedule.timezone = "UTC"
    s.schedule.publish_window_start = "00:00"
    s.schedule.publish_window_end = "23:59"
    s.publishing.min_minutes_between_posts = 0
    return s


@pytest.fixture
def db(tmp_path):
    d = Database(tmp_path / "test.db")
    d.migrate()
    return d


@pytest.fixture
def env(tmp_path):
    return Env(database_path=tmp_path / "test.db", dashboard_username="admin", dashboard_password="correct-horse-battery",
               session_secret="s" * 40, trigger_token="t" * 32, anthropic_api_key="")


@pytest.fixture
def pipeline(settings, db, env):
    return Pipeline(settings, db, env, offline=True)


class RecordingPublisher(Publisher):
    """A fake platform that records every call; outcomes can be scripted."""
    platform = "bluesky"

    def __init__(self, outcomes=None, delay: float = 0.0):
        super().__init__({})
        self.calls: list[int] = []
        self.reconciles: list[int] = []
        self.outcomes = list(outcomes or [])
        self.reconcile_result = None
        self.delay = delay

    def configured(self):
        return True, "fake"

    async def verify(self, client):
        return True, "fake"

    async def publish(self, client, job, draft):
        self.calls.append(job["id"])
        if self.delay:
            await asyncio.sleep(self.delay)
        if self.outcomes:
            return self.outcomes.pop(0)
        return PublishResult(Outcome.SUCCESS, platform_post_id=f"at://did:plc:test/app.bsky.feed.post/{job['client_ref']}",
                             url=f"https://bsky.app/profile/test/post/{job['client_ref']}")

    async def reconcile(self, client, job, draft):
        self.reconciles.append(job["id"])
        return self.reconcile_result


def discover_offline(pipeline) -> dict:
    return run(pipeline.discover(trigger="test"))


def pending_ids(db) -> list[int]:
    return [r["id"] for r in db.query("SELECT id FROM drafts WHERE status = 'pending_approval' ORDER BY id")]


@pytest.fixture
def simulated(db):
    return SimulatedLLM(db)


@pytest.fixture
def offline_client():
    return httpx.AsyncClient(transport=offline_transport())
