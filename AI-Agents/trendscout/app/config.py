"""Configuration: the account profile and behaviour live in a TOML file,
secrets live in environment variables. Both are validated at startup."""
from __future__ import annotations

import os
import re
import tomllib
from datetime import time as dtime
from pathlib import Path
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, Field, field_validator, model_validator

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "config" / "trendscout.toml"

PLATFORMS = ("bluesky", "x", "instagram", "threads", "linkedin", "tiktok")
SAFETY_CATEGORIES = (
    "tragedy", "unverified_allegation", "personal_information", "medical_misinformation",
    "financial_claims", "political_misinformation", "hate_harassment", "dangerous_challenge",
    "copyright", "engagement_bait", "outside_expertise",
)
Action = Literal["exclude", "review", "allow"]
_HHMM = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


def _parse_hhmm(value: str) -> dtime:
    m = _HHMM.match(value)
    if not m:
        raise ValueError(f"time {value!r} must be HH:MM (24-hour)")
    return dtime(int(m.group(1)), int(m.group(2)))


class Account(BaseModel):
    name: str
    niche: str
    audience: str
    voice: str
    personality: str = ""
    categories: list[str] = Field(min_length=1)
    keywords: list[str] = Field(default_factory=list)
    avoid_topics: list[str] = Field(default_factory=list)
    avoid_keywords: list[str] = Field(default_factory=list)
    language: str = "en"
    region: str = "US"


class Schedule(BaseModel):
    timezone: str = "UTC"
    discovery_times: list[str] = Field(default_factory=lambda: ["08:00", "13:00", "18:00"])
    publish_window_start: str = "08:00"
    publish_window_end: str = "21:00"
    publish_check_minutes: int = Field(default=10, ge=1, le=240)
    metrics_check_minutes: int = Field(default=60, ge=5, le=1440)

    @field_validator("timezone")
    @classmethod
    def _tz(cls, v: str) -> str:
        try:
            ZoneInfo(v)
        except (ZoneInfoNotFoundError, ValueError) as e:
            raise ValueError(f"unknown time zone {v!r}") from e
        return v

    @field_validator("discovery_times")
    @classmethod
    def _times(cls, v: list[str]) -> list[str]:
        for t in v:
            _parse_hhmm(t)
        return sorted(set(v))

    @field_validator("publish_window_start", "publish_window_end")
    @classmethod
    def _window(cls, v: str) -> str:
        _parse_hhmm(v)
        return v

    @property
    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.timezone)

    def window(self) -> tuple[dtime, dtime]:
        return _parse_hhmm(self.publish_window_start), _parse_hhmm(self.publish_window_end)

    def discovery_clock_times(self) -> list[dtime]:
        return [_parse_hhmm(t) for t in self.discovery_times]


class Publishing(BaseModel):
    require_human_approval: bool = True
    auto_publish: bool = False
    dry_run: bool = True
    min_minutes_between_posts: int = Field(default=90, ge=0)
    near_duplicate_hours: int = Field(default=48, ge=0)
    near_duplicate_threshold: float = Field(default=0.6, gt=0, le=1)
    error_pause_threshold: int = Field(default=5, ge=1)
    error_window_minutes: int = Field(default=60, ge=1)
    max_attempts: int = Field(default=3, ge=1, le=10)
    lease_minutes: int = Field(default=10, ge=1)


class Platform(BaseModel):
    enabled: bool = False
    daily_limit: int = Field(default=3, ge=0, le=50)
    threads: bool = False  # X/Bluesky: allow multi-post threads
    max_thread_posts: int = Field(default=4, ge=2, le=10)


class Content(BaseModel):
    length: Literal["short", "medium", "long"] = "medium"
    max_hashtags: int = Field(default=2, ge=0, le=10)
    include_links: bool = True
    banned_phrases: list[str] = Field(default_factory=list)


class Selection(BaseModel):
    topics_per_run: int = Field(default=2, ge=1, le=20)
    max_candidates_for_ai: int = Field(default=12, ge=1, le=60)
    min_score: float = Field(default=40, ge=0, le=100)
    cluster_similarity: float = Field(default=0.45, gt=0, le=1)
    covered_similarity: float = Field(default=0.5, gt=0, le=1)
    covered_cooldown_days: int = Field(default=7, ge=0)
    update_min_new_terms: int = Field(default=3, ge=1)
    recency_half_life_hours: float = Field(default=18, gt=0)
    max_age_hours: float = Field(default=72, gt=0)
    min_relevance: float = Field(default=35, ge=0, le=100)


class Weights(BaseModel):
    popularity: float = Field(default=0.20, ge=0)
    momentum: float = Field(default=0.15, ge=0)
    recency: float = Field(default=0.15, ge=0)
    relevance: float = Field(default=0.25, ge=0)
    engagement: float = Field(default=0.10, ge=0)
    credibility: float = Field(default=0.10, ge=0)
    originality: float = Field(default=0.05, ge=0)

    @model_validator(mode="after")
    def _nonzero(self) -> "Weights":
        if sum(self.model_dump().values()) <= 0:
            raise ValueError("at least one scoring weight must be positive")
        return self

    def normalized(self) -> dict[str, float]:
        raw = self.model_dump()
        total = sum(raw.values())
        return {k: v / total for k, v in raw.items()}


class Scoring(BaseModel):
    weights: Weights = Field(default_factory=Weights)
    learning_enabled: bool = True
    learning_min_posts: int = Field(default=5, ge=2)
    learning_max_adjustment: float = Field(default=0.2, ge=0, le=0.5)


def _default_policy() -> dict[str, str]:
    return {
        "tragedy": "exclude", "unverified_allegation": "exclude", "personal_information": "exclude",
        "medical_misinformation": "exclude", "financial_claims": "review",
        "political_misinformation": "exclude", "hate_harassment": "exclude",
        "dangerous_challenge": "exclude", "copyright": "review", "engagement_bait": "exclude",
        "outside_expertise": "exclude",
    }


class Safety(BaseModel):
    policy: dict[str, Action] = Field(default_factory=_default_policy)
    keywords: dict[str, list[str]] = Field(default_factory=dict)
    exclude_breaking_hours: float = Field(default=2, ge=0)

    @field_validator("policy")
    @classmethod
    def _policy(cls, v: dict[str, str]) -> dict[str, str]:
        unknown = set(v) - set(SAFETY_CATEGORIES)
        if unknown:
            raise ValueError(f"unknown safety categories: {sorted(unknown)}")
        merged = _default_policy()
        merged.update(v)
        return merged


class AI(BaseModel):
    model: str = "claude-opus-5-5"
    classify_model: str = "claude-haiku-5-5"
    effort_classify: Literal["low", "medium", "high"] = "low"
    effort_research: Literal["low", "medium", "high", "xhigh", "max"] = "medium"
    effort_write: Literal["low", "medium", "high", "xhigh", "max"] = "medium"
    effort_review: Literal["low", "medium", "high", "xhigh", "max"] = "high"
    use_web_search: bool = True
    web_search_max_uses: int = Field(default=3, ge=0, le=10)
    max_revisions: int = Field(default=2, ge=0, le=5)
    max_source_chars: int = Field(default=12000, ge=1000)
    monthly_budget_usd: float = Field(default=50.0, ge=0)
    request_timeout_seconds: float = Field(default=300, ge=10)


class Feed(BaseModel):
    name: str
    url: str
    credibility: float = Field(default=0.7, ge=0, le=1)
    trusted: bool = False


class Collectors(BaseModel):
    timeout_seconds: float = Field(default=15, gt=0)
    retries: int = Field(default=2, ge=0, le=5)
    hacker_news: dict = Field(default_factory=lambda: {"enabled": True, "lists": ["top", "best"], "limit": 30})
    news_rss: dict = Field(default_factory=lambda: {"enabled": True, "feeds": [], "limit_per_feed": 20})
    google_trends: dict = Field(default_factory=lambda: {"enabled": True, "geo": "US"})
    reddit: dict = Field(default_factory=lambda: {"enabled": True, "subreddits": ["popular"], "limit": 25})
    youtube: dict = Field(default_factory=lambda: {"enabled": True, "region": "US", "category_id": "", "search_queries": [], "limit": 25})
    x_trends: dict = Field(default_factory=lambda: {"enabled": False, "woeid": 1})

    def feeds(self) -> list[Feed]:
        return [Feed(**f) for f in self.news_rss.get("feeds", [])]


class Settings(BaseModel):
    account: Account
    schedule: Schedule = Field(default_factory=Schedule)
    publishing: Publishing = Field(default_factory=Publishing)
    platforms: dict[str, Platform] = Field(default_factory=dict)
    content: Content = Field(default_factory=Content)
    selection: Selection = Field(default_factory=Selection)
    scoring: Scoring = Field(default_factory=Scoring)
    safety: Safety = Field(default_factory=Safety)
    ai: AI = Field(default_factory=AI)
    collectors: Collectors = Field(default_factory=Collectors)
    source_credibility: dict[str, float] = Field(default_factory=dict)

    @field_validator("platforms")
    @classmethod
    def _platforms(cls, v: dict[str, Platform]) -> dict[str, Platform]:
        unknown = set(v) - set(PLATFORMS)
        if unknown:
            raise ValueError(f"unknown platforms: {sorted(unknown)}; supported: {PLATFORMS}")
        for p in PLATFORMS:
            v.setdefault(p, Platform())
        return v

    @property
    def enabled_platforms(self) -> list[str]:
        return [p for p in PLATFORMS if self.platforms[p].enabled]


class Env(BaseModel):
    """Secrets and deployment settings, read from the environment only."""
    database_path: Path
    dashboard_username: str = "admin"
    dashboard_password: str = ""
    dashboard_password_hash: str = ""
    session_secret: str = ""
    trigger_token: str = ""
    cookie_secure: bool = False
    anthropic_api_key: str = ""

    @classmethod
    def load(cls) -> "Env":
        def get(name: str, default: str = "") -> str:
            return os.environ.get(name, default).strip()
        return cls(
            database_path=Path(get("DATABASE_PATH", str(ROOT / "data" / "trendscout.db"))),
            dashboard_username=get("DASHBOARD_USERNAME", "admin"),
            dashboard_password=get("DASHBOARD_PASSWORD"),
            dashboard_password_hash=get("DASHBOARD_PASSWORD_HASH"),
            session_secret=get("SESSION_SECRET"),
            trigger_token=get("TRIGGER_TOKEN"),
            cookie_secure=get("COOKIE_SECURE", "false").lower() in ("1", "true", "yes"),
            anthropic_api_key=get("ANTHROPIC_API_KEY"),
        )


def load_settings(path: Path | str | None = None) -> Settings:
    path = Path(path or os.environ.get("TRENDSCOUT_CONFIG") or DEFAULT_CONFIG)
    if not path.exists():
        raise FileNotFoundError(f"config file not found: {path}")
    with path.open("rb") as f:
        data = tomllib.load(f)
    return Settings.model_validate(data)


def load_dotenv_if_present() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:  # pragma: no cover - dependency is in requirements.txt
        return
    load_dotenv(ROOT / ".env", override=False)


def secret_values() -> list[str]:
    """Every configured secret value, so log output can be scrubbed of them."""
    names = [k for k in os.environ if re.search(r"(KEY|TOKEN|SECRET|PASSWORD)", k)]
    return [v for k in names if len(v := os.environ.get(k, "")) >= 6]
