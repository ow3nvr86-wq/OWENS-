"""Bluesky via the AT Protocol XRPC API.

Credentials: BLUESKY_HANDLE (e.g. yourname.bsky.social) and an app password
from Settings -> Privacy and security -> App passwords (never your main
password). BLUESKY_PDS defaults to https://bsky.social.

Idempotency: each job carries a record key (TID) generated once when the
draft was approved. createRecord is called with that key, so a retry can
never produce a second post, and an uncertain result is reconciled with
getRecord on the same key.
"""
from __future__ import annotations

import logging
import re

import httpx

from ..models import Outcome, PostMetrics, PublishResult
from ..textutil import make_tid, tid_micros, utf8_len
from ..timeutil import iso
from .base import Publisher, from_exception, from_response, structure

log = logging.getLogger(__name__)
COLLECTION = "app.bsky.feed.post"
PUBLIC_API = "https://public.api.bsky.app"
_URL = re.compile(r"https?://[^\s]+")
_TAG = re.compile(r"(?<![\w#])#([^\s#.,!?;:()\[\]{}\"']{1,64})")


def facets(text: str) -> list[dict]:
    """Link and hashtag facets; Bluesky needs UTF-8 byte offsets."""
    out = []
    for m in _URL.finditer(text):
        url = m.group(0).rstrip(".,;:!?)]'\"")
        start = utf8_len(text[: m.start()])
        out.append({"index": {"byteStart": start, "byteEnd": start + utf8_len(url)},
                    "features": [{"$type": "app.bsky.richtext.facet#link", "uri": url}]})
    for m in _TAG.finditer(text):
        start = utf8_len(text[: m.start()])
        out.append({"index": {"byteStart": start, "byteEnd": start + utf8_len(m.group(0))},
                    "features": [{"$type": "app.bsky.richtext.facet#tag", "tag": m.group(1)}]})
    return out


def thread_keys(job: dict, n: int) -> list[str]:
    """Record keys for a thread: the job's key for the first post and
    deterministic keys for the replies, so retries reuse the same keys."""
    base = tid_micros(job["client_ref"])
    return [job["client_ref"]] + [make_tid(f"{job['idempotency_key']}:{i}", base + i) for i in range(1, n)]


class BlueskyPublisher(Publisher):
    platform = "bluesky"
    required_env = ("BLUESKY_HANDLE", "BLUESKY_APP_PASSWORD")
    prerequisites = "A Bluesky account and an app password (Settings -> Privacy and security -> App passwords)."

    def __init__(self, env=None):
        super().__init__(env)
        self.pds = (self.env.get("BLUESKY_PDS") or "https://bsky.social").rstrip("/")
        self.session: dict | None = None

    async def _login(self, client: httpx.AsyncClient) -> dict:
        resp = await client.post(f"{self.pds}/xrpc/com.atproto.server.createSession", json={
            "identifier": self.env["BLUESKY_HANDLE"], "password": self.env["BLUESKY_APP_PASSWORD"]})
        if resp.status_code == 401:
            raise PermissionError("Bluesky rejected the handle or app password")
        if resp.status_code == 429:
            raise PermissionError("Bluesky login is rate limited (createSession allows few logins per day); wait and retry")
        resp.raise_for_status()
        self.session = resp.json()
        return self.session

    def _auth(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.session['accessJwt']}"}

    async def verify(self, client):
        ok, msg = self.configured()
        if not ok:
            return False, msg
        try:
            s = await self._login(client)
        except PermissionError as e:
            return False, str(e)
        except httpx.HTTPError as e:
            return False, f"could not reach {self.pds}: {type(e).__name__}"
        return True, f"logged in as @{s.get('handle')} ({s.get('did')})"

    def _record(self, text: str, lang: str, reply: dict | None) -> dict:
        record = {"$type": COLLECTION, "text": text, "createdAt": iso(), "langs": [lang]}
        if f := facets(text):
            record["facets"] = f
        if reply:
            record["reply"] = reply
        return record

    def _url(self, rkey: str) -> str:
        return f"https://bsky.app/profile/{self.session.get('handle')}/post/{rkey}"

    async def _get(self, client, rkey: str) -> tuple[str, dict | None]:
        """("found", record) / ("missing", None) / ("unknown", None)."""
        try:
            resp = await client.get(f"{self.pds}/xrpc/com.atproto.repo.getRecord", headers=self._auth(),
                                    params={"repo": self.session["did"], "collection": COLLECTION, "rkey": rkey})
        except httpx.HTTPError:
            return "unknown", None
        if resp.status_code == 200:
            return "found", resp.json()
        if resp.status_code == 400 and "RecordNotFound" in resp.text:
            return "missing", None
        return "unknown", None

    async def publish(self, client, job, draft):
        ok, msg = self.configured()
        if not ok:
            return PublishResult(Outcome.NOT_CONFIGURED, error=f"bluesky: {msg}")
        try:
            if not self.session:
                await self._login(client)
        except PermissionError as e:
            return PublishResult(Outcome.FAILED, error=f"bluesky: {e}")
        except httpx.HTTPError as e:
            return from_exception(e, self.platform)

        posts = [draft["post_text"], *structure(draft).get("thread_posts", [])]
        keys = thread_keys(job, len(posts))
        lang = (self.env.get("BLUESKY_LANG") or "en")[:8]
        root = parent = None
        first_uri = None
        for i, (text, rkey) in enumerate(zip(posts, keys)):
            state, existing = await self._get(client, rkey)
            if state == "found":
                ref = {"uri": existing["uri"], "cid": existing["cid"]}
            else:
                reply = {"root": root, "parent": parent} if root else None
                try:
                    resp = await client.post(
                        f"{self.pds}/xrpc/com.atproto.repo.createRecord", headers=self._auth(),
                        json={"repo": self.session["did"], "collection": COLLECTION, "rkey": rkey,
                              "record": self._record(text, lang, reply)})
                except httpx.HTTPError as e:
                    result = from_exception(e, self.platform)
                    if i and result.outcome == Outcome.FAILED:
                        result.outcome, result.error = Outcome.UNCERTAIN, f"thread partly posted: {result.error}"
                    return result
                if resp.status_code != 200:
                    if resp.status_code == 400 and "already exists" in resp.text.lower():
                        return await self.reconcile(client, job, draft) or PublishResult(
                            Outcome.UNCERTAIN, error="bluesky: record key already used; could not confirm")
                    result = from_response(resp, self.platform)
                    if i and result.outcome == Outcome.FAILED:
                        result.outcome, result.error = Outcome.UNCERTAIN, f"thread partly posted: {result.error}"
                    return result
                ref = {"uri": resp.json()["uri"], "cid": resp.json()["cid"]}
            if i == 0:
                root, first_uri = ref, ref["uri"]
            parent = ref
        return PublishResult(Outcome.SUCCESS, platform_post_id=first_uri, url=self._url(keys[0]),
                             detail={"posts": len(posts)})

    async def reconcile(self, client, job, draft):
        try:
            if not self.session:
                await self._login(client)
        except (PermissionError, httpx.HTTPError):
            return None
        state, record = await self._get(client, job["client_ref"])
        if state == "found":
            return PublishResult(Outcome.SUCCESS, platform_post_id=record["uri"], url=self._url(job["client_ref"]),
                                 detail={"reconciled": True})
        if state == "missing":
            return PublishResult(Outcome.FAILED, error="bluesky: confirmed the post was not created", retryable=True)
        return None

    async def metrics(self, client, post):
        if not post.get("platform_post_id", "").startswith("at://"):
            return None
        resp = await client.get(f"{PUBLIC_API}/xrpc/app.bsky.feed.getPosts", params={"uris": post["platform_post_id"]})
        if resp.status_code != 200:
            return None
        posts = resp.json().get("posts", [])
        if not posts:
            return None
        p = posts[0]
        # Bluesky exposes no view or click counts.
        return PostMetrics(likes=p.get("likeCount"), comments=p.get("replyCount"),
                           reposts=(p.get("repostCount") or 0) + (p.get("quoteCount") or 0),
                           raw={k: p.get(k) for k in ("likeCount", "replyCount", "repostCount", "quoteCount")})
