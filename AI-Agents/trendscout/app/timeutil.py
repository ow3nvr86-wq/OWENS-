"""One timestamp format everywhere: ISO-8601 UTC with microseconds and a Z.
Strings in this format sort chronologically, which the SQL relies on."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

UTC = timezone.utc


def utcnow() -> datetime:
    return datetime.now(UTC)


def iso(dt: datetime | None = None) -> str:
    dt = dt or utcnow()
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def parse_any(value: str | int | float | None) -> datetime | None:
    """Parse the date formats feeds and APIs actually send."""
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), UTC)
    dt = parse_iso(value)
    if dt:
        return dt
    try:
        dt = parsedate_to_datetime(value)
    except (TypeError, ValueError, IndexError):
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def ago(**kwargs: float) -> str:
    return iso(utcnow() - timedelta(**kwargs))


def hours_since(dt: datetime | None, now: datetime | None = None) -> float | None:
    if dt is None:
        return None
    return max(0.0, ((now or utcnow()) - dt).total_seconds() / 3600)
