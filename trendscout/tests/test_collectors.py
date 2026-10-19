import httpx
import pytest

from app.collectors.base import CollectorContext, NotConfigured, all_collectors, run_collectors
from app.collectors.google_trends import GoogleTrendsCollector, parse_traffic
from app.collectors.hacker_news import HackerNewsCollector
from app.collectors.news_rss import NewsRSSCollector
from app.collectors.reddit import RedditCollector
from app.collectors.x_trends import XTrendsCollector
from app.collectors.youtube import YouTubeCollector
from app.fixtures import OFFLINE_ENV, handler, offline_transport
from app.http import HTTPFailure, get_with_retries
from tests.conftest import run


def ctx(settings, transport=None, env=None):
    return CollectorContext(settings, httpx.AsyncClient(transport=transport or offline_transport()),
                            OFFLINE_ENV if env is None else env)


def test_hacker_news(settings):
    items = run(HackerNewsCollector().collect(ctx(settings)))
    by_id = {i.external_id: i for i in items}
    assert "9001" in by_id and by_id["9001"].metrics == {"score": 640.0, "comments": 210.0}
    assert by_id["9005"].source_url.startswith("https://news.ycombinator.com/item")  # Ask HN has no link
    assert all(i.id and i.discovered_at and i.published_at for i in items)


def test_rss_handles_rss_and_atom_and_a_broken_feed(settings):
    items = run(NewsRSSCollector().collect(ctx(settings)))
    publishers = {i.raw["publisher"] for i in items}
    assert {"BBC Technology", "Ars Technica"} <= publishers  # RSS 2.0 and Atom fixtures
    assert all(i.source_url.startswith("https://") for i in items)
    assert all(i.published_at for i in items)


def test_google_trends(settings):
    items = run(GoogleTrendsCollector().collect(ctx(settings)))
    pi = next(i for i in items if i.topic == "raspberry pi ai model")
    assert pi.metrics["approx_traffic"] == 50000
    assert pi.source_url == "https://example.com/northwind-open-model-news"
    assert pi.raw["region"] == "US"
    assert parse_traffic("2M+") == 2_000_000 and parse_traffic("1,000+") == 1000 and parse_traffic(None) is None


def test_reddit_skips_nsfw_and_stickied(settings):
    items = run(RedditCollector().collect(ctx(settings)))
    titles = [i.topic for i in items]
    assert not any("NSFW" in t or "Weekly discussion" in t for t in titles)
    assert items[0].metrics["velocity"] > 0


def test_youtube(settings):
    items = run(YouTubeCollector().collect(ctx(settings)))
    assert {i.metrics["views"] for i in items} == {820000.0, 120000.0}


@pytest.mark.parametrize("collector", [RedditCollector(), YouTubeCollector(), XTrendsCollector()])
def test_credentialed_sources_skip_cleanly_without_keys(settings, collector):
    with pytest.raises(NotConfigured):
        run(collector.collect(ctx(settings, env={})))


def test_x_trends_reports_access_tier_problem(settings):
    t = httpx.MockTransport(lambda r: httpx.Response(403, json={"title": "Forbidden"}))
    with pytest.raises(NotConfigured, match="access"):
        run(XTrendsCollector().collect(ctx(settings, transport=t)))


def test_one_failing_source_does_not_stop_the_others(settings):
    def flaky(request):
        if request.url.host == "hacker-news.firebaseio.com":
            raise httpx.ConnectError("boom")
        return handler(request)

    settings.collectors.retries = 0
    items, reports = run(run_collectors(all_collectors(), ctx(settings, transport=httpx.MockTransport(flaky))))
    status = {r.name: r.status for r in reports}
    assert status["hacker_news"] == "failed"
    assert status["news_rss"] == "ok" and status["google_trends"] == "ok"
    assert items and not any(i.source == "hacker_news" for i in items)


def test_retries_transient_errors_then_succeeds(monkeypatch):
    calls = []

    def flaky(request):
        calls.append(1)
        return httpx.Response(503) if len(calls) < 3 else httpx.Response(200, json={"ok": True})

    async def nosleep(_):
        return None

    monkeypatch.setattr("app.http.asyncio.sleep", nosleep)
    client = httpx.AsyncClient(transport=httpx.MockTransport(flaky))
    resp = run(get_with_retries(client, "https://example.com/x", retries=2))
    assert resp.json() == {"ok": True} and len(calls) == 3


def test_rate_limit_waits_for_retry_after(monkeypatch):
    waits = []

    async def fake_sleep(s):
        waits.append(s)

    monkeypatch.setattr("app.http.asyncio.sleep", fake_sleep)
    responses = [httpx.Response(429, headers={"retry-after": "7"}), httpx.Response(200, json={})]
    client = httpx.AsyncClient(transport=httpx.MockTransport(lambda r: responses.pop(0)))
    run(get_with_retries(client, "https://example.com/x", retries=1))
    assert waits == [7.0]


def test_client_errors_are_not_retried():
    calls = []
    client = httpx.AsyncClient(transport=httpx.MockTransport(lambda r: calls.append(1) or httpx.Response(404)))
    with pytest.raises(HTTPFailure) as e:
        run(get_with_retries(client, "https://example.com/x?key=secret", retries=3))
    assert e.value.status == 404 and len(calls) == 1
    assert "secret" not in str(e.value)  # query strings (API keys) are not logged
