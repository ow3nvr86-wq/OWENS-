import re
from datetime import datetime, timedelta

import httpx
import pytest
from fastapi.testclient import TestClient

from app.dashboard import auth
from app.main import create_app
from app.models import PostMetrics
from app.services import analytics, approval, controls, scheduler
from app.timeutil import UTC, iso, utcnow
from tests.conftest import RecordingPublisher, discover_offline, pending_ids, run


@pytest.fixture
def client(settings, env, db, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-should-never-appear-in-html")
    auth._failures.clear()
    app = create_app(settings=settings, env=env, db=db, offline=True)
    return TestClient(app)


def token(html):
    return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)


def login(c, password="correct-horse-battery"):
    t = token(c.get("/login").text)
    return c.post("/login", data={"username": "admin", "password": password, "csrf_token": t}, follow_redirects=False)


def test_pages_require_login(client):
    for path in ["/", "/trends", "/drafts", "/queue", "/published", "/analytics", "/logs"]:
        r = client.get(path, follow_redirects=False)
        assert r.status_code == 303 and r.headers["location"] == "/login", path
    assert client.post("/controls/pause", data={}, follow_redirects=False).status_code == 303


def test_login_csrf_and_lockout(client):
    assert client.post("/login", data={"username": "admin", "password": "correct-horse-battery", "csrf_token": "x"}).status_code == 403
    for _ in range(auth.MAX_FAILURES):
        login(client, "wrong")
    r = login(client)  # right password, but locked out
    assert r.headers["location"] == "/login"
    auth._failures.clear()
    assert login(client).headers["location"] == "/"


def test_dashboard_workflow(client, db, pipeline):
    discover_offline(pipeline)
    login(client)
    for path in ["/", "/trends", "/drafts", "/drafts?status=all", "/queue", "/published", "/analytics", "/logs", "/topics/1"]:
        r = client.get(path)
        assert r.status_code == 200, path
        assert "sk-ant-should-never-appear" not in r.text
    page = client.get("/drafts").text
    ids = pending_ids(db)
    assert f'id="draft-{ids[0]}"' in page and "Approve" in page
    t = token(page)
    # Without the form token nothing changes.
    assert client.post(f"/drafts/{ids[0]}/approve", data={"csrf_token": "forged"}).status_code == 403
    r = client.post("/drafts/bulk-approve", data={"csrf_token": t, "ids": ids[:2]}, follow_redirects=False)
    assert r.status_code == 303
    assert db.scalar("SELECT COUNT(*) FROM publish_jobs WHERE status = 'queued'") == 2
    client.post(f"/drafts/{ids[0]}/edit", data={"csrf_token": t, "text": "Edited by a person."})
    assert db.scalar("SELECT status FROM drafts WHERE id = ?", (ids[0],)) == "pending_approval"
    client.post(f"/drafts/{ids[1]}/reject", data={"csrf_token": t, "note": "off-brand"})
    assert db.scalar("SELECT status FROM drafts WHERE id = ?", (ids[1],)) == "rejected_by_human"
    # Kill switch from the dashboard.
    client.post("/controls/pause", data={"csrf_token": t, "reason": "checking something"})
    assert controls.is_paused(db)
    assert "Publishing paused" in client.get("/").text
    client.post("/controls/resume", data={"csrf_token": t})
    assert not controls.is_paused(db)


def test_trigger_api_needs_the_token(client):
    assert client.post("/api/trigger?task=publish").status_code == 401
    assert client.post("/api/trigger?task=publish", headers={"Authorization": "Bearer wrong"}).status_code == 401
    r = client.post("/api/trigger?task=publish", headers={"Authorization": "Bearer " + "t" * 32})
    assert r.status_code == 202


def test_security_headers(client):
    r = client.get("/login")
    assert "frame-ancestors 'none'" in r.headers["content-security-policy"]
    assert r.headers["x-frame-options"] == "DENY"


# ---- scheduler -------------------------------------------------------------------------------

def test_next_slot_respects_window_spacing_and_daily_limit(db, settings):
    settings.schedule.publish_window_start = "08:00"
    settings.schedule.publish_window_end = "21:00"
    late = datetime(2099, 1, 1, 22, 0, tzinfo=UTC)
    assert scheduler.next_slot(db, settings, "bluesky", late) == datetime(2099, 1, 2, 8, 0, tzinfo=UTC)

    settings.publishing.min_minutes_between_posts = 90
    settings.platforms["bluesky"].daily_limit = 2
    day = datetime(2099, 1, 2, 9, 0, tzinfo=UTC)
    # Two queued jobs fill the day; foreign keys are not the point of this test.
    conn = db._connect()
    conn.execute("PRAGMA foreign_keys = OFF")
    for i, t in enumerate((day, day + timedelta(hours=2))):
        conn.execute("INSERT INTO publish_jobs (draft_id, platform, idempotency_key, client_ref, status, scheduled_at, created_at, updated_at) "
                     "VALUES (?, 'bluesky', ?, 'x', 'queued', ?, 'x', 'x')", (1000 + i, f"k{i}", iso(t)))
    conn.close()
    slot = scheduler.next_slot(db, settings, "bluesky", day + timedelta(hours=3))
    assert slot == datetime(2099, 1, 3, 8, 0, tzinfo=UTC)  # day is full


def test_discovery_due(db, settings):
    settings.schedule.discovery_times = ["07:30", "12:00", "17:30"]
    now = datetime(2099, 5, 1, 13, 0, tzinfo=UTC)
    assert scheduler.discovery_due(db, settings, now)
    db.execute("INSERT INTO runs (kind, status, trigger, started_at) VALUES ('discovery', 'succeeded', 'schedule', ?)",
               (iso(datetime(2099, 5, 1, 12, 1, tzinfo=UTC)),))
    assert not scheduler.discovery_due(db, settings, now)
    assert scheduler.discovery_due(db, settings, datetime(2099, 5, 1, 17, 31, tzinfo=UTC))


# ---- analytics -------------------------------------------------------------------------------

class MetricsPublisher(RecordingPublisher):
    async def metrics(self, client, post):
        return PostMetrics(likes=10, comments=2, reposts=1)  # Bluesky-like: no impressions


def _published(db, pipeline, settings, hours_ago=25):
    discover_offline(pipeline)
    d = pending_ids(db)[0]
    approval.approve(db, settings, d, "tester")
    run(pipeline.publish(trigger="test"))
    db.execute("UPDATE published_posts SET dry_run = 0, published_at = ?", (iso(utcnow() - timedelta(hours=hours_ago)),))


def test_metrics_are_collected_once_per_age_bucket(db, pipeline, settings):
    _published(db, pipeline, settings)
    pubs = {"bluesky": MetricsPublisher()}
    client = httpx.AsyncClient()
    assert run(analytics.collect(db, pubs, client))["collected"] == 1
    row = db.query_one("SELECT * FROM metrics")
    assert row["age_bucket"] == "24h" and row["likes"] == 10
    assert row["impressions"] is None and row["engagement_rate"] is None  # never invented
    assert run(analytics.collect(db, pubs, client)) == {}


def test_learning_is_bounded_and_explained(db, settings):
    conn = db._connect()
    conn.execute("PRAGMA foreign_keys = OFF")
    for i in range(12):
        cat, likes = ("AI", 100) if i < 6 else ("science", 5)
        conn.execute("INSERT INTO drafts (id, cluster_id, research_id, platform, status, post_text, generated_by, created_at, updated_at) "
                     "VALUES (?, 0, 0, 'bluesky', 'published', 'p', 't', 'x', 'x')", (i + 1,))
        conn.execute("INSERT INTO published_posts (id, job_id, draft_id, platform, post_text, category, source, dry_run, published_at) "
                     "VALUES (?, ?, ?, 'bluesky', 'p', ?, '[\"news_rss\"]', 0, ?)", (i + 1, i + 1, i + 1, cat, iso()))
        conn.execute("INSERT INTO metrics (post_id, collected_at, post_age_minutes, age_bucket, likes, comments, reposts) "
                     "VALUES (?, ?, 1440, '24h', ?, 0, 0)", (i + 1, iso(), likes))
    conn.close()
    changes = analytics.learn(db, settings)
    mult = analytics.current_multipliers(db)
    assert mult[("category", "AI")] == 1 + settings.scoring.learning_max_adjustment  # capped
    assert mult[("category", "science")] >= 1 - settings.scoring.learning_max_adjustment
    assert all("median engagement" in c["reason"] for c in changes)
    assert analytics.learn(db, settings) == []  # nothing new to change
    assert analytics.report(db, settings)["posts_measured"] == 12


def test_redirects_and_links_are_constrained(client, db, pipeline):
    from app.dashboard.routes import safe_url
    assert safe_url("javascript:alert(1)") == "#" and safe_url("https://example.com/a") == "https://example.com/a"
    discover_offline(pipeline)
    login(client)
    t = token(client.get("/drafts").text)
    d = pending_ids(db)[0]
    r = client.post(f"/drafts/{d}/reject", data={"csrf_token": t, "next": "https://evil.example/"}, follow_redirects=False)
    assert r.headers["location"] == "/"
    db.execute("UPDATE drafts SET source_urls_json = ? WHERE id = ?", ('["javascript:alert(1)"]', d))
    assert 'href="javascript:' not in client.get("/drafts?status=all").text
