"""Data shapes shared across modules.

The `*Output` models double as structured-output schemas for Claude: the API
constrains the response to the schema, and Pydantic validates it again here.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from .timeutil import iso, utcnow

SafetyFlag = Literal[
    "tragedy", "unverified_allegation", "personal_information", "medical_misinformation",
    "financial_claims", "political_misinformation", "hate_harassment", "dangerous_challenge",
    "copyright", "engagement_bait", "outside_expertise",
]


class TrendItem(BaseModel):
    """The standard trend object every collector returns."""
    id: str = ""
    source: str
    external_id: str
    topic: str
    source_url: str | None = None
    discovered_at: str = Field(default_factory=iso)
    published_at: str | None = None
    metrics: dict[str, float] = Field(default_factory=dict)
    primary_metric: float | None = None  # the one engagement number this source is ranked by
    summary: str = ""
    keywords: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0, le=1)
    raw: dict[str, Any] = Field(default_factory=dict)

    @field_validator("topic", "summary")
    @classmethod
    def _clean(cls, v: str) -> str:
        return " ".join(v.replace("\x00", "").split())[:1000]

    @field_validator("source_url")
    @classmethod
    def _url(cls, v: str | None) -> str | None:
        if v and not v.lower().startswith(("http://", "https://")):
            return None
        return v

    def model_post_init(self, __context: Any) -> None:
        if not self.id:
            self.id = trend_id(self.source, self.external_id)


def trend_id(source: str, external_id: str) -> str:
    return hashlib.sha256(f"{source}:{external_id}".encode()).hexdigest()[:24]


@dataclass
class Cluster:
    """Related trend items grouped into one underlying topic."""
    key: str
    title: str
    items: list[TrendItem]
    keywords: list[str]
    score: float = 0.0
    breakdown: dict[str, float] = field(default_factory=dict)
    status: str = "candidate"
    rejection_reason: str | None = None
    safety: dict[str, Any] = field(default_factory=dict)
    classification: dict[str, Any] = field(default_factory=dict)
    category: str | None = None
    needs_human_review: bool = False
    covered_topic_id: int | None = None
    db_id: int | None = None

    @property
    def sources(self) -> list[str]:
        return sorted({i.source for i in self.items})

    @property
    def urls(self) -> list[str]:
        seen: list[str] = []
        for i in self.items:
            if i.source_url and i.source_url not in seen:
                seen.append(i.source_url)
        return seen

    def newest(self) -> datetime | None:
        from .timeutil import parse_iso
        dates = [d for i in self.items if (d := parse_iso(i.published_at or i.discovered_at))]
        return max(dates) if dates else None


# ---- Structured outputs requested from Claude ------------------------------------------------

class ClassificationItem(BaseModel):
    candidate_id: int
    relevance: int = Field(description="0-100: fit with the account niche and categories")
    value_add: int = Field(description="0-100: room for the account to add original insight")
    engagement_potential: int = Field(description="0-100: likely interest for the target audience")
    category: str = Field(description="best matching account category, or 'none'")
    safety_flags: list[SafetyFlag]
    information_sufficient: bool
    reason: str


class ClassificationBatch(BaseModel):
    items: list[ClassificationItem]


class ResearchClaim(BaseModel):
    claim: str
    kind: Literal["fact", "opinion", "estimate", "prediction", "speculation"]
    evidence_urls: list[str] = Field(description="URLs from the provided source list that support this claim")
    evidence: str = Field(description="short paraphrase of the supporting passage")
    verified: bool = Field(description="true only if the cited source text directly supports the claim")


class ResearchOutput(BaseModel):
    summary: str
    claims: list[ResearchClaim]
    conflicting_evidence: list[str]
    missing_information: list[str]
    confidence: Literal["high", "medium", "low"]
    angle: str = Field(description="the original, useful insight a post could add")
    suitable: bool
    unsuitable_reason: str


class DraftOutput(BaseModel):
    post_text: str
    thread_posts: list[str] = Field(description="follow-up posts after post_text when a thread is used; else empty")
    carousel_slides: list[str] = Field(description="carousel slide outlines; empty unless the platform uses them")
    script: str = Field(description="short-video script; empty unless the platform is video")
    shot_list: list[str]
    media_brief: str = Field(description="image/graphic/video concept; empty if none is needed")
    hashtags: list[str]
    source_urls: list[str]
    claims: list[str] = Field(description="every factual claim the post makes")
    rationale: str


ReviewDecision = Literal["APPROVED_FOR_HUMAN_REVIEW", "NEEDS_REVISION", "REJECTED"]


class ReviewCheck(BaseModel):
    name: str
    passed: bool
    note: str


class ReviewOutput(BaseModel):
    decision: ReviewDecision
    reasons: list[str]
    revision_instructions: str
    unsupported_claims: list[str]
    checks: list[ReviewCheck]


# ---- Records built from the outputs -----------------------------------------------------------

class SourceDoc(BaseModel):
    url: str
    title: str = ""
    publisher: str = ""
    domain: str = ""
    published_at: str | None = None
    fetched: bool = False         # page body was retrieved, not just a headline
    http_status: int | None = None
    origin: Literal["trend", "page", "web_search"] = "trend"
    text: str = ""                # untrusted extract; never shown as instructions to a model


class Research(BaseModel):
    cache_key: str
    topic: str
    output: ResearchOutput
    sources: list[SourceDoc]
    sufficient: bool
    insufficiency_reason: str = ""
    generated_by: str = ""
    created_at: str = Field(default_factory=iso)

    def verified_claims(self) -> list[ResearchClaim]:
        return [c for c in self.output.claims if c.verified and c.evidence_urls]

    def source_urls(self) -> list[str]:
        return [s.url for s in self.sources]


class Draft(BaseModel):
    platform: str
    cluster_key: str
    post_text: str
    thread_posts: list[str] = Field(default_factory=list)
    carousel_slides: list[str] = Field(default_factory=list)
    script: str = ""
    shot_list: list[str] = Field(default_factory=list)
    media_brief: str = ""
    source_urls: list[str] = Field(default_factory=list)
    hashtags: list[str] = Field(default_factory=list)
    claims: list[str] = Field(default_factory=list)
    rationale: str = ""
    char_count: int = 0
    char_limit: int = 0
    status: str = "drafting"
    generated_by: str = ""

    def structure(self) -> dict[str, Any]:
        return {k: v for k, v in {
            "thread_posts": self.thread_posts, "carousel_slides": self.carousel_slides,
            "script": self.script, "shot_list": self.shot_list,
        }.items() if v}


class Review(BaseModel):
    decision: ReviewDecision
    reasons: list[str]
    revision_instructions: str = ""
    checks: dict[str, Any] = Field(default_factory=dict)
    reviewer: str = ""
    complete: bool = True  # False when the model review could not run


class Outcome(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"              # definitely not published; may be retried if `retryable`
    UNCERTAIN = "uncertain"        # the platform may have accepted it; reconcile before any retry
    NOT_CONFIGURED = "not_configured"


@dataclass
class PublishResult:
    outcome: Outcome
    platform_post_id: str | None = None
    url: str | None = None
    error: str | None = None
    retryable: bool = False
    rate_limited_until: datetime | None = None
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class PostMetrics:
    impressions: int | None = None
    likes: int | None = None
    comments: int | None = None
    reposts: int | None = None
    clicks: int | None = None
    raw: dict[str, Any] = field(default_factory=dict)
    collected_at: datetime = field(default_factory=utcnow)
