"""Single-owner authentication for the dashboard.

Signed session cookies (Starlette SessionMiddleware, HttpOnly, SameSite=Lax,
Secure when COOKIE_SECURE=true), a CSRF token checked on every form POST,
PBKDF2 password hashes, and a simple per-IP lockout after repeated failures.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
import time

from fastapi import HTTPException, Request

from ..config import Env

MAX_FAILURES = 5
LOCKOUT_SECONDS = 300
_failures: dict[str, list[float]] = {}


class LoginRequired(Exception):
    pass


def auth_configured(env: Env) -> tuple[bool, str]:
    if not (env.dashboard_password or env.dashboard_password_hash):
        return False, "Set DASHBOARD_PASSWORD_HASH (python -m app hash-password) or DASHBOARD_PASSWORD in .env."
    if len(env.session_secret) < 32:
        return False, "Set SESSION_SECRET in .env to a random value of at least 32 characters."
    return True, ""


def _check_hash(password: str, stored: str) -> bool:
    try:
        algo, iterations, salt, digest = stored.split("$")
    except ValueError:
        return False
    if algo != "pbkdf2_sha256":
        return False
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), int(iterations)).hex()
    return hmac.compare_digest(candidate, digest)


def verify_credentials(env: Env, username: str, password: str) -> bool:
    user_ok = hmac.compare_digest(username.encode(), env.dashboard_username.encode())
    if env.dashboard_password_hash:
        pw_ok = _check_hash(password, env.dashboard_password_hash)
    else:
        pw_ok = bool(env.dashboard_password) and hmac.compare_digest(password.encode(), env.dashboard_password.encode())
    return user_ok and pw_ok


def locked_out(ip: str) -> bool:
    now = time.time()
    recent = [t for t in _failures.get(ip, []) if now - t < LOCKOUT_SECONDS]
    _failures[ip] = recent
    return len(recent) >= MAX_FAILURES


def record_failure(ip: str) -> None:
    _failures.setdefault(ip, []).append(time.time())


def clear_failures(ip: str) -> None:
    _failures.pop(ip, None)


def csrf_token(request: Request) -> str:
    token = request.session.get("csrf")
    if not token:
        token = secrets.token_urlsafe(32)
        request.session["csrf"] = token
    return token


def check_csrf(request: Request, submitted: str | None) -> None:
    expected = request.session.get("csrf")
    if not expected or not submitted or not hmac.compare_digest(expected, submitted):
        raise HTTPException(status_code=403, detail="Invalid or missing form token. Reload the page and try again.")


def current_user(request: Request) -> str:
    user = request.session.get("user")
    if not user:
        raise LoginRequired()
    return user


def check_bearer(request: Request, token: str) -> None:
    if len(token) < 24:
        raise HTTPException(status_code=503, detail="TRIGGER_TOKEN is not configured (needs 24+ characters)")
    header = request.headers.get("authorization", "")
    supplied = header[7:] if header.lower().startswith("bearer ") else ""
    if not supplied or not hmac.compare_digest(supplied.encode(), token.encode()):
        raise HTTPException(status_code=401, detail="invalid token")
