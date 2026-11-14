"""Runtime switches stored in the database (so they take effect across the
dashboard, the scheduler and CLI runs at once) and lease-based locks."""
from __future__ import annotations

import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Iterator

from ..config import Settings
from ..database import Database
from ..timeutil import iso, parse_iso, utcnow

PAUSED = "publishing_paused"
PAUSE_REASON = "publishing_pause_reason"
AUTO = "auto_publish_enabled"


def get(db: Database, key: str, default: str | None = None) -> str | None:
    row = db.query_one("SELECT value FROM settings WHERE key = ?", (key,))
    return row["value"] if row else default


def put(db: Database, key: str, value: str, actor: str) -> None:
    db.execute(
        "INSERT INTO settings (key, value, updated_at, updated_by) VALUES (?, ?, ?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at, updated_by = excluded.updated_by",
        (key, value, iso(), actor),
    )


def is_paused(db: Database) -> bool:
    return get(db, PAUSED, "0") == "1"


def pause(db: Database, actor: str, reason: str) -> None:
    put(db, PAUSED, "1", actor)
    put(db, PAUSE_REASON, reason, actor)
    db.audit(actor, "pause_publishing", "settings", PAUSED, reason=reason)


def resume(db: Database, actor: str) -> None:
    put(db, PAUSED, "0", actor)
    put(db, PAUSE_REASON, "", actor)
    db.audit(actor, "resume_publishing", "settings", PAUSED)


def set_auto_publish(db: Database, enabled: bool, actor: str) -> None:
    put(db, AUTO, "1" if enabled else "0", actor)
    db.audit(actor, "auto_publish_" + ("on" if enabled else "off"), "settings", AUTO)


def auto_publish_state(db: Database, settings: Settings) -> tuple[bool, str]:
    p = settings.publishing
    if p.require_human_approval:
        return False, "human approval is required (publishing.require_human_approval = true)"
    if not p.auto_publish:
        return False, "auto publishing is off in the config (publishing.auto_publish = false)"
    if get(db, AUTO, "1") != "1":
        return False, "auto publishing was switched off on the dashboard"
    if is_paused(db):
        return False, "all publishing is paused"
    return True, "reviewer-approved drafts are approved automatically"


def backoff_until(db: Database, platform: str) -> datetime | None:
    return parse_iso(get(db, f"backoff_until:{platform}"))


def set_backoff(db: Database, platform: str, until: datetime) -> None:
    put(db, f"backoff_until:{platform}", iso(until), "system")


# ---- locks ---------------------------------------------------------------------------------------

def acquire(db: Database, name: str, holder: str, ttl: timedelta) -> bool:
    now = utcnow()
    with db.transaction() as conn:
        row = conn.execute("SELECT holder, expires_at FROM locks WHERE name = ?", (name,)).fetchone()
        if row and row["holder"] != holder and (parse_iso(row["expires_at"]) or now) > now:
            return False
        conn.execute(
            "INSERT INTO locks (name, holder, acquired_at, expires_at) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(name) DO UPDATE SET holder = excluded.holder, acquired_at = excluded.acquired_at, "
            "expires_at = excluded.expires_at",
            (name, holder, iso(now), iso(now + ttl)),
        )
    return True


def release(db: Database, name: str, holder: str) -> None:
    db.execute("DELETE FROM locks WHERE name = ? AND holder = ?", (name, holder))


@contextmanager
def locked(db: Database, name: str, ttl: timedelta) -> Iterator[str | None]:
    """Yields the holder id when the lock was taken, or None if another
    process holds it. Expired leases are taken over automatically."""
    holder = f"{name}-{uuid.uuid4().hex[:12]}"
    if not acquire(db, name, holder, ttl):
        yield None
        return
    try:
        yield holder
    finally:
        release(db, name, holder)
