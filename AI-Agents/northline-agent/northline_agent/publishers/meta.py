"""Instagram carousel and Facebook Page multi-photo posts through Meta's Graph API."""

import json
import time

import requests

GRAPH = "https://graph.facebook.com/v23.0"


class MetaError(RuntimeError):
    pass


def _request(method: str, path: str, token: str, **params) -> dict:
    payload = {**params, "access_token": token}
    if method == "GET":
        resp = requests.get(f"{GRAPH}/{path}", params=payload, timeout=120)
    else:
        resp = requests.post(f"{GRAPH}/{path}", data=payload, timeout=120)
    data = resp.json()
    if "error" in data:
        err = data["error"]
        raise MetaError(f"{err.get('message')} (code {err.get('code')}, {path})")
    return data


def _page_token(token: str, page_id: str) -> str:
    """Posting to a Page needs a Page token; derive it if we were given a user or system-user token."""
    try:
        return _request("GET", page_id, token, fields="access_token").get("access_token") or token
    except MetaError:
        return token  # already a Page token


def post_instagram(token: str, ig_user_id: str, image_urls: list[str], caption: str) -> dict:
    children = [
        _request("POST", f"{ig_user_id}/media", token, image_url=url, is_carousel_item="true")["id"]
        for url in image_urls[:10]
    ]
    container = _request(
        "POST", f"{ig_user_id}/media", token, media_type="CAROUSEL", children=",".join(children), caption=caption
    )["id"]

    for _ in range(30):
        status = _request("GET", container, token, fields="status_code").get("status_code")
        if status == "FINISHED":
            break
        if status in ("ERROR", "EXPIRED"):
            raise MetaError(f"Instagram couldn't process the carousel (status {status})")
        time.sleep(4)
    else:
        raise MetaError("Instagram took too long to process the carousel")

    media_id = _request("POST", f"{ig_user_id}/media_publish", token, creation_id=container)["id"]
    link = _request("GET", media_id, token, fields="permalink").get("permalink")
    return {"id": media_id, "url": link}


def post_facebook(token: str, page_id: str, image_urls: list[str], caption: str) -> dict:
    page_token = _page_token(token, page_id)
    photo_ids = [
        _request("POST", f"{page_id}/photos", page_token, url=url, published="false")["id"] for url in image_urls
    ]
    attached = {f"attached_media[{i}]": json.dumps({"media_fbid": pid}) for i, pid in enumerate(photo_ids)}
    post_id = _request("POST", f"{page_id}/feed", page_token, message=caption, **attached)["id"]
    return {"id": post_id, "url": f"https://www.facebook.com/{post_id}"}


def describe(token: str) -> list[str]:
    """Lists the Pages and linked Instagram accounts a token can reach, for setup."""
    lines = []
    pages = _request("GET", "me/accounts", token, fields="id,name,instagram_business_account{id,username}")
    for page in pages.get("data", []):
        ig = page.get("instagram_business_account")
        ig_text = f"Instagram @{ig.get('username')} IG_USER_ID={ig['id']}" if ig else "no Instagram linked"
        lines.append(f"Page '{page['name']}' FB_PAGE_ID={page['id']}, {ig_text}")
    return lines or ["This token can't see any Facebook Pages."]
