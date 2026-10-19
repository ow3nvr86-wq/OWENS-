"""Offline mode: an HTTP transport that answers from the files in fixtures/.

The real collectors and the research fetcher run unchanged on top of it, so
offline runs and tests exercise the same parsing code as live runs. Timestamps
in fixtures are written as {{unix:5h}}, {{rfc:2h}} or {{iso:30m}} and are
filled in relative to the current time, so sample trends never go stale.
"""
from __future__ import annotations

import json
import re
from datetime import timedelta
from email.utils import format_datetime
from pathlib import Path

import httpx

from .timeutil import iso, utcnow

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
_PLACEHOLDER = re.compile(r'"?\{\{(unix|rfc|iso):(\d+)([mhd])\}\}"?')
OFFLINE_ENV = {
    "REDDIT_CLIENT_ID": "offline", "REDDIT_CLIENT_SECRET": "offline",
    "REDDIT_USER_AGENT": "script:trendscout-offline:1.0 (by /u/sample)",
    "YOUTUBE_API_KEY": "offline", "X_BEARER_TOKEN": "offline",
}


def render(text: str) -> str:
    now = utcnow()

    def sub(m: re.Match) -> str:
        unit = {"m": "minutes", "h": "hours", "d": "days"}[m.group(3)]
        when = now - timedelta(**{unit: int(m.group(2))})
        quoted = m.group(0).startswith('"')
        if m.group(1) == "unix":
            return str(int(when.timestamp()))
        value = format_datetime(when) if m.group(1) == "rfc" else iso(when)
        return f'"{value}"' if quoted else value

    return _PLACEHOLDER.sub(sub, text)


def _file(name: str) -> str:
    return render((FIXTURES / name).read_text())


def _json(name: str) -> httpx.Response:
    return httpx.Response(200, content=_file(name).encode(), headers={"content-type": "application/json"})


def handler(request: httpx.Request) -> httpx.Response:
    host, path = request.url.host, request.url.path
    if host == "hacker-news.firebaseio.com":
        if m := re.match(r"/v0/(top|best|new)stories\.json", path):
            return _json(f"hn_{m.group(1)}stories.json")
        if m := re.match(r"/v0/item/(\d+)\.json", path):
            items = json.loads(_file("hn_items.json"))
            return httpx.Response(200, json=items.get(m.group(1)))
    if host == "trends.google.com" and path.startswith("/trending/rss"):
        return httpx.Response(200, content=_file("google_trends.xml").encode())
    if host == "feeds.bbci.co.uk":
        return httpx.Response(200, content=_file("rss_a.xml").encode())
    if host == "feeds.arstechnica.com":
        return httpx.Response(200, content=_file("rss_b.xml").encode())
    if host == "www.reddit.com" and path == "/api/v1/access_token":
        return _json("reddit_token.json")
    if host == "oauth.reddit.com":
        if path == "/r/popular/hot":
            return _json("reddit_hot.json")
        return httpx.Response(200, json={"kind": "Listing", "data": {"children": []}},
                              headers={"x-ratelimit-remaining": "95"})
    if host == "www.googleapis.com" and path == "/youtube/v3/videos":
        return _json("youtube_videos.json")
    if host == "api.x.com" and path.startswith("/2/trends/by/woeid/"):
        return _json("x_trends.json")
    if host in ("example.com", "example.org", "example.net"):
        page = FIXTURES / "articles" / f"{path.strip('/').split('/')[-1]}.html"
        if page.exists():
            return httpx.Response(200, content=render(page.read_text()).encode(),
                                  headers={"content-type": "text/html; charset=utf-8"})
    # Anything else (e.g. the other configured feeds) is unreachable offline,
    # which also demonstrates that one failed source does not stop a run.
    return httpx.Response(404, text="not available in offline mode")


def offline_transport() -> httpx.MockTransport:
    return httpx.MockTransport(handler)
