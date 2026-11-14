"""Score topics 0-100 and pick the best ones for the account.

Raw numbers are never compared across sources: a Reddit score and a YouTube
view count are each turned into a percentile within their own source first.
Cheap rules (age, keywords, safety keywords, pointer-only topics) run before
any model call; one batched classification call then scores relevance,
originality and safety for the shortlist only.
"""
from __future__ import annotations

import json
import logging
import re
from collections import defaultdict

from ..config import Settings
from ..llm import LLM, LLMError
from ..models import ClassificationBatch, Cluster, TrendItem
from ..services.deduplication import POINTER_SOURCES
from ..textutil import credibility_for, normalize, sanitize_untrusted
from ..timeutil import hours_since, parse_iso, utcnow
from . import prompts, safety

log = logging.getLogger(__name__)
COMPONENTS = ("popularity", "momentum", "recency", "relevance", "engagement", "credibility", "originality")


def percentiles(values: dict[str, float | None]) -> dict[str, float]:
    """Rank-based percentile in [0, 1]; ties share the average rank. A
    source with a single item gives no comparison, so it scores 0.5."""
    known = {k: v for k, v in values.items() if v is not None}
    out = {k: 0.5 for k in values}
    if len(known) < 2:
        return out
    ordered = sorted(known.items(), key=lambda kv: kv[1])
    i = 0
    while i < len(ordered):
        j = i
        while j + 1 < len(ordered) and ordered[j + 1][1] == ordered[i][1]:
            j += 1
        rank = (i + j) / 2
        for k in range(i, j + 1):
            out[ordered[k][0]] = rank / (len(ordered) - 1)
        i = j + 1
    return out


def _keyword_re(phrase: str) -> re.Pattern:
    p = re.escape(normalize(phrase))
    # Short terms ("ai") must match whole words; longer ones may take suffixes ("research" -> "researchers").
    return re.compile(rf"(?<![a-z0-9]){p}(?![a-z0-9])" if len(phrase) <= 3 else rf"(?<![a-z0-9]){p}")


def keyword_relevance(cluster: Cluster, settings: Settings) -> tuple[float, str | None]:
    text = normalize(" ".join(f"{i.topic} {i.summary} {' '.join(i.keywords)}" for i in cluster.items))
    terms = set(settings.account.keywords) | {c.lower() for c in settings.account.categories}
    hits = [t for t in terms if _keyword_re(t).search(text)]
    best = None
    best_hits = 0
    for cat in settings.account.categories:
        n = len(_keyword_re(cat).findall(text))
        if n > best_hits:
            best, best_hits = cat, n
    return min(1.0, len(hits) / 3), best


def item_signals(items: list[TrendItem], previous: dict[str, tuple[float, str]]) -> dict[str, dict[str, float]]:
    """Per-item popularity, momentum and engagement percentiles, within each source."""
    by_source: dict[str, list[TrendItem]] = defaultdict(list)
    for it in items:
        by_source[it.source].append(it)
    now = utcnow()
    signals: dict[str, dict[str, float]] = {}
    for source, group in by_source.items():
        pop = percentiles({i.id: i.primary_metric for i in group})
        growth: dict[str, float | None] = {}
        engage: dict[str, float | None] = {}
        for i in group:
            prev = previous.get(i.id)
            if prev and i.primary_metric is not None:
                hours = max(0.25, hours_since(parse_iso(prev[1]), now) or 0.25)
                growth[i.id] = (i.primary_metric - prev[0]) / max(prev[0], 1.0) / hours
            elif i.primary_metric is not None:
                age = hours_since(parse_iso(i.published_at), now)
                growth[i.id] = i.primary_metric / max(age, 0.5) if age is not None else None
            else:
                growth[i.id] = None
            m = i.metrics
            if "comments" in m and ("score" in m or "views" in m):
                base = m.get("score") or m.get("views") or 0
                engage[i.id] = (m["comments"] + m.get("likes", 0) * 0.1) / (base + 1)
            else:
                engage[i.id] = None
        mom = percentiles(growth)
        eng = percentiles(engage)
        for i in group:
            signals[i.id] = {"popularity": pop[i.id], "momentum": mom[i.id], "engagement": eng[i.id]}
    return signals


def base_scores(clusters: list[Cluster], items: list[TrendItem], previous: dict[str, tuple[float, str]],
                settings: Settings) -> None:
    sig = item_signals(items, previous)
    half_life = settings.selection.recency_half_life_hours
    for c in clusters:
        s = [sig[i.id] for i in c.items if i.id in sig] or [{"popularity": 0.5, "momentum": 0.5, "engagement": 0.5}]
        coverage = min(1.0, (len(c.sources) - 1) / 3)
        age = hours_since(c.newest())
        relevance, category = keyword_relevance(c, settings)
        story_items = [i for i in c.items if i.source not in POINTER_SOURCES] or c.items
        c.breakdown = {
            "popularity": 0.7 * max(x["popularity"] for x in s) + 0.3 * coverage,
            "momentum": max(x["momentum"] for x in s),
            "recency": 0.5 ** (age / half_life) if age is not None else 0.3,
            "relevance": relevance,
            "engagement": max(x["engagement"] for x in s),
            "credibility": max(credibility_for(i.source_url, settings.source_credibility, i.confidence) for i in story_items),
            "originality": 0.5,
        }
        c.category = category
        c.classification["keyword_relevance"] = round(relevance, 3)
        compute_score(c, settings)


def compute_score(c: Cluster, settings: Settings, multiplier: float = 1.0) -> None:
    w = settings.scoring.weights.normalized()
    raw = sum(w[k] * max(0.0, min(1.0, c.breakdown.get(k, 0.0))) for k in COMPONENTS)
    c.score = round(max(0.0, min(100.0, 100 * raw * multiplier)), 1)


def prefilter(clusters: list[Cluster], settings: Settings) -> None:
    """Free checks that reject topics before any model sees them."""
    sel = settings.selection
    for c in clusters:
        if c.status == "rejected":
            continue
        age = hours_since(c.newest())
        if age is not None and age > sel.max_age_hours:
            c.status, c.rejection_reason = "rejected", f"too old: newest report is {age:.0f}h old (limit {sel.max_age_hours:g}h)"
            continue
        story = [i for i in c.items if i.source not in POINTER_SOURCES]
        has_news_link = any(i.raw.get("news_items") for i in c.items if i.source == "google_trends")
        if not story and not has_news_link:
            c.status, c.rejection_reason = "rejected", "not enough information: only a search term or hashtag, no reporting"
            continue
        if len(c.title.split()) < 2 and len(c.items) == 1:
            c.status, c.rejection_reason = "rejected", "headline too vague to evaluate (a single word)"
            continue
        verdict = safety.evaluate(c, settings)
        c.safety = {"action": verdict.action, "reason": verdict.reason, "flags": verdict.flags, "stage": "rules"}
        if verdict.action == "exclude":
            c.status, c.rejection_reason = "rejected", verdict.reason
        elif verdict.action == "review":
            c.needs_human_review = True


def _candidate_payload(c: Cluster, idx: int) -> dict:
    return {
        "candidate_id": idx,
        "title": sanitize_untrusted(c.title, 300),
        "headlines": [sanitize_untrusted(i.topic, 200) for i in c.items[:6]],
        "summaries": [sanitize_untrusted(i.summary, 300) for i in c.items[:3] if i.summary],
        "sources": c.sources,
        "source_count": len(c.sources),
        "has_article": any(i.source not in POINTER_SOURCES and i.source_url for i in c.items),
        "keyword_relevance": c.classification.get("keyword_relevance", 0),
        "best_category": c.category,
    }


async def classify(shortlist: list[Cluster], settings: Settings, llm: LLM) -> None:
    if not shortlist:
        return
    payload = [_candidate_payload(c, i) for i, c in enumerate(shortlist)]
    prompt = ("Classify these trending topic candidates.\n<untrusted_source>\n"
              + json.dumps([{k: v for k, v in p.items() if k not in ("keyword_relevance", "best_category", "has_article")}
                            for p in payload], ensure_ascii=False, indent=1)
              + "\n</untrusted_source>")
    try:
        result: ClassificationBatch = await llm.structured(
            task="classify", model=settings.ai.classify_model, effort=settings.ai.effort_classify,
            system=prompts.classify_system(settings), prompt=prompt, schema=ClassificationBatch,
            context={"candidates": payload}, max_tokens=8000,
        )
    except LLMError as e:
        # Without classification we cannot vouch for relevance or safety: hold everything back.
        for c in shortlist:
            c.status, c.rejection_reason = "rejected", f"classification unavailable: {e}"
        log.warning("classification failed", extra={"error": str(e)})
        return
    by_id = {item.candidate_id: item for item in result.items}
    for i, c in enumerate(shortlist):
        item = by_id.get(i)
        if item is None:
            c.status, c.rejection_reason = "rejected", "classification returned no result for this topic"
            continue
        c.classification.update(item.model_dump())
        if item.category and item.category.lower() != "none":
            c.category = item.category
        kw = c.breakdown["relevance"]
        c.breakdown["relevance"] = 0.3 * kw + 0.7 * item.relevance / 100
        c.breakdown["engagement"] = 0.4 * c.breakdown["engagement"] + 0.6 * item.engagement_potential / 100
        c.breakdown["originality"] = item.value_add / 100


def apply_classification(c: Cluster, settings: Settings) -> None:
    if c.status == "rejected":
        return
    cls = c.classification
    if "relevance" not in cls:
        return
    verdict = safety.evaluate(c, settings, model_flags=list(cls.get("safety_flags", [])))
    c.safety = {"action": verdict.action, "reason": verdict.reason, "flags": verdict.flags, "stage": "rules+model"}
    if verdict.action == "exclude":
        c.status, c.rejection_reason = "rejected", verdict.reason
    elif verdict.action == "review":
        c.needs_human_review = True
    elif not cls.get("information_sufficient", False):
        c.status, c.rejection_reason = "rejected", f"not enough information to cover responsibly ({cls.get('reason', '')})"
    elif 100 * c.breakdown["relevance"] < settings.selection.min_relevance:
        c.status, c.rejection_reason = "rejected", f"unrelated to the account niche (relevance {100 * c.breakdown['relevance']:.0f})"
    elif cls.get("value_add", 0) < 25:
        c.status, c.rejection_reason = "rejected", f"little original value to add (value_add {cls.get('value_add')})"


def select(clusters: list[Cluster], settings: Settings) -> list[Cluster]:
    live = sorted((c for c in clusters if c.status != "rejected"), key=lambda c: -c.score)
    chosen: list[Cluster] = []
    for c in live:
        if "relevance" not in c.classification:
            c.status, c.rejection_reason = "rejected", "ranked below the classification shortlist"
        elif c.score < settings.selection.min_score:
            c.status, c.rejection_reason = "rejected", f"score {c.score:.0f} below minimum {settings.selection.min_score:g}"
        elif len(chosen) >= settings.selection.topics_per_run:
            c.status, c.rejection_reason = "rejected", f"not in the top {settings.selection.topics_per_run} this run"
        else:
            c.status = "selected"
            chosen.append(c)
    return chosen
