"""Threads (Meta) API: create a TEXT container, then publish it.

Prerequisites: a Meta developer app with the Threads use case, the
threads_basic and threads_content_publish permissions (app review for use
beyond your own test accounts), and a long-lived user access token
(THREADS_ACCESS_TOKEN, valid 60 days; refresh before it expires) plus the
Threads user id (THREADS_USER_ID). Insights need threads_manage_insights.
"""
from __future__ import annotations

import httpx

from ..models import Outcome, PostMetrics, PublishResult
from .base import Publisher, from_exception, from_response

API = "https://graph.threads.net/v1.0"


class ThreadsPublisher(Publisher):
    platform = "threads"
    required_env = ("THREADS_USER_ID", "THREADS_ACCESS_TOKEN")
    prerequisites = ("Meta app with the Threads API use case, threads_content_publish permission (app review for "
                     "public use) and a long-lived token.")

    def _p(self, **extra) -> dict:
        return {"access_token": self.env["THREADS_ACCESS_TOKEN"], **extra}

    async def verify(self, client):
        ok, msg = self.configured()
        if not ok:
            return False, msg
        try:
            resp = await client.get(f"{API}/me", params=self._p(fields="id,username"))
        except httpx.HTTPError as e:
            return False, f"could not reach Threads: {type(e).__name__}"
        if resp.status_code == 200:
            return True, f"authenticated as @{resp.json().get('username')}"
        return False, f"Threads returned HTTP {resp.status_code}: {resp.text[:200]}"

    async def publish(self, client, job, draft):
        ok, msg = self.configured()
        if not ok:
            return PublishResult(Outcome.NOT_CONFIGURED, error=f"threads: {msg}")
        uid = self.env["THREADS_USER_ID"]
        try:
            # Creating a container is not public; repeating it is harmless.
            c = await client.post(f"{API}/{uid}/threads", params=self._p(media_type="TEXT", text=draft["post_text"]))
        except httpx.HTTPError as e:
            r = from_exception(e, self.platform)
            if r.outcome == Outcome.UNCERTAIN:  # only a container could exist; nothing is public yet
                r.outcome, r.retryable = Outcome.FAILED, True
            return r
        if c.status_code != 200:
            r = from_response(c, self.platform)
            if r.outcome == Outcome.UNCERTAIN:
                r.outcome, r.retryable = Outcome.FAILED, True
            return r
        try:
            p = await client.post(f"{API}/{uid}/threads_publish", params=self._p(creation_id=c.json()["id"]))
        except httpx.HTTPError as e:
            return from_exception(e, self.platform)
        if p.status_code != 200:
            return from_response(p, self.platform)
        media_id = p.json()["id"]
        url = None
        try:
            link = await client.get(f"{API}/{media_id}", params=self._p(fields="permalink"))
            url = link.json().get("permalink") if link.status_code == 200 else None
        except httpx.HTTPError:
            pass
        return PublishResult(Outcome.SUCCESS, platform_post_id=media_id, url=url)

    async def reconcile(self, client, job, draft):
        uid = self.env.get("THREADS_USER_ID")
        if not uid:
            return None
        try:
            resp = await client.get(f"{API}/{uid}/threads", params=self._p(fields="id,text,permalink", limit=25))
        except httpx.HTTPError:
            return None
        if resp.status_code != 200:
            return None
        for t in resp.json().get("data", []):
            if (t.get("text") or "").strip() == draft["post_text"].strip():
                return PublishResult(Outcome.SUCCESS, platform_post_id=t["id"], url=t.get("permalink"),
                                     detail={"reconciled": True})
        return None

    async def metrics(self, client, post):
        pid = post.get("platform_post_id")
        if not pid:
            return None
        resp = await client.get(f"{API}/{pid}/insights", params=self._p(metric="views,likes,replies,reposts,quotes"))
        if resp.status_code != 200:
            return None
        values = {d["name"]: (d.get("values") or [{}])[0].get("value") for d in resp.json().get("data", [])}
        return PostMetrics(impressions=values.get("views"), likes=values.get("likes"), comments=values.get("replies"),
                           reposts=(values.get("reposts") or 0) + (values.get("quotes") or 0), raw=values)
