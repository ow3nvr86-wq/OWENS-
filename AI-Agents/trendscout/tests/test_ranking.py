from datetime import timedelta

from app.agents import safety, trend_ranker
from app.models import Cluster, TrendItem
from app.services.deduplication import check_covered, cluster_items, mark_covered
from app.timeutil import iso, utcnow
from tests.conftest import run


def item(source, ext, topic, metric=None, hours=1, url=None, **kw):
    return TrendItem(source=source, external_id=ext, topic=topic, primary_metric=metric,
                     published_at=iso(utcnow() - timedelta(hours=hours)), source_url=url, **kw)


def test_percentiles_are_within_source():
    p = trend_ranker.percentiles({"a": 1, "b": 10, "c": 100, "d": None})
    assert p["a"] == 0 and p["c"] == 1 and p["b"] == 0.5 and p["d"] == 0.5
    assert trend_ranker.percentiles({"only": 5}) == {"only": 0.5}


def test_raw_metrics_are_not_compared_across_sources(settings):
    # 40 Reddit points must not lose to a YouTube video just because views are bigger numbers.
    items = [item("reddit", "r1", "Open source AI model released", 40), item("reddit", "r2", "Minor app update", 2),
             item("youtube", "y1", "Gadget unboxing video", 90_000), item("youtube", "y2", "Big phone review", 2_000_000)]
    sig = trend_ranker.item_signals(items, {})
    assert sig[items[0].id]["popularity"] == 1.0  # top of Reddit
    assert sig[items[2].id]["popularity"] == 0.0  # bottom of YouTube despite 90k views


def test_momentum_uses_previous_observations(settings):
    a, b = item("hacker_news", "1", "Story A", 300), item("hacker_news", "2", "Story B", 300)
    previous = {a.id: (100.0, iso(utcnow() - timedelta(hours=1))), b.id: (290.0, iso(utcnow() - timedelta(hours=1)))}
    sig = trend_ranker.item_signals([a, b], previous)
    assert sig[a.id]["momentum"] > sig[b.id]["momentum"]  # tripled vs barely moved


def test_recency_and_score_bounds(settings):
    fresh = Cluster("k1", "AI software", [item("news_rss", "1", "New AI software tool", 5, hours=1)], ["ai"])
    old = Cluster("k2", "AI software", [item("news_rss", "2", "New AI software tool", 5, hours=60)], ["ai"])
    trend_ranker.base_scores([fresh, old], fresh.items + old.items, {}, settings)
    assert fresh.breakdown["recency"] > old.breakdown["recency"]
    assert 0 <= old.score <= fresh.score <= 100


def test_clustering_merges_related_headlines_and_same_url():
    items = [
        item("news_rss", "1", "Contoso browser to block tracking cookies for all users"),
        item("hacker_news", "2", "Contoso's browser will block third-party cookies by default"),
        item("reddit", "3", "Totally different words here", url="https://example.com/a"),
        item("youtube", "4", "Another title entirely", url="https://www.example.com/a/"),
        item("news_rss", "5", "Local derby ends in dramatic late winner"),
    ]
    clusters = cluster_items(items, 0.45)
    sizes = sorted(len(c.items) for c in clusters)
    assert sizes == [1, 2, 2]


def test_covered_topics_block_repeats_but_allow_meaningful_updates(db, settings):
    first = cluster_items([item("news_rss", "1", "Contoso browser blocks third-party cookies by default")], 0.45)[0]
    first.db_id = None
    mark_covered(db, first)
    again = cluster_items([item("hacker_news", "2", "Contoso browser blocks third-party cookies by default")], 0.45)[0]
    blocked, reason, _ = check_covered(db, again, settings)
    assert blocked and "already covered" in reason

    update = cluster_items([item("news_rss", "3", "Contoso browser cookies blocking delayed after regulator antitrust "
                                                "complaint from advertisers", hours=0)], 0.45)[0]
    update.keywords += ["contoso", "browser", "cookie", "block"]
    blocked, _, covered_id = check_covered(db, update, settings)
    assert not blocked and covered_id and update.classification["new_terms"]


def test_safety_rules(settings):
    def cl(title, hours=5):
        return Cluster("k", title, [item("news_rss", title, title, hours=hours)], [])

    assert safety.evaluate(cl("Factory explosion kills 12"), settings).action == "exclude"
    assert safety.evaluate(cl("CEO accused of fraud"), settings).action == "exclude"
    assert safety.evaluate(cl("Horoscope for techies"), settings).action == "exclude"  # avoid_keywords
    v = safety.evaluate(cl("Analyst price prediction for chip stocks"), settings)
    assert v.action == "review" and "financial" in v.reason
    # The same review-level subject is excluded while it is breaking news.
    assert safety.evaluate(cl("Analyst price prediction for chip stocks", hours=0.5), settings).action == "exclude"
    assert safety.evaluate(cl("New open source browser released"), settings).action == "ok"
    # Model-raised flags go through the same policy table.
    assert safety.evaluate(cl("A neutral headline"), settings, ["hate_harassment"]).action == "exclude"


def test_selection_respects_limits_and_reasons(settings, simulated):
    settings.selection.topics_per_run = 1
    items = [item("news_rss", "1", "New AI software model for smartphones released", 10, url="https://example.com/1"),
             item("news_rss", "2", "Open source AI programming app launches", 9, url="https://example.com/2"),
             item("google_trends", "3", "celebrity name", 100)]
    clusters = cluster_items(items, 0.45)
    trend_ranker.base_scores(clusters, items, {}, settings)
    trend_ranker.prefilter(clusters, settings)
    pointer = next(c for c in clusters if c.items[0].source == "google_trends")
    assert pointer.status == "rejected" and "search term" in pointer.rejection_reason
    live = [c for c in clusters if c.status != "rejected"]
    run(trend_ranker.classify(live, settings, simulated))
    for c in live:
        trend_ranker.apply_classification(c, settings)
    chosen = trend_ranker.select(clusters, settings)
    assert len(chosen) == 1
    assert all(c.rejection_reason for c in clusters if c.status == "rejected")


def test_classification_failure_holds_topics_back(settings):
    from app.llm import UnavailableLLM
    c = Cluster("k", "AI software", [item("news_rss", "1", "AI software", url="https://example.com")], ["ai"])
    run(trend_ranker.classify([c], settings, UnavailableLLM("no key")))
    assert c.status == "rejected" and "no key" in c.rejection_reason
