"""End-to-end workflow, human approval rules, and publishing safety."""
import asyncio
import threading
from datetime import timedelta

import httpx
import pytest

from app.models import Outcome, PublishResult
from app.pipeline import Pipeline
from app.services import approval, controls, publishing
from app.timeutil import iso, utcnow
from tests.conftest import NoNetwork, RecordingPublisher, discover_offline, pending_ids, run


def publish(db, settings, pub, dry_run=False):
    return run(publishing.publish_due(db, settings, {"bluesky": pub}, httpx.AsyncClient(transport=NoNetwork()),
                                      dry_run=dry_run))


def test_full_dry_run_workflow(pipeline, db, settings):
    stats = discover_offline(pipeline)
    assert stats["selected"] and stats["awaiting_approval"] >= 1
    ids = pending_ids(db)
    # Nothing is queued until a person approves.
    assert db.scalar("SELECT COUNT(*) FROM publish_jobs") == 0
    assert run(pipeline.publish(trigger="test")).get("published") is None

    approval.approve(db, settings, ids[0], "tester")
    out = run(pipeline.publish(trigger="test"))
    assert out["published"] == 1
    post = db.query_one("SELECT * FROM published_posts")
    assert post["dry_run"] == 1 and post["platform_post_id"].startswith("dryrun-")
    assert db.scalar("SELECT status FROM drafts WHERE id = ?", (ids[0],)) == "published"
    # Running again publishes nothing new.
    assert run(pipeline.publish(trigger="test")).get("published") is None
    assert db.scalar("SELECT COUNT(*) FROM published_posts") == 1
    # Every record is auditable back to its sources.
    research = db.query_one("SELECT r.data_json FROM research r JOIN drafts d ON d.research_id = r.id WHERE d.id = ?", (ids[0],))
    assert "https://example.com/" in research["data_json"]
    actions = {r["action"] for r in db.query("SELECT action FROM audit_log")}
    assert {"approve", "published_dry_run"} <= actions


def test_covered_topics_are_not_selected_again(pipeline, db):
    first = discover_offline(pipeline)
    second = discover_offline(pipeline)
    assert first["selected"] and not set(first["selected"]) & set(second["selected"])
    reasons = [r["rejection_reason"] for r in db.query("SELECT rejection_reason FROM clusters WHERE run_id = ?", (second["run_id"],))]
    assert any(r and r.startswith("already covered") for r in reasons)


def test_without_api_key_trends_are_ranked_but_nothing_is_written(settings, db, env):
    from app.fixtures import offline_transport
    p = Pipeline(settings, db, env, offline=False, transport=offline_transport(), publishers={})
    p.environ.update({"REDDIT_CLIENT_ID": "", "YOUTUBE_API_KEY": ""})
    stats = run(p.discover(trigger="test"))
    assert stats["items"] > 0 and stats["drafts"] == 0 and stats["llm"] == "unavailable"
    assert any("ANTHROPIC_API_KEY" in (r["rejection_reason"] or "") for r in db.query("SELECT rejection_reason FROM clusters"))


def test_approval_rules(pipeline, db, settings):
    discover_offline(pipeline)
    first, second = pending_ids(db)[:2]
    job = approval.approve(db, settings, first, "tester")
    assert approval.approve(db, settings, first, "tester") == job  # idempotent
    assert db.scalar("SELECT COUNT(*) FROM publish_jobs") == 1
    db.execute("UPDATE drafts SET status = 'rejected' WHERE id = ?", (second,))
    with pytest.raises(approval.ApprovalError, match="only drafts awaiting approval"):
        approval.approve(db, settings, second, "tester")
    db.execute("UPDATE drafts SET status = 'pending_approval', char_count = 999 WHERE id = ?", (second,))
    with pytest.raises(approval.ApprovalError, match="character limit"):
        approval.approve(db, settings, second, "tester")


def test_edit_after_approval_requires_new_approval(pipeline, db, settings):
    discover_offline(pipeline)
    d = pending_ids(db)[0]
    approval.approve(db, settings, d, "tester")
    approval.edit(db, d, "tester", "A shorter, human-written version of the post.")
    assert db.scalar("SELECT status FROM drafts WHERE id = ?", (d,)) == "pending_approval"
    assert db.scalar("SELECT status FROM publish_jobs WHERE draft_id = ?", (d,)) == "cancelled"
    assert run(pipeline.publish(trigger="test")).get("published") is None
    approval.approve(db, settings, d, "tester")
    assert run(pipeline.publish(trigger="test"))["published"] == 1
    assert db.scalar("SELECT post_text FROM published_posts") == "A shorter, human-written version of the post."


def test_reject_cancels(pipeline, db, settings):
    discover_offline(pipeline)
    d = pending_ids(db)[0]
    approval.approve(db, settings, d, "tester")
    approval.reject(db, d, "tester", "not our angle")
    assert db.scalar("SELECT status FROM publish_jobs WHERE draft_id = ?", (d,)) == "cancelled"
    assert run(pipeline.publish(trigger="test")).get("published") is None


def test_auto_publish_only_when_configured(settings, db, env):
    settings.publishing.require_human_approval = False
    settings.publishing.auto_publish = True
    discover_offline(Pipeline(settings, db, env, offline=True))
    assert db.scalar("SELECT COUNT(*) FROM drafts WHERE status = 'approved'") >= 1
    assert db.query_one("SELECT actor FROM approvals WHERE action = 'auto_approve'")["actor"] == "system:auto"


def test_dry_run_never_calls_the_real_publisher(pipeline, db, settings):
    discover_offline(pipeline)
    approval.approve(db, settings, pending_ids(db)[0], "tester")
    pub = RecordingPublisher()
    assert publish(db, settings, pub, dry_run=True)["published"] == 1
    assert pub.calls == []


@pytest.fixture
def one_job(pipeline, db, settings):
    discover_offline(pipeline)
    d = pending_ids(db)[0]
    return approval.approve(db, settings, d, "tester")


def job(db, job_id):
    return db.query_one("SELECT * FROM publish_jobs WHERE id = ?", (job_id,))


def test_live_publish_records_platform_ids(db, settings, one_job):
    pub = RecordingPublisher()
    assert publish(db, settings, pub)["published"] == 1
    post = db.query_one("SELECT * FROM published_posts")
    assert post["dry_run"] == 0 and post["url"].startswith("https://bsky.app/") and pub.calls == [one_job]


def test_kill_switch_stops_publishing(db, settings, one_job):
    controls.pause(db, "tester", "test")
    pub = RecordingPublisher()
    assert publish(db, settings, pub) == {"skipped": "publishing is paused"}
    assert pub.calls == []
    controls.resume(db, "tester")
    assert publish(db, settings, pub)["published"] == 1


def test_retryable_failure_is_requeued_later(db, settings, one_job):
    pub = RecordingPublisher([PublishResult(Outcome.FAILED, error="connect failed", retryable=True)])
    assert publish(db, settings, pub)["retry"] == 1
    j = job(db, one_job)
    assert j["status"] == "queued" and j["attempts"] == 1 and j["scheduled_at"] > iso()


def test_definite_failure_is_not_retried(db, settings, one_job):
    pub = RecordingPublisher([PublishResult(Outcome.FAILED, error="HTTP 400 invalid record")])
    assert publish(db, settings, pub)["failed"] == 1
    assert job(db, one_job)["status"] == "failed"
    assert publish(db, settings, pub).get("published") is None and len(pub.calls) == 1


def test_uncertain_result_is_never_blindly_retried(db, settings, one_job):
    pub = RecordingPublisher([PublishResult(Outcome.UNCERTAIN, error="read timeout")])
    assert publish(db, settings, pub)["uncertain"] == 1
    # Platform cannot tell us: the job stays uncertain and is not sent again.
    assert publish(db, settings, pub)["still_uncertain"] == 1
    assert pub.calls == [one_job] and job(db, one_job)["status"] == "uncertain"
    with pytest.raises(publishing.QueueError):
        publishing.retry(db, one_job, "tester")  # needs explicit confirmation
    # Reconciliation finds the post: it is recorded, without a second submission.
    pub.reconcile_result = PublishResult(Outcome.SUCCESS, platform_post_id="at://x", url="https://bsky.app/x",
                                         detail={"reconciled": True})
    assert publish(db, settings, pub)["reconciled_published"] == 1
    assert pub.calls == [one_job] and job(db, one_job)["status"] == "published"
    assert db.scalar("SELECT COUNT(*) FROM published_posts") == 1


def test_uncertain_confirmed_missing_is_retried(db, settings, one_job):
    pub = RecordingPublisher([PublishResult(Outcome.UNCERTAIN, error="HTTP 502")])
    publish(db, settings, pub)
    pub.reconcile_result = PublishResult(Outcome.FAILED, error="confirmed not posted", retryable=True)
    out = publish(db, settings, pub)
    assert out["reconciled_queued"] == 1 and out["published"] == 1 and pub.calls == [one_job, one_job]


def test_crash_mid_publish_becomes_uncertain(db, settings, one_job):
    past = iso(utcnow() - timedelta(minutes=30))
    db.execute("UPDATE publish_jobs SET status = 'publishing', lease_expires_at = ? WHERE id = ?", (past, one_job))
    pub = RecordingPublisher()
    out = publish(db, settings, pub)
    assert out["recovered_stale"] == 1 and pub.calls == []
    assert job(db, one_job)["status"] == "uncertain"


def test_unexpected_exception_is_treated_as_uncertain(db, settings, one_job):
    class Boom(RecordingPublisher):
        async def publish(self, client, job, draft):
            raise RuntimeError("bug after sending")
    assert publish(db, settings, Boom())["uncertain"] == 1


def test_rate_limit_backs_off_without_using_an_attempt(db, settings, one_job):
    until = utcnow() + timedelta(minutes=20)
    pub = RecordingPublisher([PublishResult(Outcome.FAILED, error="429", retryable=True, rate_limited_until=until)])
    assert publish(db, settings, pub)["deferred"] == 1
    j = job(db, one_job)
    assert j["attempts"] == 0 and j["status"] == "queued" and controls.backoff_until(db, "bluesky") >= until - timedelta(seconds=1)


def test_unconfigured_platform_holds_the_job(db, settings, one_job):
    pub = RecordingPublisher([PublishResult(Outcome.NOT_CONFIGURED, error="missing BLUESKY_HANDLE")])
    assert publish(db, settings, pub)["held"] == 1
    assert job(db, one_job)["status"] == "held"


def test_daily_limit_and_spacing(pipeline, db, settings):
    settings.platforms["bluesky"].daily_limit = 1
    discover_offline(pipeline)
    ids = pending_ids(db)
    assert len(ids) >= 2
    jobs = [approval.approve(db, settings, d, "tester") for d in ids[:2]]
    # Approval already spreads them: the second is scheduled on a later day.
    assert job(db, jobs[1])["scheduled_at"] > job(db, jobs[0])["scheduled_at"]
    db.execute("UPDATE publish_jobs SET scheduled_at = ?", (iso(utcnow() - timedelta(minutes=1)),))
    out = publish(db, settings, RecordingPublisher())
    assert out["published"] == 1 and out["deferred"] == 1


def test_near_duplicate_is_held(pipeline, db, settings):
    discover_offline(pipeline)
    ids = pending_ids(db)
    approval.edit(db, ids[1], "tester", db.scalar("SELECT post_text FROM drafts WHERE id = ?", (ids[0],)))
    for d in ids[:2]:
        approval.approve(db, settings, d, "tester")
    db.execute("UPDATE publish_jobs SET scheduled_at = ?", (iso(utcnow() - timedelta(minutes=1)),))
    out = publish(db, settings, RecordingPublisher())
    assert out["published"] == 1 and out["held"] == 1


def test_circuit_breaker_pauses_publishing(db, settings, one_job):
    for _ in range(settings.publishing.error_pause_threshold):
        db.log_error("publishing", "simulated failure")
    pub = RecordingPublisher()
    assert publish(db, settings, pub)["circuit_breaker"] == 1
    assert controls.is_paused(db) and pub.calls == []


def test_concurrent_claims_have_one_winner(db, settings, one_job):
    winners = []
    barrier = threading.Barrier(8)

    def worker(n):
        barrier.wait()
        if publishing.claim(db, one_job, f"w{n}", timedelta(minutes=5), utcnow()):
            winners.append(n)

    threads = [threading.Thread(target=worker, args=(n,)) for n in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(winners) == 1


def test_two_simultaneous_runs_cannot_publish_the_same_job_twice(db, settings, one_job):
    pub = RecordingPublisher(delay=0.3)  # slow platform: both runs overlap
    results = []

    def run_publisher():
        results.append(asyncio.run(publishing.publish_due(
            db, settings, {"bluesky": pub}, httpx.AsyncClient(transport=NoNetwork()), dry_run=False)))

    threads = [threading.Thread(target=run_publisher) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert pub.calls == [one_job]
    assert db.scalar("SELECT COUNT(*) FROM published_posts") == 1
    assert {"skipped": "another publishing run is in progress"} in results or sum(r.get("published", 0) for r in results) == 1


def test_queue_resolution_actions(db, settings, one_job):
    publish(db, settings, RecordingPublisher([PublishResult(Outcome.UNCERTAIN, error="timeout")]))
    publishing.mark_published(db, one_job, "https://bsky.app/profile/me/post/abc", "tester")
    assert job(db, one_job)["status"] == "published"
    assert db.scalar("SELECT url FROM published_posts") == "https://bsky.app/profile/me/post/abc"


def test_failed_rereview_leaves_human_edit_in_place(settings, db, env):
    from app.llm import UnavailableLLM
    discover_offline(Pipeline(settings, db, env, offline=True))
    d = pending_ids(db)[0]
    approval.edit(db, d, "tester", "My own wording of the post.")
    p = Pipeline(settings, db, env, offline=False, llm=UnavailableLLM("API down"), publishers={})
    result = run(p.rereview(d, "tester"))
    assert not result.complete
    assert db.scalar("SELECT status FROM drafts WHERE id = ?", (d,)) == "pending_approval"
