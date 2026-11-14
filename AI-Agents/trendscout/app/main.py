"""FastAPI application factory for the dashboard and the trigger API."""
from __future__ import annotations

import asyncio
import logging
import secrets
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from .config import Env, Settings, load_dotenv_if_present, load_settings
from .dashboard.auth import LoginRequired, auth_configured
from .database import Database
from .logging_config import setup_logging

log = logging.getLogger(__name__)
HERE = Path(__file__).resolve().parent / "dashboard"

SECURITY_HEADERS = {
    "Content-Security-Policy": "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; "
                               "frame-ancestors 'none'; form-action 'self'; base-uri 'none'",
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "same-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Cache-Control": "no-store",
}


def create_app(settings: Settings | None = None, env: Env | None = None, db: Database | None = None,
               offline: bool = False, pipeline_factory=None) -> FastAPI:
    from .dashboard.routes import router
    from .pipeline import Pipeline

    settings = settings or load_settings()
    env = env or Env.load()
    db = db or Database(env.database_path)
    db.migrate()

    app = FastAPI(title="Trend Scout", docs_url=None, redoc_url=None, openapi_url=None)
    ok, problem = auth_configured(env)
    if not ok:
        log.warning("dashboard login disabled until configured", extra={"problem": problem})
    # Without a configured secret, sessions use a random per-process key: nobody can log in
    # (no password), and nothing signed survives a restart.
    secret = env.session_secret if len(env.session_secret) >= 32 else secrets.token_urlsafe(48)
    app.add_middleware(SessionMiddleware, secret_key=secret, session_cookie="trendscout_session",
                       max_age=12 * 3600, same_site="lax", https_only=env.cookie_secure)

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        for k, v in SECURITY_HEADERS.items():
            response.headers.setdefault(k, v)
        return response

    @app.exception_handler(LoginRequired)
    async def _login_required(request: Request, exc: LoginRequired):
        return RedirectResponse("/login", status_code=303)

    app.state.settings = settings
    app.state.env = env
    app.state.db = db
    app.state.offline = offline
    app.state.tasks = set()
    app.state.pipeline = pipeline_factory or (lambda: Pipeline(settings, db, env, offline=offline))
    app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")
    app.include_router(router)
    return app


def background(app: FastAPI, coro, label: str) -> None:
    """Run a long task (discovery, rewrite) without blocking the request."""
    db: Database = app.state.db

    async def runner():
        try:
            await coro
        except Exception as e:  # recorded for the logs page
            log.exception("background task failed", extra={"task": label})
            db.log_error(f"dashboard:{label}", f"{type(e).__name__}: {e}")

    task = asyncio.create_task(runner())
    app.state.tasks.add(task)
    task.add_done_callback(app.state.tasks.discard)


def app_from_env() -> FastAPI:
    """Entry point for `uvicorn app.main:app_from_env --factory`."""
    load_dotenv_if_present()
    setup_logging()
    import os
    return create_app(offline=os.environ.get("TRENDSCOUT_OFFLINE", "").lower() in ("1", "true", "yes"))
