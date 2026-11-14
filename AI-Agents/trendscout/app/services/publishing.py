"""The publishing queue.

Safety properties, in order of importance:
1. Only jobs created by `approval.approve` exist, and a job is re-checked
   against its draft's status right before publishing.
2. One publishing run at a time (a DB lease lock), and every job is claimed
   with an atomic compare-and-set (queued -> publishing) before any network
   call, so two processes can never submit the same job.
3. A job is marked `publishing` in the database before the request goes out.
   If the process dies mid-request, the expired lease turns it into
   `uncertain`, never back into `queued`.
4. Uncertain jobs are reconciled with the platform; they are retried only
   when the platform confirms the post does not exist, or a person says so.
5. The kill switch is checked before every job, and too many failures in a
   short window pause publishing automatically.
"""
from __future__ import annotations

import logging
from collections import Counter
from datetime import datetime, timedelta

import httpx

from ..config import Settings
from ..database import Database
from ..models import Outcome, PublishResult
from ..publishers.base import DryRunPublisher, Publisher
from ..textutil import similarity
from ..timeutil import iso, parse_iso, utcnow
from . import controls, scheduler

log = logging.getLogger(__name__)


def recover_stale(db: Database, now: datetime) -> int:
    return db.execute(
        "UPDATE publish_jobs SET status = 'uncertain', last_error = 'process stopped while publishing; needs reconciliation', "
        "updated_at = ? WHERE status = 'publishing' AND lease_expires_at < ?", (iso(now), iso(now)))


def claim(db: Database, job_id: int, holder: str, lease: timedelta, now: datetime) -> dict | None:
    with db.transaction() as conn:
        n = conn.execute(
            "UPDATE publish_jobs SET status = 'publishing', claimed_by = ?, lease_expires_at = ?, attempts = attempts + 1, "
            "updated_at = ? WHERE id = ? AND status = 'queued'",
            (holder, iso(now + lease), iso(now), job_id)).rowcount
        if n != 1:
            return None
        return dict(conn.execute("SELECT * FROM publish_jobs WHERE id = ?", (job_id,)).fetchone())


def _defer(db: Database, job_id: int, when: datetime, reason: str) -> None:
    db.execute("UPDATE publish_jobs SET scheduled_at = ?, last_error = ?, updated_at = ? WHERE id = ? AND status = 'queued'",
               (iso(when), f"deferred: {reason}", iso(), job_id))


def _hold(db: Database, job_id: int, reason: str) -> None:
    db.execute("UPDATE publish_jobs SET status = 'held', last_error = ?, updated_at = ? WHERE id = ? AND status = 'queued'",
               (reason, iso(), job_id))


def gate(db: Database, settings: Settings, job: dict, draft: dict, now: datetime, dry_run: bool) -> tuple[str, object, str] | None:
    """Checks that can postpone or hold a job. None means go ahead."""
    platform = job["platform"]
    if not settings.platforms[platform].enabled:
        return "hold", None, f"{platform} is disabled in the config"
    until = controls.backoff_until(db, platform)
    if until and until > now:
        return "defer", until, f"{platform} rate limit until {iso(until)}"
    if not scheduler.in_window(settings, now):
        return "defer", scheduler.next_window_start(settings, now), "outside the publishing window"
    limit = settings.platforms[platform].daily_limit
    if limit and scheduler.posts_on_day(db, platform, settings, now, dry_run) >= limit:
        _, end = scheduler.local_day_bounds(settings, now)
        return "defer", scheduler.next_window_start(settings, end - timedelta(minutes=1)), f"daily limit of {limit} reached"
    last = parse_iso(db.scalar("SELECT MAX(published_at) FROM published_posts WHERE platform = ? AND dry_run = ?",
                               (platform, int(dry_run))))
    spacing = timedelta(minutes=settings.publishing.min_minutes_between_posts)
    if last and now < last + spacing:
        return "defer", last + spacing, "too soon after the previous post"
    since = iso(now - timedelta(hours=settings.publishing.near_duplicate_hours))
    for p in db.query("SELECT post_text FROM published_posts WHERE platform = ? AND published_at >= ? AND draft_id != ?",
                      (platform, since, draft["id"])):
        if similarity(p["post_text"], draft["post_text"]) >= settings.publishing.near_duplicate_threshold:
            return "hold", None, "near-identical to a post published recently"
    return None


def circuit_open(db: Database, settings: Settings, now: datetime) -> bool:
    since = iso(now - timedelta(minutes=settings.publishing.error_window_minutes))
    n = db.scalar("SELECT COUNT(*) FROM error_log WHERE component = 'publishing' AND ts >= ?", (since,)) or 0
    return n >= settings.publishing.error_pause_threshold


def record_success(db: Database, job: dict, draft: dict, result: PublishResult, dry_run: bool, actor: str) -> None:
    now = iso()
    cluster = db.query_one("SELECT category, sources_json FROM clusters WHERE id = ?", (draft["cluster_id"],)) or {}
    with db.transaction() as conn:
        n = conn.execute(
            "UPDATE publish_jobs SET status = 'published', lease_expires_at = NULL, last_error = NULL, "
            "platform_ref = COALESCE(?, platform_ref), updated_at = ? WHERE id = ? AND status IN ('publishing', 'uncertain')",
            (result.platform_post_id, now, job["id"])).rowcount
        if not n:
            return
        conn.execute(
            """INSERT INTO published_posts (job_id, draft_id, platform, platform_post_id, url, post_text, category, source,
                   dry_run, published_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(job_id) DO NOTHING""",
            (job["id"], draft["id"], job["platform"], result.platform_post_id, result.url, draft["post_text"],
             cluster.get("category"), (cluster.get("sources_json") or "[]"), int(dry_run), now))
        conn.execute("UPDATE drafts SET status = 'published', updated_at = ? WHERE id = ?", (now, draft["id"]))
    db.audit(actor, "published" if not dry_run else "published_dry_run", "publish_job", job["id"],
             platform=job["platform"], url=result.url, post_id=result.platform_post_id,
             reconciled=bool(result.detail.get("reconciled")))


def record_failure(db: Database, settings: Settings, job: dict, result: PublishResult, now: datetime) -> str:
    attempts = job["attempts"]
    if result.outcome == Outcome.NOT_CONFIGURED:
        db.execute("UPDATE publish_jobs SET status = 'held', attempts = MAX(0, attempts - 1), last_error = ?, "
                   "lease_expires_at = NULL, updated_at = ? WHERE id = ?", (result.error, iso(now), job["id"]))
        return "held"
    if result.outcome == Outcome.UNCERTAIN:
        db.execute("UPDATE publish_jobs SET status = 'uncertain', last_error = ?, platform_ref = COALESCE(?, platform_ref), "
                   "updated_at = ? WHERE id = ?", (result.error, result.platform_post_id, iso(now), job["id"]))
        db.log_error("publishing", f"job {job['id']} uncertain: {result.error}")
        return "uncertain"
    if result.rate_limited_until:
        controls.set_backoff(db, job["platform"], result.rate_limited_until)
        db.execute("UPDATE publish_jobs SET status = 'queued', attempts = MAX(0, attempts - 1), scheduled_at = ?, "
                   "last_error = ?, lease_expires_at = NULL, updated_at = ? WHERE id = ?",
                   (iso(result.rate_limited_until), result.error, iso(now), job["id"]))
        return "deferred"
    db.log_error("publishing", f"job {job['id']} failed: {result.error}")
    if result.retryable and attempts < settings.publishing.max_attempts:
        retry_at = now + timedelta(minutes=5 * 2 ** (attempts - 1))
        db.execute("UPDATE publish_jobs SET status = 'queued', scheduled_at = ?, last_error = ?, lease_expires_at = NULL, "
                   "updated_at = ? WHERE id = ?", (iso(retry_at), result.error, iso(now), job["id"]))
        return "retry"
    db.execute("UPDATE publish_jobs SET status = 'failed', last_error = ?, lease_expires_at = NULL, updated_at = ? WHERE id = ?",
               (result.error, iso(now), job["id"]))
    return "failed"


async def reconcile_uncertain(db: Database, settings: Settings, publishers: dict[str, Publisher],
                              client: httpx.AsyncClient, now: datetime) -> Counter:
    stats: Counter = Counter()
    for job in db.query("SELECT * FROM publish_jobs WHERE status = 'uncertain' ORDER BY updated_at"):
        draft = db.query_one("SELECT * FROM drafts WHERE id = ?", (job["draft_id"],))
        publisher = publishers.get(job["platform"])
        if not draft or not publisher:
            continue
        try:
            result = await publisher.reconcile(client, job, draft)
        except Exception as e:  # noqa: BLE001 - reconciliation must never crash the run
            log.warning("reconcile failed", extra={"job": job["id"], "error": type(e).__name__})
            result = None
        if result is None:
            stats["still_uncertain"] += 1
        elif result.outcome == Outcome.SUCCESS:
            record_success(db, job, draft, result, dry_run=False, actor="system:reconcile")
            stats["reconciled_published"] += 1
        elif result.outcome == Outcome.FAILED:
            status = "queued" if job["attempts"] < settings.publishing.max_attempts else "failed"
            db.execute("UPDATE publish_jobs SET status = ?, scheduled_at = ?, last_error = ?, updated_at = ? "
                       "WHERE id = ? AND status = 'uncertain'",
                       (status, iso(now), "confirmed not posted; " + (result.error or ""), iso(now), job["id"]))
            stats[f"reconciled_{status}"] += 1
    return stats


async def publish_due(db: Database, settings: Settings, publishers: dict[str, Publisher], client: httpx.AsyncClient,
                      *, dry_run: bool, now: datetime | None = None) -> dict:
    now = now or utcnow()
    stats: Counter = Counter()
    if controls.is_paused(db):
        return {"skipped": "publishing is paused"}
    lease = timedelta(minutes=settings.publishing.lease_minutes)
    with controls.locked(db, "publishing", lease) as holder:
        if holder is None:
            return {"skipped": "another publishing run is in progress"}
        stats["recovered_stale"] = recover_stale(db, now)
        if not dry_run:
            stats.update(await reconcile_uncertain(db, settings, publishers, client, now))
        due = db.query("SELECT * FROM publish_jobs WHERE status = 'queued' AND scheduled_at <= ? ORDER BY scheduled_at, id",
                       (iso(now),))
        for job in due:
            now = max(now, utcnow())  # publishing takes time; gates compare against the real clock
            if controls.is_paused(db):
                stats["stopped_paused"] += 1
                break
            if circuit_open(db, settings, now):
                controls.pause(db, "system", f"automatic pause: {settings.publishing.error_pause_threshold} or more "
                                             f"publishing errors in {settings.publishing.error_window_minutes} minutes")
                stats["circuit_breaker"] += 1
                break
            draft = db.query_one("SELECT * FROM drafts WHERE id = ?", (job["draft_id"],))
            if not draft or draft["status"] != "approved":
                db.execute("UPDATE publish_jobs SET status = 'cancelled', last_error = 'draft no longer approved', "
                           "updated_at = ? WHERE id = ? AND status = 'queued'", (iso(now), job["id"]))
                stats["cancelled"] += 1
                continue
            decision = gate(db, settings, job, draft, now, dry_run)
            if decision:
                kind, when, reason = decision
                if kind == "defer":
                    _defer(db, job["id"], when, reason)
                    stats["deferred"] += 1
                else:
                    _hold(db, job["id"], reason)
                    stats["held"] += 1
                continue
            claimed = claim(db, job["id"], holder, lease, now)
            if not claimed:
                stats["lost_claim"] += 1
                continue
            publisher = DryRunPublisher(job["platform"]) if dry_run else publishers[job["platform"]]
            try:
                result = await publisher.publish(client, claimed, draft)
            except Exception as e:  # noqa: BLE001 - an unknown error may have happened after sending
                result = PublishResult(Outcome.UNCERTAIN, error=f"unexpected {type(e).__name__}: {e}")
            if result.outcome == Outcome.SUCCESS:
                record_success(db, claimed, draft, result, dry_run, actor="system:publisher")
                stats["published"] += 1
            else:
                stats[record_failure(db, settings, claimed, result, utcnow())] += 1
    return {k: v for k, v in stats.items() if v}


# ---- manual resolution from the dashboard --------------------------------------------------------

class QueueError(Exception):
    pass


def _job(db: Database, job_id: int) -> dict:
    job = db.query_one("SELECT * FROM publish_jobs WHERE id = ?", (job_id,))
    if not job:
        raise QueueError(f"job {job_id} not found")
    return job


def mark_published(db: Database, job_id: int, url: str, actor: str) -> None:
    job = _job(db, job_id)
    if job["status"] not in ("uncertain", "failed"):
        raise QueueError("only uncertain or failed jobs can be marked as published")
    draft = db.query_one("SELECT * FROM drafts WHERE id = ?", (job["draft_id"],))
    db.execute("UPDATE publish_jobs SET status = 'uncertain' WHERE id = ?", (job_id,))
    record_success(db, job, draft, PublishResult(Outcome.SUCCESS, url=url or None, detail={"manual": True}),
                   dry_run=False, actor=actor)


def retry(db: Database, job_id: int, actor: str, confirmed_not_posted: bool = False) -> None:
    job = _job(db, job_id)
    if job["status"] == "uncertain" and not confirmed_not_posted:
        raise QueueError("confirm on the platform that the post does not exist before retrying an uncertain job")
    if job["status"] not in ("failed", "held", "uncertain", "cancelled"):
        raise QueueError(f"a {job['status']} job cannot be retried")
    draft = db.query_one("SELECT status FROM drafts WHERE id = ?", (job["draft_id"],))
    if not draft or draft["status"] != "approved":
        raise QueueError("the draft is no longer approved; approve it again first")
    db.execute("UPDATE publish_jobs SET status = 'queued', attempts = 0, scheduled_at = ?, last_error = NULL, "
               "updated_at = ? WHERE id = ?", (iso(), iso(), job_id))
    db.audit(actor, "retry_job", "publish_job", job_id, confirmed_not_posted=confirmed_not_posted)


def cancel(db: Database, job_id: int, actor: str) -> None:
    job = _job(db, job_id)
    if job["status"] in ("publishing", "published"):
        raise QueueError(f"a {job['status']} job cannot be cancelled")
    db.execute("UPDATE publish_jobs SET status = 'cancelled', updated_at = ? WHERE id = ?", (iso(), job_id))
    db.execute("UPDATE drafts SET status = 'pending_approval', updated_at = ? WHERE id = ? AND status = 'approved'",
               (iso(), job["draft_id"]))
    db.audit(actor, "cancel_job", "publish_job", job_id)


def requeue_live(db: Database, job_id: int, actor: str) -> None:
    """Send a post that was only simulated (dry run) through the real publisher."""
    job = _job(db, job_id)
    post = db.query_one("SELECT * FROM published_posts WHERE job_id = ?", (job_id,))
    if job["status"] != "published" or not post or not post["dry_run"]:
        raise QueueError("only dry-run publications can be re-queued for live publishing")
    with db.transaction() as conn:
        conn.execute("DELETE FROM published_posts WHERE id = ?", (post["id"],))
        conn.execute("UPDATE publish_jobs SET status = 'queued', attempts = 0, scheduled_at = ?, updated_at = ? WHERE id = ?",
                     (iso(), iso(), job_id))
        conn.execute("UPDATE drafts SET status = 'approved', updated_at = ? WHERE id = ?", (iso(), job["draft_id"]))
    db.audit(actor, "requeue_live", "publish_job", job_id)
