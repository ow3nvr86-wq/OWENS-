"""Dashboard pages and actions. Every POST requires a signed-in session and
a valid CSRF token; every state change is written to the audit log by the
service it calls."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from jinja2 import pass_context

from ..database import Database, loads
from ..llm import month_spend
from ..publishers.base import all_publishers
from ..services import analytics, approval, controls, publishing
from ..timeutil import UTC, parse_iso, utcnow
from . import auth

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))
STATUSES = ["pending_approval", "approved", "published", "rejected", "rejected_by_human", "drafting"]


def _local(value: str | datetime | None, tz=UTC, fmt: str = "%a %d %b %H:%M") -> str:
    dt = parse_iso(value) if isinstance(value, str) else value
    if not dt:
        return "—"
    return dt.astimezone(tz).strftime(fmt)


@pass_context
def _local_filter(ctx, value, fmt: str = "%a %d %b %H:%M") -> str:
    settings = ctx.get("settings")
    return _local(value, settings.schedule.tz if settings else UTC, fmt)


templates.env.filters["local"] = _local_filter
templates.env.filters["safe_url"] = lambda v: safe_url(v)
templates.env.filters["fromjson"] = lambda v, d=None: loads(v, d if d is not None else {})


def trends_by_ids(db: Database, ids: list[str]) -> list[dict]:
    if not ids:
        return []
    return db.query(f"SELECT * FROM trends WHERE id IN ({','.join('?' * len(ids))})", ids)


def db_of(request: Request) -> Database:
    return request.app.state.db


def render(request: Request, name: str, **ctx: Any) -> HTMLResponse:
    s = request.app.state.settings
    db = db_of(request)
    auto, auto_reason = controls.auto_publish_state(db, s)
    ctx.update(
        request=request, user=request.session.get("user"), csrf=auth.csrf_token(request), settings=s,
        flash=request.session.pop("flash", None), paused=controls.is_paused(db),
        pause_reason=controls.get(db, controls.PAUSE_REASON, ""), auto_publish=auto, auto_reason=auto_reason,
        dry_run=s.publishing.dry_run or request.app.state.offline, offline=request.app.state.offline,
        pending_count=db.scalar("SELECT COUNT(*) FROM drafts WHERE status = 'pending_approval'"),
    )
    return templates.TemplateResponse(request, name, ctx)


def back(request: Request, url: str, message: str, kind: str = "ok") -> RedirectResponse:
    request.session["flash"] = {"kind": kind, "text": message}
    if not url.startswith("/") or url.startswith("//") or "\\" in url:
        url = "/"  # only same-site paths; `next` comes from a form field
    return RedirectResponse(url, status_code=303)


def safe_url(value: str | None) -> str:
    """Links on the dashboard come from collected or generated data: allow http(s) only."""
    return value if isinstance(value, str) and value.lower().startswith(("http://", "https://")) else "#"


def _parse_local(value: str, request: Request) -> datetime | None:
    if not value:
        return None
    try:
        naive = datetime.fromisoformat(value)
    except ValueError:
        raise HTTPException(400, "invalid date/time")
    return naive.replace(tzinfo=request.app.state.settings.schedule.tz).astimezone(UTC)


# ---- auth ------------------------------------------------------------------------------------

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    ok, problem = auth.auth_configured(request.app.state.env)
    return render(request, "login.html", problem=None if ok else problem)


@router.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...), csrf_token: str = Form("")):
    auth.check_csrf(request, csrf_token)
    env = request.app.state.env
    ip = request.client.host if request.client else "unknown"
    ok, problem = auth.auth_configured(env)
    if not ok:
        return back(request, "/login", problem, "error")
    if auth.locked_out(ip):
        return back(request, "/login", "Too many failed attempts. Wait five minutes.", "error")
    if not auth.verify_credentials(env, username, password):
        auth.record_failure(ip)
        db_of(request).audit(username[:64], "login_failed", "session", ip)
        return back(request, "/login", "Wrong username or password.", "error")
    auth.clear_failures(ip)
    request.session.clear()
    request.session["user"] = env.dashboard_username
    db_of(request).audit(env.dashboard_username, "login", "session", ip)
    return RedirectResponse("/", status_code=303)


@router.post("/logout")
async def logout(request: Request, csrf_token: str = Form("")):
    auth.check_csrf(request, csrf_token)
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


@router.get("/healthz")
async def healthz(request: Request):
    db_of(request).scalar("SELECT 1")
    return {"ok": True}


# ---- pages -----------------------------------------------------------------------------------

@router.get("/", response_class=HTMLResponse)
async def overview(request: Request, user: str = Depends(auth.current_user)):
    db = db_of(request)
    s = request.app.state.settings
    counts = {r["status"]: r["n"] for r in db.query("SELECT status, COUNT(*) AS n FROM drafts GROUP BY status")}
    jobs = {r["status"]: r["n"] for r in db.query("SELECT status, COUNT(*) AS n FROM publish_jobs GROUP BY status")}
    accounts = {r["platform"]: r for r in db.query("SELECT * FROM platform_accounts")}
    platforms = []
    for name, pub in all_publishers().items():
        configured, msg = pub.configured()
        platforms.append({"name": name, "enabled": s.platforms[name].enabled, "configured": configured, "detail": msg,
                          "verified": accounts.get(name, {}).get("status"), "prerequisites": pub.prerequisites,
                          "daily_limit": s.platforms[name].daily_limit})
    return render(request, "overview.html", counts=counts, jobs=jobs, platforms=platforms,
                  runs=db.query("SELECT * FROM runs ORDER BY id DESC LIMIT 8"),
                  errors=db.query("SELECT * FROM error_log ORDER BY id DESC LIMIT 5"),
                  spend=month_spend(db), budget=s.ai.monthly_budget_usd, running=len(request.app.state.tasks),
                  ai_ready=bool(request.app.state.env.anthropic_api_key) or request.app.state.offline)


@router.get("/trends", response_class=HTMLResponse)
async def trends(request: Request, run: int | None = None, show: str = "all", user: str = Depends(auth.current_user)):
    db = db_of(request)
    runs = db.query("SELECT id, started_at, status, offline FROM runs WHERE kind = 'discovery' ORDER BY id DESC LIMIT 30")
    run = run or (runs[0]["id"] if runs else None)
    where = "run_id = ?" + ("" if show == "all" else " AND status = ?")
    params: list = [run] + ([] if show == "all" else [show])
    clusters = db.query(f"SELECT * FROM clusters WHERE {where} ORDER BY status = 'selected' DESC, score DESC", params)
    for c in clusters:
        c["items"] = trends_by_ids(db, loads(c["trend_ids_json"], []))
    return render(request, "trends.html", clusters=clusters, runs=runs, run=run, show=show)


@router.get("/topics/{cluster_id}", response_class=HTMLResponse)
async def topic(request: Request, cluster_id: int, user: str = Depends(auth.current_user)):
    db = db_of(request)
    c = db.query_one("SELECT * FROM clusters WHERE id = ?", (cluster_id,))
    if not c:
        raise HTTPException(404)
    items = trends_by_ids(db, loads(c["trend_ids_json"], []))
    research = db.query_one("SELECT * FROM research WHERE cluster_id = ? ORDER BY id DESC", (cluster_id,))
    drafts = db.query("SELECT * FROM drafts WHERE cluster_id = ? ORDER BY platform", (cluster_id,))
    return render(request, "topic.html", c=c, items=items, research=loads(research["data_json"]) if research else None,
                  drafts=drafts)


def _draft_rows(db: Database, where: str, params: list) -> list[dict]:
    drafts = db.query(
        f"""SELECT d.*, c.title AS topic, c.score AS topic_score, c.category, j.status AS job_status, j.scheduled_at,
                   j.id AS job_id FROM drafts d JOIN clusters c ON c.id = d.cluster_id
            LEFT JOIN publish_jobs j ON j.draft_id = d.id WHERE {where} ORDER BY d.updated_at DESC LIMIT 200""", params)
    for d in drafts:
        d["reviews"] = db.query("SELECT * FROM reviews WHERE draft_id = ? ORDER BY attempt DESC", (d["id"],))
        d["structure"] = loads(d["structure_json"], {})
    return drafts


@router.get("/drafts", response_class=HTMLResponse)
async def drafts(request: Request, status: str = "pending_approval", platform: str = "",
                 user: str = Depends(auth.current_user)):
    db = db_of(request)
    clauses, params = [], []
    if status != "all":
        clauses.append("d.status = ?")
        params.append(status)
    if platform:
        clauses.append("d.platform = ?")
        params.append(platform)
    rows = _draft_rows(db, " AND ".join(clauses) or "1=1", params)
    return render(request, "drafts.html", drafts=rows, status=status, platform=platform, statuses=STATUSES)


@router.get("/queue", response_class=HTMLResponse)
async def queue(request: Request, user: str = Depends(auth.current_user)):
    db = db_of(request)
    jobs = db.query("""SELECT j.*, d.post_text, d.platform AS dplatform, p.url, p.dry_run, p.published_at
                       FROM publish_jobs j JOIN drafts d ON d.id = j.draft_id
                       LEFT JOIN published_posts p ON p.job_id = j.id
                       ORDER BY CASE j.status WHEN 'uncertain' THEN 0 WHEN 'publishing' THEN 1 WHEN 'queued' THEN 2
                                WHEN 'held' THEN 3 WHEN 'failed' THEN 4 ELSE 5 END, j.scheduled_at DESC LIMIT 200""")
    return render(request, "queue.html", jobs=jobs)


@router.get("/published", response_class=HTMLResponse)
async def published(request: Request, user: str = Depends(auth.current_user)):
    db = db_of(request)
    posts = db.query("SELECT * FROM published_posts ORDER BY published_at DESC LIMIT 200")
    for p in posts:
        p["metrics"] = db.query("SELECT * FROM metrics WHERE post_id = ? ORDER BY post_age_minutes", (p["id"],))
    return render(request, "published.html", posts=posts)


@router.get("/analytics", response_class=HTMLResponse)
async def analytics_page(request: Request, user: str = Depends(auth.current_user)):
    db = db_of(request)
    s = request.app.state.settings
    usage = db.query("""SELECT substr(ts, 1, 10) AS day, model, COUNT(*) AS calls, SUM(input_tokens) AS input_tokens,
                               SUM(output_tokens) AS output_tokens, SUM(web_searches) AS searches, SUM(cost_usd) AS cost
                        FROM llm_usage GROUP BY day, model ORDER BY day DESC LIMIT 60""")
    return render(request, "analytics.html", report=analytics.report(db, s),
                  adjustments=db.query("SELECT * FROM scoring_adjustments ORDER BY id DESC LIMIT 50"),
                  usage=usage, spend=month_spend(db), weights=s.scoring.weights.normalized())


@router.get("/logs", response_class=HTMLResponse)
async def logs(request: Request, user: str = Depends(auth.current_user)):
    db = db_of(request)
    return render(request, "logs.html", runs=db.query("SELECT * FROM runs ORDER BY id DESC LIMIT 50"),
                  errors=db.query("SELECT * FROM error_log ORDER BY id DESC LIMIT 100"),
                  audit=db.query("SELECT * FROM audit_log ORDER BY id DESC LIMIT 150"))


# ---- draft actions ---------------------------------------------------------------------------

def _guard(request: Request, csrf_token: str) -> str:
    user = auth.current_user(request)
    auth.check_csrf(request, csrf_token)
    return user


@router.post("/drafts/{draft_id}/approve")
async def approve_draft(request: Request, draft_id: int, csrf_token: str = Form(""), scheduled_at: str = Form(""),
                        next: str = Form("/drafts")):
    user = _guard(request, csrf_token)
    try:
        job = approval.approve(db_of(request), request.app.state.settings, draft_id, user, _parse_local(scheduled_at, request))
    except approval.ApprovalError as e:
        return back(request, next, str(e), "error")
    when = db_of(request).scalar("SELECT scheduled_at FROM publish_jobs WHERE id = ?", (job,))
    return back(request, next, f"Approved. Scheduled for {_local(when, request.app.state.settings.schedule.tz)}.")


@router.post("/drafts/bulk-approve")
async def bulk_approve(request: Request, csrf_token: str = Form(""), ids: list[int] = Form(default=[])):
    user = _guard(request, csrf_token)
    if not ids:
        return back(request, "/drafts", "Select at least one draft.", "error")
    jobs, errors = approval.approve_many(db_of(request), request.app.state.settings, ids, user)
    msg = f"Approved {len(jobs)} draft(s)." + (f" {len(errors)} skipped: {'; '.join(errors)[:300]}" if errors else "")
    return back(request, "/drafts", msg, "error" if errors and not jobs else "ok")


@router.post("/drafts/{draft_id}/reject")
async def reject_draft(request: Request, draft_id: int, csrf_token: str = Form(""), note: str = Form(""),
                       next: str = Form("/drafts")):
    user = _guard(request, csrf_token)
    try:
        approval.reject(db_of(request), draft_id, user, note[:1000])
    except approval.ApprovalError as e:
        return back(request, next, str(e), "error")
    return back(request, next, "Draft rejected.")


@router.post("/drafts/{draft_id}/edit")
async def edit_draft(request: Request, draft_id: int, csrf_token: str = Form(""), text: str = Form(...),
                     media_url: str = Form(""), rereview: str = Form(""), next: str = Form("/drafts")):
    user = _guard(request, csrf_token)
    try:
        approval.edit(db_of(request), draft_id, user, text[:10000], media_url.strip())
    except approval.ApprovalError as e:
        return back(request, next, str(e), "error")
    if rereview:
        from ..main import background
        background(request.app, request.app.state.pipeline().rereview(draft_id, user), "rereview")
        return back(request, next, "Saved. The reviewer is checking your edit; refresh in a moment.")
    return back(request, next, "Saved. Edited drafts are marked as not re-reviewed until you run the reviewer.")


@router.post("/drafts/{draft_id}/rewrite")
async def rewrite_draft(request: Request, draft_id: int, csrf_token: str = Form(""), instructions: str = Form(""),
                        next: str = Form("/drafts")):
    user = _guard(request, csrf_token)
    from ..main import background
    background(request.app, request.app.state.pipeline().rewrite(draft_id, instructions[:2000], user), "rewrite")
    return back(request, next, "Rewrite requested. The new version goes through the reviewer again; refresh in a minute.")


@router.post("/drafts/{draft_id}/rereview")
async def rereview_draft(request: Request, draft_id: int, csrf_token: str = Form(""), next: str = Form("/drafts")):
    user = _guard(request, csrf_token)
    from ..main import background
    background(request.app, request.app.state.pipeline().rereview(draft_id, user), "rereview")
    return back(request, next, "Review started; refresh in a moment.")


@router.post("/drafts/{draft_id}/schedule")
async def schedule_draft(request: Request, draft_id: int, csrf_token: str = Form(""), scheduled_at: str = Form(...),
                         next: str = Form("/queue")):
    user = _guard(request, csrf_token)
    when = _parse_local(scheduled_at, request)
    try:
        approval.reschedule(db_of(request), request.app.state.settings, draft_id, when, user)
    except approval.ApprovalError as e:
        return back(request, next, str(e), "error")
    return back(request, next, "Rescheduled.")


# ---- queue actions -----------------------------------------------------------------------------

@router.post("/jobs/{job_id}/{action}")
async def job_action(request: Request, job_id: int, action: str, csrf_token: str = Form(""), url: str = Form(""),
                     confirm: str = Form("")):
    user = _guard(request, csrf_token)
    db = db_of(request)
    try:
        if action == "retry":
            publishing.retry(db, job_id, user, confirmed_not_posted=bool(confirm))
            msg = "Queued for another attempt."
        elif action == "mark-published":
            publishing.mark_published(db, job_id, url.strip(), user)
            msg = "Marked as published."
        elif action == "cancel":
            publishing.cancel(db, job_id, user)
            msg = "Cancelled; the draft is back in the approval queue."
        elif action == "requeue-live":
            if request.app.state.settings.publishing.dry_run or request.app.state.offline:
                raise publishing.QueueError("dry run is still on; set publishing.dry_run = false first")
            publishing.requeue_live(db, job_id, user)
            msg = "Queued for live publishing."
        else:
            raise HTTPException(404)
    except publishing.QueueError as e:
        return back(request, "/queue", str(e), "error")
    return back(request, "/queue", msg)


# ---- controls ------------------------------------------------------------------------------

@router.post("/controls/{action}")
async def control(request: Request, action: str, csrf_token: str = Form(""), reason: str = Form("")):
    user = _guard(request, csrf_token)
    db = db_of(request)
    from ..main import background
    if action == "pause":
        controls.pause(db, user, reason or "paused from the dashboard")
        return back(request, "/", "All publishing is paused. Nothing will be posted until you resume.")
    if action == "resume":
        controls.resume(db, user)
        return back(request, "/", "Publishing resumed.")
    if action == "auto-off":
        controls.set_auto_publish(db, False, user)
        return back(request, "/", "Automatic publishing is off; every post needs your approval.")
    if action == "auto-on":
        controls.set_auto_publish(db, True, user)
        _, why = controls.auto_publish_state(db, request.app.state.settings)
        return back(request, "/", f"Dashboard switch on. Current state: {why}.")
    if action in ("run-discovery", "run-publish", "run-metrics"):
        p = request.app.state.pipeline()
        coro = {"run-discovery": p.discover, "run-publish": p.publish, "run-metrics": p.metrics}[action](trigger="dashboard")
        background(request.app, coro, action)
        db.audit(user, action, "run")
        return back(request, "/", f"Started {action.removeprefix('run-')} run. It appears under Recent runs.")
    raise HTTPException(404)


# ---- API for schedulers (GitHub Actions) ----------------------------------------------------------

@router.post("/api/trigger")
async def api_trigger(request: Request, task: str = "discover"):
    auth.check_bearer(request, request.app.state.env.trigger_token)
    if task not in ("discover", "publish", "metrics", "all"):
        raise HTTPException(400, "task must be discover, publish, metrics or all")
    from ..main import background
    p = request.app.state.pipeline()

    async def run_all():
        await p.discover(trigger="api")
        await p.publish(trigger="api")
        await p.metrics(trigger="api")

    coro = run_all() if task == "all" else {"discover": p.discover, "publish": p.publish, "metrics": p.metrics}[task](trigger="api")
    background(request.app, coro, f"api:{task}")
    db_of(request).audit("api", f"trigger_{task}", "run", detail=str(utcnow()))
    return JSONResponse({"accepted": task}, status_code=202)
