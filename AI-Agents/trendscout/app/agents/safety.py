"""Editorial safety filter.

Two layers: configurable keyword rules (free, run on every topic) and the
categories the classification model flags. Both feed the same policy table:
exclude, review (keep, but a person must look) or allow. Every exclusion
carries a reason that is stored and shown on the dashboard.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..config import Settings
from ..models import Cluster
from ..textutil import normalize
from ..timeutil import hours_since

LABELS = {
    "tragedy": "tragedy or breaking emergency",
    "unverified_allegation": "unverified allegation",
    "personal_information": "sensitive personal information",
    "medical_misinformation": "possible medical misinformation",
    "financial_claims": "financial claims",
    "political_misinformation": "possible political misinformation",
    "hate_harassment": "hate or harassment",
    "dangerous_challenge": "dangerous challenge",
    "copyright": "copyright concern",
    "engagement_bait": "misleading engagement bait",
    "outside_expertise": "outside the account's expertise",
}


@dataclass
class SafetyVerdict:
    action: str                        # ok | review | exclude
    reason: str = ""
    flags: dict[str, list[str]] = field(default_factory=dict)


def _phrase_re(phrase: str) -> re.Pattern:
    return re.compile(r"(?<![a-z0-9])" + re.escape(normalize(phrase)) + r"(?![a-z0-9])")


def cluster_text(cluster: Cluster) -> str:
    return normalize(" ".join(f"{i.topic} {i.summary}" for i in cluster.items))


def rule_flags(text: str, settings: Settings) -> dict[str, list[str]]:
    flags: dict[str, list[str]] = {}
    for category, phrases in settings.safety.keywords.items():
        hits = [p for p in phrases if _phrase_re(p).search(text)]
        if hits:
            flags[category] = hits
    return flags


def avoided(text: str, settings: Settings) -> str | None:
    for phrase in settings.account.avoid_keywords + settings.account.avoid_topics:
        if _phrase_re(phrase).search(text):
            return phrase
    return None


def evaluate(cluster: Cluster, settings: Settings, model_flags: list[str] | None = None) -> SafetyVerdict:
    text = cluster_text(cluster)
    flags = rule_flags(text, settings)
    for f in model_flags or []:
        flags.setdefault(f, []).append("model")

    hit = avoided(text, settings)
    if hit:
        return SafetyVerdict("exclude", f"matches a topic to avoid: {hit!r}", flags)

    policy = settings.safety.policy
    excluded = [c for c in flags if policy.get(c) == "exclude"]
    if excluded:
        detail = ", ".join(f"{LABELS.get(c, c)} ({', '.join(flags[c][:3])})" for c in excluded)
        return SafetyVerdict("exclude", f"editorial policy excludes: {detail}", flags)

    review = [c for c in flags if policy.get(c) == "review"]
    if review:
        age = hours_since(cluster.newest())
        if age is not None and age < settings.safety.exclude_breaking_hours:
            return SafetyVerdict(
                "exclude", f"sensitive subject ({', '.join(LABELS.get(c, c) for c in review)}) in breaking news "
                           f"under {settings.safety.exclude_breaking_hours:g}h old", flags)
        return SafetyVerdict("review", "needs human review: " + ", ".join(LABELS.get(c, c) for c in review), flags)
    return SafetyVerdict("ok", "", flags)
