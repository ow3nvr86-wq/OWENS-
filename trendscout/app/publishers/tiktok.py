"""TikTok Content Posting API (Direct Post, video pulled from a URL).

Prerequisites: a TikTok developer app with the Content Posting API and the
video.publish scope, a user access token (TIKTOK_ACCESS_TOKEN), and a
recorded video at a public HTTPS URL on a domain verified in the TikTok
developer portal (added on the dashboard as the draft's media URL).
Until the app passes TikTok's audit, posts can only be SELF_ONLY (private);
TIKTOK_PRIVACY_LEVEL defaults to that. Text-only posting is not possible.
"""
from __future__ import annotations

import httpx

from ..models import Outcome, PublishResult
from .base import Publisher, from_exception, from_response, structure

API = "https://open.tiktokapis.com/v2"


class TikTokPublisher(Publisher):
    platform = "tiktok"
    required_env = ("TIKTOK_ACCESS_TOKEN",)
    prerequisites = ("TikTok app with Content Posting API (video.publish), a user token, a recorded video on a "
                     "verified domain; unaudited apps can only post privately.")

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.env['TIKTOK_ACCESS_TOKEN']}", "Content-Type": "application/json; charset=UTF-8"}

    async def verify(self, client):
        ok, msg = self.configured()
        if not ok:
            return False, msg
        try:
            resp = await client.post(f"{API}/post/publish/creator_info/query/", headers=self._headers())
        except httpx.HTTPError as e:
            return False, f"could not reach TikTok: {type(e).__name__}"
        data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
        if resp.status_code == 200 and data.get("error", {}).get("code") == "ok":
            info = data.get("data", {})
            return True, f"creator @{info.get('creator_username')}; allowed privacy: {info.get('privacy_level_options')}"
        return False, f"TikTok returned HTTP {resp.status_code}: {resp.text[:200]}"

    async def publish(self, client, job, draft):
        ok, msg = self.configured()
        if not ok:
            return PublishResult(Outcome.NOT_CONFIGURED, error=f"tiktok: {msg}")
        video = structure(draft).get("media_url")
        if not video:
            return PublishResult(Outcome.NOT_CONFIGURED,
                                 error="tiktok: record the video and add its public URL to the draft first")
        body = {
            "post_info": {"title": draft["post_text"][:2200],
                          "privacy_level": self.env.get("TIKTOK_PRIVACY_LEVEL") or "SELF_ONLY",
                          "disable_comment": False, "disable_duet": False, "disable_stitch": False},
            "source_info": {"source": "PULL_FROM_URL", "video_url": video},
        }
        try:
            resp = await client.post(f"{API}/post/publish/video/init/", json=body, headers=self._headers())
        except httpx.HTTPError as e:
            return from_exception(e, self.platform)
        if resp.status_code != 200:
            return from_response(resp, self.platform)
        publish_id = resp.json().get("data", {}).get("publish_id")
        # Processing is asynchronous: the job is uncertain until the status endpoint confirms it.
        return PublishResult(Outcome.UNCERTAIN, platform_post_id=publish_id,
                             error="tiktok: upload accepted; waiting for processing", detail={"publish_id": publish_id})

    async def reconcile(self, client, job, draft):
        publish_id = job.get("platform_ref")
        if not publish_id:
            return None
        try:
            resp = await client.post(f"{API}/post/publish/status/fetch/", json={"publish_id": publish_id},
                                     headers=self._headers())
        except httpx.HTTPError:
            return None
        status = resp.json().get("data", {}).get("status") if resp.status_code == 200 else None
        if status == "PUBLISH_COMPLETE":
            return PublishResult(Outcome.SUCCESS, platform_post_id=publish_id, detail={"reconciled": True})
        if status == "FAILED":
            return PublishResult(Outcome.FAILED, error="tiktok: processing failed", retryable=False)
        return None
