"""LinkedIn Posts API (POST /rest/posts).

Prerequisites: a LinkedIn developer app with the "Share on LinkedIn" product
(w_member_social scope) for personal posts, or Community Management API
access (w_organization_social) for a company page; a 3-legged OAuth access
token (LINKEDIN_ACCESS_TOKEN, about 60 days); and the author URN
(LINKEDIN_AUTHOR_URN, urn:li:person:... or urn:li:organization:...).
LINKEDIN_VERSION is the monthly API version (YYYYMM); LinkedIn supports each
version for about a year, so keep it current.
Post analytics for personal profiles are not available to most apps, so
metrics are left empty rather than guessed.
"""
from __future__ import annotations

import re

import httpx

from ..models import Outcome, PublishResult
from .base import Publisher, from_exception, from_response

API = "https://api.linkedin.com/rest"
_RESERVED = re.compile(r"([\\|{}@\[\]()<>#*_~])")


def escape_commentary(text: str) -> str:
    """LinkedIn's 'little' text format treats these characters as markup."""
    return _RESERVED.sub(r"\\\1", text)


class LinkedInPublisher(Publisher):
    platform = "linkedin"
    required_env = ("LINKEDIN_ACCESS_TOKEN", "LINKEDIN_AUTHOR_URN")
    prerequisites = ("LinkedIn app with 'Share on LinkedIn' (w_member_social) or Community Management API access, "
                     "an OAuth token and the author URN.")

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.env['LINKEDIN_ACCESS_TOKEN']}",
                "LinkedIn-Version": self.env.get("LINKEDIN_VERSION") or "202609",
                "X-Restli-Protocol-Version": "2.0.0"}

    async def verify(self, client):
        ok, msg = self.configured()
        if not ok:
            return False, msg
        try:
            resp = await client.get("https://api.linkedin.com/v2/userinfo",
                                    headers={"Authorization": f"Bearer {self.env['LINKEDIN_ACCESS_TOKEN']}"})
        except httpx.HTTPError as e:
            return False, f"could not reach LinkedIn: {type(e).__name__}"
        if resp.status_code == 200:
            return True, f"token valid for {resp.json().get('name', 'member')}"
        return False, f"LinkedIn returned HTTP {resp.status_code} (the userinfo check needs the openid/profile scopes)"

    async def publish(self, client, job, draft):
        ok, msg = self.configured()
        if not ok:
            return PublishResult(Outcome.NOT_CONFIGURED, error=f"linkedin: {msg}")
        body = {
            "author": self.env["LINKEDIN_AUTHOR_URN"], "commentary": escape_commentary(draft["post_text"]),
            "visibility": "PUBLIC", "lifecycleState": "PUBLISHED", "isReshareDisabledByAuthor": False,
            "distribution": {"feedDistribution": "MAIN_FEED", "targetEntities": [], "thirdPartyDistributionChannels": []},
        }
        try:
            resp = await client.post(f"{API}/posts", json=body, headers=self._headers())
        except httpx.HTTPError as e:
            return from_exception(e, self.platform)
        if resp.status_code != 201:
            return from_response(resp, self.platform)
        urn = resp.headers.get("x-restli-id", "")
        return PublishResult(Outcome.SUCCESS, platform_post_id=urn,
                             url=f"https://www.linkedin.com/feed/update/{urn}/" if urn else None)
