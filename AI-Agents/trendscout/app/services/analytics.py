"""Performance collection and learning.

Metrics are captured at fixed post ages (1h, 24h, 72h, 7d) so posts are
compared like for like. Missing numbers stay NULL; nothing is estimated.

Learning is deliberately conservative: it adjusts a topic's final score by a
bounded multiplier per category and per source (at most +/-20% by default),
only after enough posts, and never touches the safety filter, relevance or
credibility checks. A boost can therefore re-order safe topics, but it can
never let an unsafe or off-niche topic through.
"""
from __future__ import annotations

import logging
import statistics
from collections import defaultdict
from datetime import timedelta

import httpx

from ..config import Settings
from ..database import Database, dumps, loads
from ..models import PostMetrics
from ..publishers.base import Publisher
from ..timeutil import iso, parse_iso, utcnow

log = logging.getLogger(__name__)
BUCKETS = [("1h", 60), ("24h", 1440), ("72h", 4320), ("7d", 10080)]
LEARNING_BUCKET = "24h"


def due_bucket(post: dict, collected: set[str], now) -> str | None:
    """The latest age bucket the post has reached, if not yet measured. A
    bucket that was missed (the scheduler was down) is skipped, never filled
    with numbers taken at a different age."""
    age = (now - parse_iso(post["published_at"])).total_seconds() / 60
    reached = [name for name, minutes in BUCKETS if age >= minutes]
    if not reached or reached[-1] in collected:
        return None
    return reached[-1]


async def collect(db: Database, publishers: dict[str, Publisher], client: httpx.AsyncClient) -> dict:
    now = utcnow()
    stats = defaultdict(int)
    since = iso(now - timedelta(days=8))
    for post in db.query("SELECT * FROM published_posts WHERE dry_run = 0 AND published_at >= ?", (since,)):
        have = {r["age_bucket"] for r in db.query("SELECT age_bucket FROM metrics WHERE post_id = ?", (post["id"],))}
        bucket = due_bucket(post, have, now)
        if not bucket:
            continue
        publisher = publishers.get(post["platform"])
        try:
            m: PostMetrics | None = await publisher.metrics(client, post) if publisher else None
        except Exception as e:  # noqa: BLE001 - metrics are best effort
            log.info("metrics fetch failed", extra={"post": post["id"], "error": type(e).__name__})
            m = None
        if m is None:
            stats["unavailable"] += 1
            continue
        age = int((now - parse_iso(post["published_at"])).total_seconds() // 60)
        engagement = sum(v or 0 for v in (m.likes, m.comments, m.reposts))
        rate = round(engagement / m.impressions, 5) if m.impressions else None
        db.execute(
            """INSERT INTO metrics (post_id, collected_at, post_age_minutes, age_bucket, impressions, likes, comments,
                   reposts, clicks, engagement_rate, raw_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(post_id, age_bucket) DO NOTHING""",
            (post["id"], iso(m.collected_at), age, bucket, m.impressions, m.likes, m.comments, m.reposts, m.clicks,
             rate, dumps(m.raw)))
        stats["collected"] += 1
    return dict(stats)


def engagement_score(row: dict) -> float:
    return (row["likes"] or 0) + 2 * (row["comments"] or 0) + 2 * (row["reposts"] or 0)


def performance_rows(db: Database, settings: Settings) -> list[dict]:
    rows = db.query(
        """SELECT p.id, p.platform, p.category, p.source, p.published_at, p.post_text, d.structure_json, d.char_count,
                  m.likes, m.comments, m.reposts, m.impressions, m.engagement_rate
           FROM published_posts p JOIN metrics m ON m.post_id = p.id AND m.age_bucket = ?
           JOIN drafts d ON d.id = p.draft_id WHERE p.dry_run = 0""", (LEARNING_BUCKET,))
    by_platform: dict[str, list[float]] = defaultdict(list)
    for r in rows:
        r["score"] = engagement_score(r)
        by_platform[r["platform"]].append(r["score"])
    medians = {p: statistics.median(v) for p, v in by_platform.items()}
    tz = settings.schedule.tz
    for r in rows:
        # Relative to the platform's median, so platforms with different audience sizes compare fairly.
        r["ratio"] = r["score"] / medians[r["platform"]] if medians[r["platform"]] else 1.0
        r["hour"] = parse_iso(r["published_at"]).astimezone(tz).hour
        r["has_link"] = "http" in r["post_text"]
        r["thread"] = bool(loads(r["structure_json"], {}).get("thread_posts"))
        r["sources_list"] = loads(r["source"], []) if (r["source"] or "").startswith("[") else [r["source"]]
    return rows


def current_multipliers(db: Database) -> dict[tuple[str, str], float]:
    rows = db.query("""SELECT dimension, key, multiplier FROM scoring_adjustments a
                       WHERE created_at = (SELECT MAX(created_at) FROM scoring_adjustments b
                                           WHERE b.dimension = a.dimension AND b.key = a.key)""")
    return {(r["dimension"], r["key"]): r["multiplier"] for r in rows}


def learn(db: Database, settings: Settings) -> list[dict]:
    """Recompute bounded multipliers and record why each one changed."""
    sc = settings.scoring
    if not sc.learning_enabled:
        return []
    rows = performance_rows(db, settings)
    current = current_multipliers(db)
    changes = []
    groups: dict[tuple[str, str], list[float]] = defaultdict(list)
    for r in rows:
        if r["category"]:
            groups[("category", r["category"])].append(r["ratio"])
        for s in r["sources_list"]:
            groups[("source", s)].append(r["ratio"])
    for (dim, key), ratios in groups.items():
        if len(ratios) < sc.learning_min_posts:
            continue
        mean = statistics.fmean(ratios)
        target = 1 + 0.5 * (mean - 1)
        new = round(min(1 + sc.learning_max_adjustment, max(1 - sc.learning_max_adjustment, target)), 3)
        old = current.get((dim, key), 1.0)
        if abs(new - old) < 0.02:
            continue
        reason = (f"{len(ratios)} posts in {dim} '{key}' averaged {mean:.2f}x their platform's median engagement at 24h; "
                  f"multiplier {old:.2f} -> {new:.2f} (bounded to ±{sc.learning_max_adjustment:.0%})")
        db.execute("INSERT INTO scoring_adjustments (dimension, key, multiplier, previous, sample_size, reason, created_at) "
                   "VALUES (?, ?, ?, ?, ?, ?, ?)", (dim, key, new, old, len(ratios), reason, iso()))
        changes.append({"dimension": dim, "key": key, "multiplier": new, "reason": reason})
    return changes


def multiplier_for(cluster_category: str | None, sources: list[str], multipliers: dict[tuple[str, str], float]) -> float:
    m = multipliers.get(("category", cluster_category or ""), 1.0)
    src = [multipliers.get(("source", s), 1.0) for s in sources]
    return m * (statistics.fmean(src) if src else 1.0)


def report(db: Database, settings: Settings) -> dict:
    rows = performance_rows(db, settings)

    def summarize(key) -> list[dict]:
        g: dict = defaultdict(list)
        for r in rows:
            g[key(r)].append(r)
        out = [{"key": k, "posts": len(v), "avg_ratio": round(statistics.fmean(x["ratio"] for x in v), 2),
                "avg_likes": round(statistics.fmean((x["likes"] or 0) for x in v), 1)} for k, v in g.items()]
        return sorted(out, key=lambda x: -x["avg_ratio"])

    return {
        "posts_measured": len(rows),
        "by_category": summarize(lambda r: r["category"] or "uncategorised"),
        "by_platform": summarize(lambda r: r["platform"]),
        "by_hour": sorted(summarize(lambda r: f"{r['hour']:02d}:00"), key=lambda x: x["key"]),
        "by_format": summarize(lambda r: ("thread" if r["thread"] else "single") + (" + link" if r["has_link"] else "")),
    }


def writing_insights(db: Database, settings: Settings) -> str:
    """Short performance notes given to writers once there is enough data."""
    rep = report(db, settings)
    if rep["posts_measured"] < settings.scoring.learning_min_posts:
        return ""
    notes = []
    fmt = [f for f in rep["by_format"] if f["posts"] >= 3]
    if len(fmt) >= 2:
        notes.append(f"Best-performing format so far: {fmt[0]['key']} ({fmt[0]['avg_ratio']}x median).")
    hours = [h for h in rep["by_hour"] if h["posts"] >= 3]
    if hours:
        best = max(hours, key=lambda h: h["avg_ratio"])
        notes.append(f"Posts published around {best['key']} have done best ({best['avg_ratio']}x median).")
    if not notes:
        return ""
    return "Performance notes (for style only; never trade accuracy for engagement): " + " ".join(notes)
