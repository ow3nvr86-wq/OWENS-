"""Persist trend items, group related headlines into topics, and decide
whether a topic was already covered.

Duplicate prevention lives in the database (trends, covered_topics,
publish_jobs), never in memory, so it survives restarts and separate
scheduled processes.
"""
from __future__ import annotations

from collections import Counter
from datetime import timedelta
from urllib.parse import urlsplit, urlunsplit

from ..config import Settings
from ..database import Database, dumps, loads
from ..models import Cluster, TrendItem
from ..textutil import jaccard, overlap, stable_hash, tokens
from ..timeutil import iso, parse_iso, utcnow

# Sources whose items are pointers (a search term, a hashtag) rather than stories.
POINTER_SOURCES = {"google_trends", "x_trends"}
TITLE_PREFERENCE = {"news_rss": 0, "hacker_news": 1, "reddit": 2, "youtube": 3, "google_trends": 4, "x_trends": 5}


def canonical_url(url: str | None) -> str | None:
    if not url:
        return None
    parts = urlsplit(url)
    host = (parts.hostname or "").lower().removeprefix("www.")
    return urlunsplit((parts.scheme.lower(), host, parts.path.rstrip("/"), "", ""))


def item_terms(item: TrendItem) -> set[str]:
    terms = set(tokens(item.topic)) | set(item.keywords)
    if item.source == "google_trends":
        for n in item.raw.get("news_items", [])[:2]:
            terms |= set(tokens(n.get("title", "")))
    return terms


def _similar(a: set[str], b: set[str]) -> float:
    score = jaccard(a, b)
    if min(len(a), len(b)) >= 3:
        score = max(score, 0.85 * overlap(a, b))
    return score


def cluster_items(items: list[TrendItem], threshold: float) -> list[Cluster]:
    """Single-link clustering: two items join when their terms are similar
    enough or they point at the same article."""
    n = len(items)
    parent = list(range(n))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i: int, j: int) -> None:
        parent[find(i)] = find(j)

    terms = [item_terms(i) for i in items]
    urls = [canonical_url(i.source_url) for i in items]
    for i in range(n):
        for j in range(i + 1, n):
            if (urls[i] and urls[i] == urls[j]) or _similar(terms[i], terms[j]) >= threshold:
                union(i, j)

    groups: dict[int, list[int]] = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)

    clusters: list[Cluster] = []
    for members in groups.values():
        group = [items[i] for i in members]
        counts = Counter(t for i in members for t in terms[i])
        kw = [w for w, _ in counts.most_common(12)]
        title_item = min(group, key=lambda it: (TITLE_PREFERENCE.get(it.source, 9), -len(it.topic)))
        key = stable_hash(*sorted(kw[:6]))
        clusters.append(Cluster(key=key, title=title_item.topic, items=group, keywords=kw))
    return clusters


def store_items(db: Database, items: list[TrendItem], run_id: int) -> None:
    now = iso()
    with db.transaction() as conn:
        for it in items:
            conn.execute(
                """INSERT INTO trends (id, source, external_id, topic, url, summary, keywords_json, metrics_json,
                       confidence, raw_json, published_at, first_seen_at, last_seen_at, last_run_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(id) DO UPDATE SET topic=excluded.topic, url=excluded.url, summary=excluded.summary,
                       keywords_json=excluded.keywords_json, metrics_json=excluded.metrics_json,
                       raw_json=excluded.raw_json, last_seen_at=excluded.last_seen_at, last_run_id=excluded.last_run_id""",
                (it.id, it.source, it.external_id, it.topic, it.source_url, it.summary, dumps(it.keywords),
                 dumps(it.metrics), it.confidence, dumps(it.raw), it.published_at, now, now, run_id),
            )
            conn.execute(
                "INSERT INTO trend_observations (trend_id, run_id, observed_at, metric, metrics_json) VALUES (?, ?, ?, ?, ?)",
                (it.id, run_id, now, it.primary_metric, dumps(it.metrics)),
            )


def previous_observations(db: Database, trend_ids: list[str], run_id: int) -> dict[str, tuple[float, str]]:
    """The most recent earlier observation of each item, for momentum."""
    if not trend_ids:
        return {}
    marks = ",".join("?" * len(trend_ids))
    rows = db.query(
        f"""SELECT trend_id, metric, observed_at FROM trend_observations
            WHERE trend_id IN ({marks}) AND (run_id IS NULL OR run_id != ?) AND metric IS NOT NULL
            ORDER BY observed_at DESC""",
        [*trend_ids, run_id],
    )
    out: dict[str, tuple[float, str]] = {}
    for r in rows:
        out.setdefault(r["trend_id"], (r["metric"], r["observed_at"]))
    return out


def check_covered(db: Database, cluster: Cluster, settings: Settings) -> tuple[bool, str | None, int | None]:
    """Returns (blocked, reason, covered_topic_id). A covered topic becomes
    eligible again when there is a meaningful update: enough new terms and
    reporting newer than the last coverage."""
    sel = settings.selection
    since = iso(utcnow() - timedelta(days=sel.covered_cooldown_days))
    rows = db.query("SELECT * FROM covered_topics WHERE last_covered_at >= ? ORDER BY last_covered_at DESC", (since,))
    mine = set(cluster.keywords)
    for row in rows:
        theirs = set(loads(row["keywords_json"], []))
        if _similar(mine, theirs) < sel.covered_similarity:
            continue
        new_terms = mine - theirs
        newest = cluster.newest()
        last = parse_iso(row["last_covered_at"])
        if len(new_terms) >= sel.update_min_new_terms and newest and last and newest > last:
            cluster.classification["update_of"] = row["id"]
            cluster.classification["new_terms"] = sorted(new_terms)[:10]
            return False, None, row["id"]
        return True, f"already covered on {row['last_covered_at'][:10]} (topic #{row['id']}: {row['title'][:80]})", row["id"]
    return False, None, None


def mark_covered(db: Database, cluster: Cluster) -> int:
    now = iso()
    if cluster.covered_topic_id:
        db.execute(
            "UPDATE covered_topics SET last_covered_at = ?, update_count = update_count + 1, keywords_json = ?, cluster_id = ? WHERE id = ?",
            (now, dumps(sorted(set(cluster.keywords))), cluster.db_id, cluster.covered_topic_id),
        )
        return cluster.covered_topic_id
    return db.execute(
        """INSERT INTO covered_topics (cluster_key, title, keywords_json, cluster_id, first_covered_at, last_covered_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (cluster.key, cluster.title, dumps(cluster.keywords), cluster.db_id, now, now),
    )

