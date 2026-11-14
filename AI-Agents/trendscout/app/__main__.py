"""Command line: `python -m app <command>`. Run `python -m app --help`."""
from __future__ import annotations

import argparse
import asyncio
import getpass
import hashlib
import json
import os
import secrets
import sys

from .config import Env, load_dotenv_if_present, load_settings
from .database import Database
from .logging_config import setup_logging
from .timeutil import iso


def hash_password(password: str, salt: str | None = None, iterations: int = 600_000) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations).hex()
    return f"pbkdf2_sha256${iterations}${salt}${digest}"


def build(args) -> tuple:
    from .pipeline import Pipeline
    settings = load_settings(args.config)
    env = Env.load()
    db = Database(env.database_path)
    db.migrate()
    return settings, env, db, Pipeline(settings, db, env, offline=getattr(args, "offline", False))


def _print(obj) -> None:
    print(json.dumps(obj, indent=2, default=str, ensure_ascii=False))


async def doctor(settings, env, db, pipeline) -> dict:
    """Check configuration and credentials without posting anything."""
    from .collectors.base import all_collectors
    from .services import controls
    out: dict = {"database": str(env.database_path), "dry_run": settings.publishing.dry_run,
                 "require_human_approval": settings.publishing.require_human_approval,
                 "auto_publish": controls.auto_publish_state(db, settings)[1],
                 "anthropic_api_key": "set" if env.anthropic_api_key else "missing (AI steps disabled)",
                 "dashboard_auth": "configured" if (env.dashboard_password or env.dashboard_password_hash) and len(env.session_secret) >= 32
                 else "NOT configured: set DASHBOARD_PASSWORD(_HASH) and a 32+ character SESSION_SECRET",
                 "collectors": {}, "platforms": {}}
    for c in all_collectors():
        out["collectors"][c.name] = "enabled" if c.enabled(settings) else "disabled"
    async with pipeline.client() as client:
        for name, pub in pipeline.publishers.items():
            enabled = settings.platforms[name].enabled
            ok, msg = pub.configured()
            if ok:
                try:
                    ok, msg = await pub.verify(client)
                except Exception as e:  # noqa: BLE001
                    ok, msg = False, f"{type(e).__name__}: {e}"
            status = "verified" if ok else ("unconfigured" if msg.startswith("missing") else "error")
            db.execute("INSERT INTO platform_accounts (platform, status, detail, last_checked_at) VALUES (?, ?, ?, ?) "
                       "ON CONFLICT(platform) DO UPDATE SET status = excluded.status, detail = excluded.detail, "
                       "last_checked_at = excluded.last_checked_at", (name, status, msg, iso()))
            out["platforms"][name] = {"enabled_in_config": enabled, "status": status, "detail": msg,
                                      "prerequisites": pub.prerequisites}
    return out


async def test_post(settings, env, db, pipeline, platform: str, text: str) -> dict:
    """Publish one real post, outside the queue, after explicit confirmation."""
    from .models import Outcome
    pub = pipeline.publishers.get(platform)
    if not pub:
        return {"error": f"unknown platform {platform}"}
    from .textutil import make_tid
    seed = f"test:{secrets.token_hex(8)}"
    job = {"id": 0, "client_ref": make_tid(seed), "idempotency_key": seed, "platform": platform}
    async with pipeline.client() as client:
        result = await pub.publish(client, job, {"post_text": text, "structure_json": "{}"})
    db.audit("cli", "test_post", "platform", platform, outcome=result.outcome.value, url=result.url, error=result.error)
    return {"outcome": result.outcome.value, "url": result.url, "post_id": result.platform_post_id,
            "error": result.error, "ok": result.outcome == Outcome.SUCCESS}


def main(argv: list[str] | None = None) -> int:
    load_dotenv_if_present()
    p = argparse.ArgumentParser(prog="python -m app", description="Trend Scout")
    p.add_argument("--config", help="path to trendscout.toml (default: config/trendscout.toml or $TRENDSCOUT_CONFIG)")
    p.add_argument("--log-level", default=os.environ.get("LOG_LEVEL", "INFO"))
    sub = p.add_subparsers(dest="cmd", required=True)
    for name, help_ in [("discover", "collect, rank, research, write and review"), ("publish", "publish approved posts that are due"),
                        ("metrics", "collect performance metrics and update learning"), ("run-all", "discover, publish and metrics")]:
        sp = sub.add_parser(name, help=help_)
        sp.add_argument("--offline", action="store_true", help="use sample fixtures and the simulated model; never publishes")
    sp = sub.add_parser("scheduler", help="run the scheduler loop (discovery times, publishing, metrics)")
    sp.add_argument("--offline", action="store_true")
    sp = sub.add_parser("serve", help="run the dashboard")
    sp.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"))
    sp.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8000")))
    sp.add_argument("--offline", action="store_true", help="dashboard actions use fixtures and the simulated model")
    sub.add_parser("init-db", help="create or migrate the database")
    sub.add_parser("check-config", help="validate config/trendscout.toml")
    sub.add_parser("doctor", help="check configuration and platform credentials (posts nothing)")
    sub.add_parser("hash-password", help="hash a dashboard password for DASHBOARD_PASSWORD_HASH")
    sp = sub.add_parser("test-post", help="publish ONE real post to verify a platform connection")
    sp.add_argument("platform")
    sp.add_argument("--text", required=True)
    sp.add_argument("--yes", action="store_true", help="skip the confirmation prompt")
    sp = sub.add_parser("pause", help="stop all publishing immediately (kill switch)")
    sp.add_argument("--reason", default="paused from the command line")
    sub.add_parser("resume", help="lift the kill switch")
    args = p.parse_args(argv)
    setup_logging(args.log_level)

    if args.cmd == "hash-password":
        pw = getpass.getpass("Password: ")
        if len(pw) < 12:
            print("Use at least 12 characters.", file=sys.stderr)
            return 1
        print(hash_password(pw))
        return 0
    if args.cmd == "check-config":
        s = load_settings(args.config)
        _print({"ok": True, "account": s.account.name, "platforms": s.enabled_platforms,
                "weights": s.scoring.weights.normalized(), "timezone": s.schedule.timezone})
        return 0

    settings, env, db, pipeline = build(args)
    from .services import controls
    if args.cmd == "init-db":
        _print({"database": str(env.database_path), "applied": db.migrate() or "up to date"})
    elif args.cmd == "discover":
        _print(asyncio.run(pipeline.discover(trigger="cli")))
    elif args.cmd == "publish":
        _print(asyncio.run(pipeline.publish(trigger="cli")))
    elif args.cmd == "metrics":
        _print(asyncio.run(pipeline.metrics(trigger="cli")))
    elif args.cmd == "run-all":
        async def all_() -> dict:
            return {"discover": await pipeline.discover(trigger="cli"), "publish": await pipeline.publish(trigger="cli"),
                    "metrics": await pipeline.metrics(trigger="cli")}
        _print(asyncio.run(all_()))
    elif args.cmd == "scheduler":
        from .pipeline import Pipeline
        from .services.scheduler import run_forever
        asyncio.run(run_forever(lambda: Pipeline(settings, db, env, offline=args.offline), settings, db))
    elif args.cmd == "serve":
        import uvicorn
        from .main import create_app
        uvicorn.run(create_app(settings=settings, env=env, db=db, offline=args.offline), host=args.host, port=args.port,
                    proxy_headers=True, log_config=None)
    elif args.cmd == "doctor":
        _print(asyncio.run(doctor(settings, env, db, pipeline)))
    elif args.cmd == "test-post":
        if not args.yes:
            answer = input(f"This publishes a real, public post to {args.platform}:\n\n{args.text}\n\nType 'publish' to continue: ")
            if answer.strip() != "publish":
                print("Cancelled.")
                return 1
        result = asyncio.run(test_post(settings, env, db, pipeline, args.platform, args.text))
        _print(result)
        return 0 if result.get("ok") else 1
    elif args.cmd == "pause":
        controls.pause(db, "cli", args.reason)
        _print({"paused": True})
    elif args.cmd == "resume":
        controls.resume(db, "cli")
        _print({"paused": False})
    return 0


if __name__ == "__main__":
    sys.exit(main())
