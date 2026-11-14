"""The end-to-end workflow: discover -> rank -> research -> write -> review
-> (human approval) -> publish -> measure. Each entry point records a run."""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import timedelta

import httpx

from .agents import reviewer, trend_ranker
from .agents.researcher import research_topic, store_research
from .agents.writer_base import PlatformWriter, writers_for
from .collectors.base import CollectorContext, all_collectors, run_collectors
from .config import Env, Settings
from .database import Database, dumps, loads
from .fixtures import OFFLINE_ENV, offline_transport
from .http import make_client
from .llm import LLM, ClaudeLLM, LLMError, SimulatedLLM, UnavailableLLM
from .models import Cluster, Draft, Research, Review
from .publishers.base import Publisher, all_publishers
from .services import analytics, approval, controls, publishing
from .services.deduplication import check_covered, cluster_items, mark_covered, previous_observations, store_items
from .timeutil import ago, iso

log = logging.getLogger(__name__)


class Pipeline:
    def __init__(self, settings: Settings, db: Database, env: Env, *, offline: bool = False,
                 transport: httpx.AsyncBaseTransport | None = None, llm: LLM | None = None,
                 publishers: dict[str, Publisher] | None = None, environ: dict[str, str] | None = None):
        self.settings = settings
        self.db = db
        self.env = env
        self.offline = offline
        self.transport = transport or (offline_transport() if offline else None)
        self._llm_override = llm
        self.environ = {**(environ if environ is not None else os.environ), **(OFFLINE_ENV if offline else {})}
        self.publishers = publishers if publishers is not None else ({} if offline else all_publishers(self.environ))

    @property
    def dry_run(self) -> bool:
        return self.offline or self.settings.publishing.dry_run

    def client(self) -> httpx.AsyncClient:
        return make_client(self.settings.collectors.timeout_seconds, transport=self.transport)

    def llm(self, run_id: int | None) -> LLM:
        if self._llm_override:
            return self._llm_override
        if self.offline:
            return SimulatedLLM(self.db, run_id)
        if not self.env.anthropic_api_key:
            return UnavailableLLM("ANTHROPIC_API_KEY is not set; trends were collected and ranked but not researched "
                                  "(run with --offline to simulate the AI steps)")
        return ClaudeLLM(self.db, api_key=self.env.anthropic_api_key, timeout=self.settings.ai.request_timeout_seconds,
                         budget_usd=self.settings.ai.monthly_budget_usd, run_id=run_id)

    # ---- run bookkeeping -------------------------------------------------------------------

    def _start(self, kind: str, trigger: str) -> int:
        return self.db.execute(
            "INSERT INTO runs (kind, status, trigger, dry_run, offline, started_at) VALUES (?, 'running', ?, ?, ?, ?)",
            (kind, trigger, int(self.dry_run), int(self.offline), iso()))

    def _finish(self, run_id: int, status: str, stats: dict, error: str | None = None) -> None:
        self.db.execute("UPDATE runs SET status = ?, finished_at = ?, stats_json = ?, error = ? WHERE id = ?",
                        (status, iso(), dumps(stats), error, run_id))

    def _skipped(self, kind: str, trigger: str, reason: str) -> dict:
        run_id = self._start(kind, trigger)
        self._finish(run_id, "skipped", {"reason": reason})
        return {"run_id": run_id, "skipped": reason}

    # ---- discovery ---------------------------------------------------------------------------

    async def discover(self, trigger: str = "manual") -> dict:
        with controls.locked(self.db, "discovery", timedelta(minutes=60)) as holder:
            if holder is None:
                return self._skipped("discovery", trigger, "another discovery run is in progress")
            run_id = self._start("discovery", trigger)
            try:
                stats = await self._discover(run_id)
            except Exception as e:
                log.exception("discovery failed")
                self.db.log_error("discovery", f"{type(e).__name__}: {e}", run_id=run_id)
                self._finish(run_id, "failed", {}, f"{type(e).__name__}: {e}")
                raise
            self._finish(run_id, "succeeded", stats)
            return {"run_id": run_id, **stats}

    async def _discover(self, run_id: int) -> dict:
        s = self.settings
        llm = self.llm(run_id)
        async with self.client() as client:
            items, reports = await run_collectors(all_collectors(), CollectorContext(s, client, self.environ))
            for r in reports:
                if r.status == "failed":
                    self.db.log_error(f"collector:{r.name}", r.message, run_id=run_id)
            store_items(self.db, items, run_id)
            previous = previous_observations(self.db, [i.id for i in items], run_id)
            clusters = cluster_items(items, s.selection.cluster_similarity)
            for c in clusters:
                blocked, reason, covered_id = check_covered(self.db, c, s)
                c.covered_topic_id = covered_id
                if blocked:
                    c.status, c.rejection_reason = "rejected", reason

            trend_ranker.base_scores(clusters, items, previous, s)
            multipliers = analytics.current_multipliers(self.db)
            trend_ranker.prefilter(clusters, s)
            live = sorted((c for c in clusters if c.status != "rejected"), key=lambda c: -c.score)
            shortlist = live[: s.selection.max_candidates_for_ai]
            await trend_ranker.classify(shortlist, s, llm)
            for c in shortlist:
                trend_ranker.apply_classification(c, s)
                m = analytics.multiplier_for(c.category, c.sources, multipliers)
                c.breakdown["learned_multiplier"] = round(m, 3)
                trend_ranker.compute_score(c, s, m)
            chosen = trend_ranker.select(clusters, s)
            for c in clusters:
                self._store_cluster(c, run_id)
            for c in chosen:
                covered = mark_covered(self.db, c)
                self.db.execute("UPDATE clusters SET covered_topic_id = ? WHERE id = ?", (covered, c.db_id))

            sem = asyncio.Semaphore(2)

            async def produce(c: Cluster) -> dict:
                async with sem:
                    return await self._produce(c, llm, client)

            produced = await asyncio.gather(*(produce(c) for c in chosen))

        drafts = [d for p in produced for d in p.get("drafts", [])]
        return {
            "collectors": {r.name: {"status": r.status, "count": r.count, "message": r.message} for r in reports},
            "items": len(items), "topics": len(clusters), "selected": [c.title for c in chosen],
            "rejected": sum(1 for c in clusters if c.status == "rejected"),
            "drafts": len(drafts), "awaiting_approval": sum(1 for d in drafts if d["status"] == "pending_approval"),
            "llm": llm.name,
        }

    def _store_cluster(self, c: Cluster, run_id: int) -> None:
        c.db_id = self.db.execute(
            """INSERT INTO clusters (run_id, cluster_key, title, keywords_json, trend_ids_json, sources_json, score,
                   score_breakdown_json, status, rejection_reason, safety_json, classification_json, category,
                   needs_human_review, covered_topic_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (run_id, c.key, c.title, dumps(c.keywords), dumps([i.id for i in c.items]), dumps(c.sources), c.score,
             dumps({k: round(v, 3) for k, v in c.breakdown.items()}), c.status, c.rejection_reason, dumps(c.safety),
             dumps(c.classification), c.category, int(c.needs_human_review), c.covered_topic_id, iso()))

    def _reject_cluster(self, c: Cluster, reason: str) -> None:
        c.status, c.rejection_reason = "rejected", reason
        self.db.execute("UPDATE clusters SET status = 'rejected', rejection_reason = ? WHERE id = ?", (reason, c.db_id))

    async def _produce(self, c: Cluster, llm: LLM, client: httpx.AsyncClient) -> dict:
        try:
            research = await research_topic(c, self.settings, llm, self.db, client)
        except LLMError as e:
            self._reject_cluster(c, f"research failed: {e}")
            self.db.log_error("research", str(e))
            return {}
        research_id = store_research(self.db, research, c.db_id)
        if not research.sufficient:
            self._reject_cluster(c, f"research: {research.insufficiency_reason}")
            return {}
        insights = analytics.writing_insights(self.db, self.settings)
        jobs = [self._write_and_review(w, research, c.db_id, c.key, research_id, llm, insights=insights,
                                       needs_human_review=c.needs_human_review)
                for w in writers_for(self.settings.enabled_platforms)]
        drafts = await asyncio.gather(*jobs)
        return {"drafts": [d for d in drafts if d]}

    def _recent_posts(self, platform: str) -> list[str]:
        since = ago(hours=max(self.settings.publishing.near_duplicate_hours, 1))
        rows = self.db.query(
            "SELECT post_text FROM published_posts WHERE platform = ? AND published_at >= ? "
            "UNION ALL SELECT post_text FROM drafts WHERE platform = ? AND status IN ('pending_approval', 'approved') "
            "AND updated_at >= ?", (platform, since, platform, since))
        return [r["post_text"] for r in rows]

    def _save_draft(self, draft_id: int | None, d: Draft, cluster_id: int, research_id: int, attempt: int,
                    needs_review: bool) -> int:
        now = iso()
        structure = d.structure()
        if draft_id:  # keep a media URL a person attached to the draft
            existing = loads(self.db.scalar("SELECT structure_json FROM drafts WHERE id = ?", (draft_id,)), {})
            if existing.get("media_url"):
                structure["media_url"] = existing["media_url"]
        values = (d.post_text, dumps(structure), d.media_brief, dumps(d.source_urls), dumps(d.hashtags),
                  dumps(d.claims), d.rationale, d.char_count, d.char_limit, attempt, d.generated_by, int(needs_review), now)
        if draft_id:
            self.db.execute(
                "UPDATE drafts SET post_text = ?, structure_json = ?, media_brief = ?, source_urls_json = ?, "
                "hashtags_json = ?, claims_json = ?, rationale = ?, char_count = ?, char_limit = ?, revision_count = ?, "
                "generated_by = ?, needs_human_review = ?, updated_at = ?, status = 'drafting', human_edited = 0 WHERE id = ?",
                (*values, draft_id))
            return draft_id
        return self.db.execute(
            """INSERT INTO drafts (post_text, structure_json, media_brief, source_urls_json, hashtags_json, claims_json,
                   rationale, char_count, char_limit, revision_count, generated_by, needs_human_review, updated_at,
                   cluster_id, research_id, platform, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'drafting', ?)""",
            (*values, cluster_id, research_id, d.platform, now))

    def _save_review(self, draft_id: int, attempt: int, r: Review) -> None:
        self.db.execute(
            "INSERT INTO reviews (draft_id, attempt, decision, reasons_json, instructions, checks_json, reviewer, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (draft_id, attempt, r.decision, dumps(r.reasons), r.revision_instructions, dumps(r.checks), r.reviewer, iso()))

    async def _write_and_review(self, writer: PlatformWriter, research: Research, cluster_id: int, cluster_key: str,
                                research_id: int, llm: LLM, *, draft_id: int | None = None, human: str = "",
                                insights: str = "", needs_human_review: bool = False, start_attempt: int = 0) -> dict | None:
        s = self.settings
        revision = ""
        recent = self._recent_posts(writer.platform)
        stub = Cluster(key=cluster_key, title=research.topic, items=[], keywords=[])
        final = "REJECTED"
        reason = ""
        for attempt in range(start_attempt, start_attempt + s.ai.max_revisions + 1):
            try:
                draft = await writer.write(research, stub, s, llm, revision=revision, human=human if attempt == start_attempt else "",
                                           insights=insights)
            except LLMError as e:
                self.db.log_error(f"writer:{writer.platform}", str(e))
                if draft_id:
                    self.db.execute("UPDATE drafts SET status = 'rejected', review_decision = 'REJECTED', updated_at = ? "
                                    "WHERE id = ?", (iso(), draft_id))
                return None
            draft_id = self._save_draft(draft_id, draft, cluster_id, research_id, attempt, needs_human_review)
            mine = [p for p in recent if p != draft.post_text]
            result = await reviewer.review(draft, research, s, llm, mine, writer.needs_media)
            self._save_review(draft_id, attempt + 1, result)
            final = result.decision
            if result.decision != "NEEDS_REVISION":
                break
            revision = result.revision_instructions or "; ".join(result.reasons)
            reason = revision
        else:
            reason = f"still failing review after {s.ai.max_revisions} revision(s): {reason}"
        status = "pending_approval" if final == "APPROVED_FOR_HUMAN_REVIEW" else "rejected"
        self.db.execute("UPDATE drafts SET status = ?, review_decision = ?, updated_at = ? WHERE id = ?",
                        (status, "REJECTED" if final == "NEEDS_REVISION" else final, iso(), draft_id))
        if reason and status == "rejected":
            self.db.audit("system", "draft_rejected_by_reviewer", "draft", draft_id, reason=reason[:500])
        auto, _ = controls.auto_publish_state(self.db, s)
        if status == "pending_approval" and auto and not needs_human_review:
            try:
                approval.approve(self.db, s, draft_id, "system:auto", note="auto-publish: reviewer approved")
                status = "approved"
            except approval.ApprovalError as e:
                log.warning("auto-approve failed", extra={"draft": draft_id, "error": str(e)})
        return {"draft_id": draft_id, "platform": writer.platform, "status": status}

    # ---- dashboard actions that need a model -------------------------------------------------

    def _load(self, draft_id: int) -> tuple[dict, Research]:
        draft = approval.get_draft(self.db, draft_id)
        row = self.db.query_one("SELECT data_json FROM research WHERE id = ?", (draft["research_id"],))
        return draft, Research.model_validate_json(row["data_json"])

    async def rewrite(self, draft_id: int, instructions: str, actor: str) -> dict | None:
        draft, research = self._load(draft_id)
        if draft["status"] not in ("pending_approval", "rejected", "rejected_by_human"):
            raise approval.ApprovalError(f"a {draft['status']} draft cannot be rewritten; cancel its queued job first")
        cluster = self.db.query_one("SELECT cluster_key, needs_human_review FROM clusters WHERE id = ?", (draft["cluster_id"],))
        writer = writers_for([draft["platform"]])[0]
        self.db.execute("INSERT INTO approvals (draft_id, action, actor, note, created_at) VALUES (?, 'rewrite', ?, ?, ?)",
                        (draft_id, actor, instructions[:1000], iso()))
        self.db.audit(actor, "request_rewrite", "draft", draft_id, instructions=instructions[:1000])
        run_id = self._start("rewrite", "dashboard")
        result = await self._write_and_review(
            writer, research, draft["cluster_id"], cluster["cluster_key"], draft["research_id"], self.llm(run_id),
            draft_id=draft_id, human=instructions, needs_human_review=bool(cluster["needs_human_review"]),
            start_attempt=draft["revision_count"] + 1)
        self._finish(run_id, "succeeded" if result else "failed", result or {})
        return result

    async def rereview(self, draft_id: int, actor: str) -> Review:
        """Review a human-edited draft again. The result is shown to the person;
        a REJECTED result moves the draft out of the approval queue."""
        row, research = self._load(draft_id)
        structure = loads(row["structure_json"], {})
        d = Draft(platform=row["platform"], cluster_key="", post_text=row["post_text"],
                  thread_posts=structure.get("thread_posts", []), source_urls=loads(row["source_urls_json"], []),
                  hashtags=loads(row["hashtags_json"], []), claims=loads(row["claims_json"], []),
                  media_brief=row["media_brief"], char_count=row["char_count"], char_limit=row["char_limit"])
        writer = writers_for([row["platform"]])[0]
        recent = [p for p in self._recent_posts(row["platform"]) if p != row["post_text"]]
        result = await reviewer.review(d, research, self.settings, self.llm(None), recent, writer.needs_media)
        self._save_review(draft_id, row["revision_count"] + 1, result)
        if not result.complete:
            # The reviewer could not run: record that, but leave the person's draft where it was.
            self.db.audit(actor, "rereview_failed", "draft", draft_id, reason=result.reasons[0])
            return result
        new_status = "rejected" if result.decision == "REJECTED" else row["status"]
        self.db.execute("UPDATE drafts SET review_decision = ?, human_edited = 0, status = ?, updated_at = ? WHERE id = ?",
                        (result.decision, new_status, iso(), draft_id))
        self.db.audit(actor, "rereview", "draft", draft_id, decision=result.decision)
        return result

    # ---- publishing and metrics ----------------------------------------------------------------

    async def publish(self, trigger: str = "manual") -> dict:
        run_id = self._start("publish", trigger)
        try:
            async with self.client() as client:
                stats = await publishing.publish_due(self.db, self.settings, self.publishers, client, dry_run=self.dry_run)
        except Exception as e:
            self.db.log_error("publishing", f"{type(e).__name__}: {e}", run_id=run_id)
            self._finish(run_id, "failed", {}, str(e))
            raise
        self._finish(run_id, "skipped" if "skipped" in stats else "succeeded", stats)
        return {"run_id": run_id, **stats}

    async def metrics(self, trigger: str = "manual") -> dict:
        run_id = self._start("metrics", trigger)
        async with self.client() as client:
            stats = await analytics.collect(self.db, self.publishers, client)
        stats["adjustments"] = len(analytics.learn(self.db, self.settings))
        self._finish(run_id, "succeeded", stats)
        return {"run_id": run_id, **stats}
