"""Instagram Graph API content publishing (image posts).

Prerequisites: an Instagram professional (Business or Creator) account, a Meta
app with instagram_content_publish permission (app review for public use),
a long-lived access token (INSTAGRAM_ACCESS_TOKEN) and the Instagram user id
(INSTAGRAM_USER_ID). Instagram cannot publish text alone: each draft needs a
public HTTPS JPEG URL, added on the dashboard as the draft's media URL.
INSTAGRAM_GRAPH_VERSION should be set to a current Graph API version.
"""
from __future__ import annotations

import httpx

from ..models import Outcome, PostMetrics, PublishResult
from .base import Publisher, from_exception, from_response, structure


class InstagramPublisher(Publisher):
    platform = "instagram"
    required_env = ("INSTAGRAM_USER_ID", "INSTAGRAM_ACCESS_TOKEN")
    prerequisites = ("Instagram professional account linked to a Meta app with instagram_content_publish "
                     "(app review), a long-lived token, and a public image URL for every post.")

    @property
    def api(self) -> str:
        return f"https://graph.facebook.com/{self.env.get('INSTAGRAM_GRAPH_VERSION') or 'v23.0'}"

    def _p(self, **extra) -> dict:
        return {"access_token": self.env["INSTAGRAM_ACCESS_TOKEN"], **extra}

    async def verify(self, client):
        ok, msg = self.configured()
        if not ok:
            return False, msg
        try:
            resp = await client.get(f"{self.api}/{self.env['INSTAGRAM_USER_ID']}", params=self._p(fields="username"))
        except httpx.HTTPError as e:
            return False, f"could not reach Instagram: {type(e).__name__}"
        if resp.status_code == 200:
            return True, f"authenticated as @{resp.json().get('username')}"
        return False, f"Instagram returned HTTP {resp.status_code}: {resp.text[:200]}"

    async def publish(self, client, job, draft):
        ok, msg = self.configured()
        if not ok:
            return PublishResult(Outcome.NOT_CONFIGURED, error=f"instagram: {msg}")
        media_url = structure(draft).get("media_url")
        if not media_url:
            return PublishResult(Outcome.NOT_CONFIGURED,
                                 error="instagram: this draft has no image; add a public https image URL on the dashboard")
        uid = self.env["INSTAGRAM_USER_ID"]
        try:
            c = await client.post(f"{self.api}/{uid}/media", params=self._p(image_url=media_url, caption=draft["post_text"]))
        except httpx.HTTPError as e:
            r = from_exception(e, self.platform)
            r.outcome, r.retryable = Outcome.FAILED, True  # a container is private until published
            return r
        if c.status_code != 200:
            r = from_response(c, self.platform)
            if r.outcome == Outcome.UNCERTAIN:
                r.outcome, r.retryable = Outcome.FAILED, True
            return r
        try:
            p = await client.post(f"{self.api}/{uid}/media_publish", params=self._p(creation_id=c.json()["id"]))
        except httpx.HTTPError as e:
            return from_exception(e, self.platform)
        if p.status_code != 200:
            return from_response(p, self.platform)
        media_id = p.json()["id"]
        url = None
        try:
            link = await client.get(f"{self.api}/{media_id}", params=self._p(fields="permalink"))
            url = link.json().get("permalink") if link.status_code == 200 else None
        except httpx.HTTPError:
            pass
        return PublishResult(Outcome.SUCCESS, platform_post_id=media_id, url=url)

    async def reconcile(self, client, job, draft):
        uid = self.env.get("INSTAGRAM_USER_ID")
        if not uid:
            return None
        try:
            resp = await client.get(f"{self.api}/{uid}/media", params=self._p(fields="id,caption,permalink", limit=25))
        except httpx.HTTPError:
            return None
        if resp.status_code != 200:
            return None
        for m in resp.json().get("data", []):
            if (m.get("caption") or "").strip() == draft["post_text"].strip():
                return PublishResult(Outcome.SUCCESS, platform_post_id=m["id"], url=m.get("permalink"),
                                     detail={"reconciled": True})
        return None

    async def metrics(self, client, post):
        pid = post.get("platform_post_id")
        if not pid:
            return None
        resp = await client.get(f"{self.api}/{pid}/insights", params=self._p(metric="reach,likes,comments,shares"))
        if resp.status_code != 200:
            return None
        values = {d["name"]: (d.get("values") or [{}])[0].get("value") for d in resp.json().get("data", [])}
        return PostMetrics(impressions=values.get("reach"), likes=values.get("likes"), comments=values.get("comments"),
                           reposts=values.get("shares"), raw=values)
