"""X (Twitter) API v2, POST /2/tweets, OAuth 1.0a user context.

Prerequisites: a developer account and project on an X API tier that allows
posting, an app with "Read and write" permissions, and the user's access
token and secret generated after setting that permission. Reading metrics
and reconciling needs a tier with read access; without it uncertain results
are left for a person to resolve on the queue page.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import time
from urllib.parse import quote, urlsplit, parse_qsl

import httpx

from ..models import Outcome, PostMetrics, PublishResult
from .base import Publisher, from_exception, from_response, structure

API = "https://api.x.com/2"


def _pct(s: str) -> str:
    return quote(s, safe="~-._")


def oauth1_header(method: str, url: str, consumer_key: str, consumer_secret: str, token: str, token_secret: str,
                  nonce: str | None = None, timestamp: str | None = None,
                  form_params: dict[str, str] | None = None) -> str:
    parts = urlsplit(url)
    base_url = f"{parts.scheme}://{parts.netloc}{parts.path}"
    oauth = {
        "oauth_consumer_key": consumer_key, "oauth_nonce": nonce or secrets.token_hex(16),
        "oauth_signature_method": "HMAC-SHA1", "oauth_timestamp": timestamp or str(int(time.time())),
        "oauth_token": token, "oauth_version": "1.0",
    }
    # Query and form-encoded body parameters are signed; JSON bodies (what API v2 uses) are not.
    params = sorted([*oauth.items(), *parse_qsl(parts.query), *(form_params or {}).items()])
    param_str = "&".join(f"{_pct(k)}={_pct(v)}" for k, v in params)
    base = "&".join([method.upper(), _pct(base_url), _pct(param_str)])
    key = f"{_pct(consumer_secret)}&{_pct(token_secret)}"
    oauth["oauth_signature"] = base64.b64encode(hmac.new(key.encode(), base.encode(), hashlib.sha1).digest()).decode()
    return "OAuth " + ", ".join(f'{_pct(k)}="{_pct(v)}"' for k, v in sorted(oauth.items()))


class XPublisher(Publisher):
    platform = "x"
    required_env = ("X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET")
    prerequisites = ("X developer account on a tier that permits posting; app permission 'Read and write'; "
                     "user access token + secret generated after enabling write access.")

    def _auth(self, method: str, url: str) -> dict[str, str]:
        e = self.env
        return {"Authorization": oauth1_header(method, url, e["X_API_KEY"], e["X_API_SECRET"],
                                               e["X_ACCESS_TOKEN"], e["X_ACCESS_TOKEN_SECRET"])}

    async def verify(self, client):
        ok, msg = self.configured()
        if not ok:
            return False, msg
        url = f"{API}/users/me"
        try:
            resp = await client.get(url, headers=self._auth("GET", url))
        except httpx.HTTPError as e:
            return False, f"could not reach X: {type(e).__name__}"
        if resp.status_code == 200:
            return True, f"authenticated as @{resp.json().get('data', {}).get('username')}"
        return False, f"X returned HTTP {resp.status_code}: {resp.text[:200]}"

    async def publish(self, client, job, draft):
        ok, msg = self.configured()
        if not ok:
            return PublishResult(Outcome.NOT_CONFIGURED, error=f"x: {msg}")
        posts = [draft["post_text"], *structure(draft).get("thread_posts", [])]
        url = f"{API}/tweets"
        first_id = previous = None
        for i, text in enumerate(posts):
            body: dict = {"text": text}
            if previous:
                body["reply"] = {"in_reply_to_tweet_id": previous}
            try:
                resp = await client.post(url, json=body, headers=self._auth("POST", url))
            except httpx.HTTPError as e:
                r = from_exception(e, self.platform)
                if i:
                    r.outcome, r.error = Outcome.UNCERTAIN, f"thread partly posted: {r.error}"
                return r
            if resp.status_code not in (200, 201):
                r = from_response(resp, self.platform)
                if i and r.outcome == Outcome.FAILED:
                    r.outcome, r.error = Outcome.UNCERTAIN, f"thread partly posted: {r.error}"
                return r
            previous = resp.json()["data"]["id"]
            first_id = first_id or previous
        return PublishResult(Outcome.SUCCESS, platform_post_id=first_id, url=f"https://x.com/i/web/status/{first_id}")

    async def reconcile(self, client, job, draft):
        """Look for the exact text among the account's latest posts (needs read access)."""
        try:
            me_url = f"{API}/users/me"
            me = await client.get(me_url, headers=self._auth("GET", me_url))
            if me.status_code != 200:
                return None
            uid = me.json()["data"]["id"]
            tl_url = f"{API}/users/{uid}/tweets?max_results=20"
            tl = await client.get(tl_url, headers=self._auth("GET", tl_url))
        except (httpx.HTTPError, KeyError):
            return None
        if tl.status_code != 200:
            return None
        for t in tl.json().get("data", []):
            if t.get("text", "").strip() == draft["post_text"].strip():
                return PublishResult(Outcome.SUCCESS, platform_post_id=t["id"], url=f"https://x.com/i/web/status/{t['id']}",
                                     detail={"reconciled": True})
        # Absence from the latest 20 is strong but not certain evidence; let a person decide.
        return None

    async def metrics(self, client, post):
        pid = post.get("platform_post_id")
        if not pid:
            return None
        url = f"{API}/tweets?ids={pid}&tweet.fields=public_metrics"
        resp = await client.get(url, headers=self._auth("GET", url))
        if resp.status_code != 200 or not resp.json().get("data"):
            return None
        m = resp.json()["data"][0].get("public_metrics", {})
        return PostMetrics(impressions=m.get("impression_count"), likes=m.get("like_count"),
                           comments=m.get("reply_count"),
                           reposts=(m.get("retweet_count") or 0) + (m.get("quote_count") or 0), raw=m)
