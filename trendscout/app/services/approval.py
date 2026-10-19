"""Human decisions on drafts. Only `approve` creates a publishing job, and it
only accepts drafts the reviewer passed (status pending_approval)."""
from __future__ import annotations

from datetime import datetime

from ..config import Settings
from ..database import Database, dumps, loads
from ..textutil import count_chars, make_tid, stable_hash
from ..timeutil import iso
from . import scheduler

APPROVABLE = {"pending_approval"}
EDITABLE = {"pending_approval", "approved", "rejected"}


class ApprovalError(Exception):
    pass


def get_draft(db: Database, draft_id: int) -> dict:
    row = db.query_one("SELECT * FROM drafts WHERE id = ?", (draft_id,))
    if not row:
        raise ApprovalError(f"draft {draft_id} not found")
    return row


def approve(db: Database, settings: Settings, draft_id: int, actor: str, when: datetime | None = None,
            note: str = "") -> int:
    """Approve a draft and queue it. Returns the publishing job id. Approving
    an already-approved draft returns its existing job instead of a new one."""
    draft = get_draft(db, draft_id)
    if draft["status"] == "approved":
        job = db.query_one("SELECT id FROM publish_jobs WHERE draft_id = ?", (draft_id,))
        if job:
            return job["id"]
    if draft["status"] not in APPROVABLE:
        raise ApprovalError(f"draft {draft_id} is {draft['status']}; only drafts awaiting approval can be approved")
    if draft["char_count"] > draft["char_limit"]:
        raise ApprovalError(f"draft {draft_id} is over the {draft['platform']} character limit")
    platform = draft["platform"]
    scheduled = scheduler.next_slot(db, settings, platform, when)
    key = f"{draft_id}:{platform}:{stable_hash(draft['post_text'])}"
    now = iso()
    with db.transaction() as conn:
        updated = conn.execute(
            "UPDATE drafts SET status = 'approved', updated_at = ? WHERE id = ? AND status = 'pending_approval'",
            (now, draft_id)).rowcount
        if not updated:
            raise ApprovalError(f"draft {draft_id} changed while approving; reload and try again")
        conn.execute("INSERT INTO approvals (draft_id, action, actor, note, created_at) VALUES (?, ?, ?, ?, ?)",
                     (draft_id, "auto_approve" if actor.startswith("system") else "approve", actor, note, now))
        existing = conn.execute("SELECT id, status FROM publish_jobs WHERE draft_id = ?", (draft_id,)).fetchone()
        if existing:
            conn.execute(
                "UPDATE publish_jobs SET status = 'queued', scheduled_at = ?, idempotency_key = ?, last_error = NULL, "
                "updated_at = ? WHERE id = ? AND status IN ('cancelled', 'held')",
                (iso(scheduled), key, now, existing["id"]))
            job_id = existing["id"]
        else:
            job_id = conn.execute(
                """INSERT INTO publish_jobs (draft_id, platform, idempotency_key, client_ref, status, scheduled_at,
                       created_at, updated_at) VALUES (?, ?, ?, ?, 'queued', ?, ?, ?)""",
                (draft_id, platform, key, make_tid(key), iso(scheduled), now, now)).lastrowid
    db.audit(actor, "approve", "draft", draft_id, job_id=job_id, scheduled_at=iso(scheduled))
    return job_id


def approve_many(db: Database, settings: Settings, draft_ids: list[int], actor: str) -> tuple[list[int], list[str]]:
    jobs, errors = [], []
    for d in draft_ids:
        try:
            jobs.append(approve(db, settings, d, actor))
        except ApprovalError as e:
            errors.append(str(e))
    return jobs, errors


def reschedule(db: Database, settings: Settings, draft_id: int, when: datetime, actor: str) -> None:
    job = db.query_one("SELECT * FROM publish_jobs WHERE draft_id = ?", (draft_id,))
    if not job or job["status"] != "queued":
        raise ApprovalError("only queued posts can be rescheduled")
    # An explicit time inside the publishing window is honoured as given; the
    # daily limit and spacing are still enforced when the job runs.
    slot = when if scheduler.in_window(settings, when) else scheduler.next_window_start(settings, when)
    db.execute("UPDATE publish_jobs SET scheduled_at = ?, updated_at = ? WHERE id = ? AND status = 'queued'",
               (iso(slot), iso(), job["id"]))
    db.execute("INSERT INTO approvals (draft_id, action, actor, note, created_at) VALUES (?, 'schedule', ?, ?, ?)",
               (draft_id, actor, iso(slot), iso()))
    db.audit(actor, "schedule", "draft", draft_id, scheduled_at=iso(slot))


def _cancel_job(conn, draft_id: int, reason: str) -> None:
    conn.execute("UPDATE publish_jobs SET status = 'cancelled', last_error = ?, updated_at = ? "
                 "WHERE draft_id = ? AND status IN ('queued', 'held')", (reason, iso(), draft_id))


def reject(db: Database, draft_id: int, actor: str, note: str = "") -> None:
    draft = get_draft(db, draft_id)
    if draft["status"] == "published":
        raise ApprovalError("a published post cannot be rejected")
    with db.transaction() as conn:
        job = conn.execute("SELECT status FROM publish_jobs WHERE draft_id = ?", (draft_id,)).fetchone()
        if job and job["status"] in ("publishing", "uncertain"):
            raise ApprovalError("this post is being published or awaiting reconciliation; resolve it on the queue page")
        conn.execute("UPDATE drafts SET status = 'rejected_by_human', updated_at = ? WHERE id = ?", (iso(), draft_id))
        _cancel_job(conn, draft_id, "draft rejected")
        conn.execute("INSERT INTO approvals (draft_id, action, actor, note, created_at) VALUES (?, 'reject', ?, ?, ?)",
                     (draft_id, actor, note, iso()))
    db.audit(actor, "reject", "draft", draft_id, note=note)


def edit(db: Database, draft_id: int, actor: str, text: str, media_url: str = "") -> dict:
    """Save a human edit. An approved draft goes back to awaiting approval
    and its queued job is cancelled, so an edit can never slip out unapproved."""
    draft = get_draft(db, draft_id)
    if draft["status"] not in EDITABLE:
        raise ApprovalError(f"a {draft['status']} draft cannot be edited")
    text = text.replace("\r\n", "\n").strip()
    if not text:
        raise ApprovalError("post text cannot be empty")
    structure = loads(draft["structure_json"], {})
    if media_url:
        if not media_url.startswith("https://"):
            raise ApprovalError("media URL must be a public https:// URL")
        structure["media_url"] = media_url
    count = count_chars(text, draft["platform"])
    with db.transaction() as conn:
        job = conn.execute("SELECT status FROM publish_jobs WHERE draft_id = ?", (draft_id,)).fetchone()
        if job and job["status"] in ("publishing", "uncertain", "published"):
            raise ApprovalError("this post is already being published")
        conn.execute(
            "UPDATE drafts SET post_text = ?, char_count = ?, structure_json = ?, human_edited = 1, "
            "status = 'pending_approval', updated_at = ? WHERE id = ?",
            (text, count, dumps(structure), iso(), draft_id))
        _cancel_job(conn, draft_id, "draft edited after approval")
        conn.execute("INSERT INTO approvals (draft_id, action, actor, note, created_at) VALUES (?, 'edit', ?, ?, ?)",
                     (draft_id, actor, f"{draft['char_count']} -> {count} chars", iso()))
    db.audit(actor, "edit", "draft", draft_id, before=draft["post_text"], after=text)
    return get_draft(db, draft_id)
