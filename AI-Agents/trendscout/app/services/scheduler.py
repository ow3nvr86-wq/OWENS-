"""When things run: discovery times, publishing slots, and the long-running
server-side scheduler loop (`python -m app scheduler`)."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta

from ..config import Settings
from ..database import Database
from ..timeutil import UTC, iso, parse_iso, utcnow

log = logging.getLogger(__name__)


def local_day_bounds(settings: Settings, when: datetime) -> tuple[datetime, datetime]:
    tz = settings.schedule.tz
    local = when.astimezone(tz)
    start = local.replace(hour=0, minute=0, second=0, microsecond=0)
    return start.astimezone(UTC), (start + timedelta(days=1)).astimezone(UTC)


def posts_on_day(db: Database, platform: str, settings: Settings, day: datetime, dry_run: bool | None = None) -> int:
    """Posts published that local day in the given mode (simulated posts never use up the real limit)."""
    start, end = local_day_bounds(settings, day)
    mode = settings.publishing.dry_run if dry_run is None else dry_run
    published = db.scalar(
        "SELECT COUNT(*) FROM published_posts WHERE platform = ? AND published_at >= ? AND published_at < ? AND dry_run = ?",
        (platform, iso(start), iso(end), int(mode)))
    return int(published or 0)


def jobs_on_day(db: Database, platform: str, settings: Settings, day: datetime) -> int:
    start, end = local_day_bounds(settings, day)
    return int(db.scalar(
        "SELECT COUNT(*) FROM publish_jobs WHERE platform = ? AND status IN ('queued', 'publishing', 'uncertain') "
        "AND scheduled_at >= ? AND scheduled_at < ?", (platform, iso(start), iso(end))) or 0)


def in_window(settings: Settings, when: datetime) -> bool:
    start, end = settings.schedule.window()
    t = when.astimezone(settings.schedule.tz).time()
    return start <= t <= end if start <= end else (t >= start or t <= end)


def next_window_start(settings: Settings, when: datetime) -> datetime:
    tz = settings.schedule.tz
    start, _ = settings.schedule.window()
    local = when.astimezone(tz)
    candidate = local.replace(hour=start.hour, minute=start.minute, second=0, microsecond=0)
    if candidate <= local:
        candidate += timedelta(days=1)
    return candidate.astimezone(UTC)


def last_post_time(db: Database, platform: str) -> datetime | None:
    a = db.scalar("SELECT MAX(published_at) FROM published_posts WHERE platform = ?", (platform,))
    b = db.scalar("SELECT MAX(scheduled_at) FROM publish_jobs WHERE platform = ? AND status IN ('queued','publishing','uncertain')",
                  (platform,))
    times = [t for t in (parse_iso(a), parse_iso(b)) if t]
    return max(times) if times else None


def next_slot(db: Database, settings: Settings, platform: str, after: datetime | None = None) -> datetime:
    """Earliest time that respects the publishing window, the spacing between
    posts and the platform's daily limit. Posts spread out instead of bunching."""
    now = utcnow()
    t = max(after or now, now)
    spacing = timedelta(minutes=settings.publishing.min_minutes_between_posts)
    last = last_post_time(db, platform)
    if last and t < last + spacing:
        t = last + spacing
    limit = settings.platforms[platform].daily_limit
    for _ in range(30):
        if not in_window(settings, t):
            t = next_window_start(settings, t)
            continue
        if limit and posts_on_day(db, platform, settings, t) + jobs_on_day(db, platform, settings, t) >= limit:
            _, end = local_day_bounds(settings, t)
            t = next_window_start(settings, end - timedelta(minutes=1))
            continue
        return t
    return t


def discovery_due(db: Database, settings: Settings, now: datetime | None = None) -> bool:
    """True when a configured discovery time has passed since the last discovery run."""
    now = now or utcnow()
    tz = settings.schedule.tz
    local_now = now.astimezone(tz)
    last = parse_iso(db.scalar("SELECT MAX(started_at) FROM runs WHERE kind = 'discovery' AND status != 'skipped'"))
    for day_offset in (0, -1):
        day = (local_now + timedelta(days=day_offset)).date()
        for t in sorted(settings.schedule.discovery_clock_times(), reverse=True):
            slot = datetime.combine(day, t, tz).astimezone(UTC)
            if slot <= now:
                return last is None or last < slot
    return False


async def run_forever(make_pipeline, settings: Settings, db: Database, stop: asyncio.Event | None = None) -> None:
    stop = stop or asyncio.Event()
    last_publish = last_metrics = datetime.min.replace(tzinfo=UTC)
    log.info("scheduler started", extra={"timezone": settings.schedule.timezone,
                                         "discovery_times": settings.schedule.discovery_times})
    while not stop.is_set():
        now = utcnow()
        pipeline = make_pipeline()
        try:
            if discovery_due(db, settings, now):
                await pipeline.discover(trigger="schedule")
            if now - last_publish >= timedelta(minutes=settings.schedule.publish_check_minutes):
                last_publish = now
                await pipeline.publish(trigger="schedule")
            if now - last_metrics >= timedelta(minutes=settings.schedule.metrics_check_minutes):
                last_metrics = now
                await pipeline.metrics(trigger="schedule")
        except Exception as e:  # keep the loop alive; the error is logged and stored
            log.exception("scheduler iteration failed")
            db.log_error("scheduler", f"{type(e).__name__}: {e}")
        try:
            await asyncio.wait_for(stop.wait(), timeout=60)
        except asyncio.TimeoutError:
            pass
