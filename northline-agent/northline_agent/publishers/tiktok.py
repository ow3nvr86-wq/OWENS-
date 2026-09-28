"""TikTok photo posts through the Content Posting API."""

import time

import requests

API = "https://open.tiktokapis.com/v2"


class TikTokError(RuntimeError):
    pass


def access_token(client_key: str, client_secret: str, refresh_token: str) -> tuple[str, str]:
    """Trades the long-lived refresh token for a 24-hour access token.

    Returns (access_token, refresh_token). TikTok may hand back a new refresh
    token; the caller warns you if it changed so you can update the secret.
    """
    resp = requests.post(
        f"{API}/oauth/token/",
        data={
            "client_key": client_key,
            "client_secret": client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
        timeout=60,
    )
    data = resp.json()
    if "access_token" not in data:
        raise TikTokError(f"Couldn't refresh the TikTok login: {data.get('error_description') or data}")
    return data["access_token"], data.get("refresh_token", refresh_token)


def exchange_code(client_key: str, client_secret: str, code: str, redirect_uri: str) -> dict:
    """One-time setup: turns the code from TikTok's login page into tokens."""
    resp = requests.post(
        f"{API}/oauth/token/",
        data={
            "client_key": client_key,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        },
        timeout=60,
    )
    data = resp.json()
    if "refresh_token" not in data:
        raise TikTokError(f"TikTok didn't accept the code: {data.get('error_description') or data}")
    return data


def _post(token: str, path: str, body: dict) -> dict:
    resp = requests.post(
        f"{API}/{path}",
        json=body,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=UTF-8"},
        timeout=60,
    )
    data = resp.json()
    error = data.get("error", {})
    if error.get("code") not in (None, "ok"):
        raise TikTokError(f"{error.get('message') or error.get('code')} ({path})")
    return data.get("data", {})


def privacy_level(token: str) -> str:
    """Public if the app is allowed to post publicly, otherwise private.

    Until TikTok audits the app, it may only post as private (SELF_ONLY).
    """
    options = _post(token, "post/publish/creator_info/query/", {}).get("privacy_level_options", [])
    return "PUBLIC_TO_EVERYONE" if "PUBLIC_TO_EVERYONE" in options else "SELF_ONLY"


def post_photos(token: str, image_urls: list[str], title: str, description: str) -> dict:
    privacy = privacy_level(token)
    publish_id = _post(
        token,
        "post/publish/content/init/",
        {
            "post_info": {
                "title": title[:89],
                "description": description[:4000],
                "privacy_level": privacy,
                "disable_comment": False,
                "auto_add_music": True,
            },
            "source_info": {"source": "PULL_FROM_URL", "photo_cover_index": 0, "photo_images": image_urls[:35]},
            "post_mode": "DIRECT_POST",
            "media_type": "PHOTO",
        },
    )["publish_id"]

    status = "PROCESSING"
    for _ in range(20):
        info = _post(token, "post/publish/status/fetch/", {"publish_id": publish_id})
        status = info.get("status", status)
        if status == "PUBLISH_COMPLETE":
            break
        if status == "FAILED":
            raise TikTokError(f"TikTok rejected the post: {info.get('fail_reason')}")
        time.sleep(5)
    # A post still processing after this is almost always published a minute later.
    return {"id": publish_id, "status": status, "privacy": privacy}
