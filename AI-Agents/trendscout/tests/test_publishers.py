"""Publisher adapters against local fakes of each platform API."""
import json

import httpx
import pytest

from app.models import Outcome
from app.publishers.base import all_publishers
from app.publishers.bluesky import BlueskyPublisher, facets
from app.publishers.linkedin import LinkedInPublisher, escape_commentary
from app.publishers.instagram import InstagramPublisher
from app.publishers.threads import ThreadsPublisher
from app.publishers.tiktok import TikTokPublisher
from app.publishers.x import XPublisher, oauth1_header
from app.textutil import make_tid
from tests.conftest import run

BSKY_ENV = {"BLUESKY_HANDLE": "tester.bsky.social", "BLUESKY_APP_PASSWORD": "app-pass-1234"}


class FakePDS:
    """Enough of an AT Protocol PDS to test idempotent posting."""

    def __init__(self):
        self.records: dict[str, dict] = {}
        self.creates = 0
        self.mode = None  # "timeout_after_write" | "connect_error" | "rate_limit" | "bad_login"

    def __call__(self, request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("createSession"):
            body = json.loads(request.content)
            if self.mode == "bad_login" or body["password"] != "app-pass-1234":
                return httpx.Response(401, json={"error": "AuthenticationRequired"})
            return httpx.Response(200, json={"accessJwt": "jwt", "refreshJwt": "r", "did": "did:plc:test",
                                             "handle": "tester.bsky.social"})
        if path.endswith("getPosts"):  # public AppView endpoint, no auth
            return httpx.Response(200, json={"posts": [{"likeCount": 4, "replyCount": 1, "repostCount": 2, "quoteCount": 1}]})
        assert request.headers.get("authorization") == "Bearer jwt"
        if path.endswith("createRecord"):
            if self.mode == "connect_error":
                raise httpx.ConnectError("refused")
            if self.mode == "rate_limit":
                return httpx.Response(429, headers={"ratelimit-reset": "2000000000"}, json={"error": "RateLimitExceeded"})
            body = json.loads(request.content)
            self.creates += 1
            rkey = body["rkey"]
            if rkey in self.records:
                return httpx.Response(400, json={"error": "InvalidRequest", "message": "Record already exists"})
            uri = f"at://did:plc:test/app.bsky.feed.post/{rkey}"
            self.records[rkey] = {"uri": uri, "cid": f"cid-{rkey}", "value": body["record"]}
            if self.mode == "timeout_after_write":
                self.mode = None
                raise httpx.ReadTimeout("no response")
            return httpx.Response(200, json={"uri": uri, "cid": f"cid-{rkey}"})
        if path.endswith("getRecord"):
            rkey = request.url.params["rkey"]
            if rkey in self.records:
                return httpx.Response(200, json=self.records[rkey])
            return httpx.Response(400, json={"error": "RecordNotFound", "message": "Could not locate record"})
        return httpx.Response(404)


def bsky_job(n=1):
    key = f"{n}:bluesky:abc"
    return {"id": n, "client_ref": make_tid(key), "idempotency_key": key, "platform": "bluesky"}


def bsky(pds):
    return BlueskyPublisher(dict(BSKY_ENV)), httpx.AsyncClient(transport=httpx.MockTransport(pds))


def test_bluesky_post_uses_job_record_key_and_facets():
    pds = FakePDS()
    pub, client = bsky(pds)
    job = bsky_job()
    text = "Café ☕ news: https://example.com/a #AI"
    r = run(pub.publish(client, job, {"post_text": text, "structure_json": "{}"}))
    assert r.outcome == Outcome.SUCCESS and r.url == f"https://bsky.app/profile/tester.bsky.social/post/{job['client_ref']}"
    record = pds.records[job["client_ref"]]["value"]
    link = next(f for f in record["facets"] if f["features"][0]["$type"].endswith("#link"))
    b = text.encode()
    assert b[link["index"]["byteStart"]:link["index"]["byteEnd"]] == b"https://example.com/a"
    tag = next(f for f in record["facets"] if f["features"][0]["$type"].endswith("#tag"))
    assert tag["features"][0]["tag"] == "AI"


def test_bluesky_timeout_after_write_is_uncertain_then_reconciled_without_duplicate():
    pds = FakePDS()
    pds.mode = "timeout_after_write"
    pub, client = bsky(pds)
    job = bsky_job()
    draft = {"post_text": "hello", "structure_json": "{}"}
    first = run(pub.publish(client, job, draft))
    assert first.outcome == Outcome.UNCERTAIN
    rec = run(pub.reconcile(client, job, draft))
    assert rec.outcome == Outcome.SUCCESS and rec.detail["reconciled"]
    again = run(pub.publish(client, job, draft))  # even a retry cannot duplicate: same record key
    assert again.outcome == Outcome.SUCCESS and pds.creates == 1 and len(pds.records) == 1


def test_bluesky_reconcile_confirms_missing_post():
    pds = FakePDS()
    pub, client = bsky(pds)
    r = run(pub.reconcile(client, bsky_job(), {"post_text": "x"}))
    assert r.outcome == Outcome.FAILED and r.retryable


def test_bluesky_failure_classification():
    pds = FakePDS()
    pds.mode = "connect_error"
    pub, client = bsky(pds)
    r = run(pub.publish(client, bsky_job(), {"post_text": "x", "structure_json": "{}"}))
    assert r.outcome == Outcome.FAILED and r.retryable

    pds.mode = "rate_limit"
    r = run(pub.publish(client, bsky_job(2), {"post_text": "x", "structure_json": "{}"}))
    assert r.outcome == Outcome.FAILED and r.rate_limited_until is not None

    pds2 = FakePDS()
    pds2.mode = "bad_login"
    pub2, client2 = bsky(pds2)
    r = run(pub2.publish(client2, bsky_job(), {"post_text": "x", "structure_json": "{}"}))
    assert r.outcome == Outcome.FAILED and "app password" in r.error
    ok, msg = run(pub2.verify(client2))
    assert not ok


def test_bluesky_thread_replies_reference_root():
    pds = FakePDS()
    pub, client = bsky(pds)
    draft = {"post_text": "1/3 first", "structure_json": json.dumps({"thread_posts": ["2/3 second", "3/3 third"]})}
    r = run(pub.publish(client, bsky_job(), draft))
    assert r.outcome == Outcome.SUCCESS and len(pds.records) == 3
    replies = [v["value"] for v in pds.records.values() if "reply" in v["value"]]
    assert len(replies) == 2 and all(rp["reply"]["root"]["uri"] == r.platform_post_id for rp in replies)


def test_bluesky_metrics_and_verify():
    pds = FakePDS()
    pub, client = bsky(pds)
    ok, msg = run(pub.verify(client))
    assert ok and "tester.bsky.social" in msg
    m = run(pub.metrics(client, {"platform_post_id": "at://did:plc:test/app.bsky.feed.post/x"}))
    assert (m.likes, m.comments, m.reposts, m.impressions) == (4, 1, 3, None)


def test_facets_use_utf8_byte_offsets():
    f = facets("👋 https://a.example")
    assert f[0]["index"] == {"byteStart": 5, "byteEnd": 5 + len("https://a.example")}


def test_x_oauth_signature_matches_documented_example():
    header = oauth1_header(
        "POST", "https://api.twitter.com/1.1/statuses/update.json?include_entities=true",
        "xvz1evFS4wEEPTGEFPHBog", "kAcSOqF21Fu85e7zjz7ZN2U4ZRhfV3WpwPAoE3Z7kBw",
        "370773112-GmHxMAgYyLbNEtIKZeRNFsMKPR9EyMZeS9weJAEb", "LswwdoUaIvS8ltyTt5jkRh4J50vUPVVHtR2YPi5kE",
        nonce="kYjzVBB8Y0ZFabxSWbWovY3uYSQ2pTgmZeNu2VS4cg", timestamp="1318622958",
        form_params={"status": "Hello Ladies + Gentlemen, a signed OAuth request!"})
    assert 'oauth_signature="hCtSmYh%2BiHYCEqBWrE7C7hYmtUk%3D"' in header


X_ENV = {"X_API_KEY": "k", "X_API_SECRET": "s", "X_ACCESS_TOKEN": "t", "X_ACCESS_TOKEN_SECRET": "ts"}


def test_x_publish_and_permission_error():
    seen = []

    def api(request):
        seen.append(json.loads(request.content))
        assert request.headers["authorization"].startswith("OAuth ")
        return httpx.Response(201, json={"data": {"id": str(100 + len(seen))}})

    client = httpx.AsyncClient(transport=httpx.MockTransport(api))
    r = run(XPublisher(X_ENV).publish(client, {"id": 1}, {"post_text": "a", "structure_json": json.dumps({"thread_posts": ["b"]})}))
    assert r.outcome == Outcome.SUCCESS and r.platform_post_id == "101"
    assert seen[1]["reply"] == {"in_reply_to_tweet_id": "101"}

    denied = httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(403, json={"detail": "tier"})))
    r = run(XPublisher(X_ENV).publish(denied, {"id": 1}, {"post_text": "a", "structure_json": "{}"}))
    assert r.outcome == Outcome.FAILED and "permission" in r.error and not r.retryable


def test_server_error_is_uncertain():
    client = httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(503)))
    r = run(XPublisher(X_ENV).publish(client, {"id": 1}, {"post_text": "a", "structure_json": "{}"}))
    assert r.outcome == Outcome.UNCERTAIN


def test_linkedin():
    assert escape_commentary("AI (beta) #1 @me") == r"AI \(beta\) \#1 \@me"
    captured = {}

    def api(request):
        captured.update(json.loads(request.content))
        assert request.headers["linkedin-version"] and request.headers["x-restli-protocol-version"] == "2.0.0"
        return httpx.Response(201, headers={"x-restli-id": "urn:li:share:42"})

    env = {"LINKEDIN_ACCESS_TOKEN": "tok", "LINKEDIN_AUTHOR_URN": "urn:li:person:abc"}
    r = run(LinkedInPublisher(env).publish(httpx.AsyncClient(transport=httpx.MockTransport(api)), {"id": 1},
                                          {"post_text": "Hello (world)", "structure_json": "{}"}))
    assert r.outcome == Outcome.SUCCESS and r.url == "https://www.linkedin.com/feed/update/urn:li:share:42/"
    assert captured["commentary"] == r"Hello \(world\)" and captured["author"] == "urn:li:person:abc"


def test_threads_two_step_publish():
    calls = []

    def api(request):
        calls.append(request.url.path)
        if request.url.path.endswith("/threads"):
            assert request.url.params["media_type"] == "TEXT"
            return httpx.Response(200, json={"id": "container1"})
        if request.url.path.endswith("/threads_publish"):
            assert request.url.params["creation_id"] == "container1"
            return httpx.Response(200, json={"id": "media9"})
        return httpx.Response(200, json={"permalink": "https://www.threads.net/@me/post/abc"})

    env = {"THREADS_USER_ID": "u1", "THREADS_ACCESS_TOKEN": "tok"}
    r = run(ThreadsPublisher(env).publish(httpx.AsyncClient(transport=httpx.MockTransport(api)), {"id": 1},
                                         {"post_text": "hi", "structure_json": "{}"}))
    assert r.outcome == Outcome.SUCCESS and r.platform_post_id == "media9" and r.url.endswith("/abc")


def test_media_platforms_require_media():
    no_net = httpx.AsyncClient(transport=httpx.MockTransport(lambda r: pytest.fail("should not call the API")))
    ig = InstagramPublisher({"INSTAGRAM_USER_ID": "1", "INSTAGRAM_ACCESS_TOKEN": "t"})
    r = run(ig.publish(no_net, {"id": 1}, {"post_text": "caption", "structure_json": "{}"}))
    assert r.outcome == Outcome.NOT_CONFIGURED and "image" in r.error
    tt = TikTokPublisher({"TIKTOK_ACCESS_TOKEN": "t"})
    r = run(tt.publish(no_net, {"id": 1}, {"post_text": "caption", "structure_json": "{}"}))
    assert r.outcome == Outcome.NOT_CONFIGURED and "video" in r.error


def test_tiktok_is_uncertain_until_processing_completes():
    def api(request):
        if request.url.path.endswith("/video/init/"):
            body = json.loads(request.content)
            assert body["post_info"]["privacy_level"] == "SELF_ONLY"  # unaudited apps can only post privately
            return httpx.Response(200, json={"data": {"publish_id": "p_123"}, "error": {"code": "ok"}})
        return httpx.Response(200, json={"data": {"status": "PUBLISH_COMPLETE"}, "error": {"code": "ok"}})

    client = httpx.AsyncClient(transport=httpx.MockTransport(api))
    pub = TikTokPublisher({"TIKTOK_ACCESS_TOKEN": "t"})
    draft = {"post_text": "cap", "structure_json": json.dumps({"media_url": "https://cdn.example.com/v.mp4"})}
    r = run(pub.publish(client, {"id": 1}, draft))
    assert r.outcome == Outcome.UNCERTAIN and r.platform_post_id == "p_123"
    done = run(pub.reconcile(client, {"id": 1, "platform_ref": "p_123"}, draft))
    assert done.outcome == Outcome.SUCCESS


def test_every_adapter_reports_missing_credentials():
    no_net = httpx.AsyncClient(transport=httpx.MockTransport(lambda r: pytest.fail("should not call the API")))
    for name, pub in all_publishers({}).items():
        ok, msg = pub.configured()
        assert not ok and msg.startswith("missing"), name
        r = run(pub.publish(no_net, {"id": 1, "client_ref": make_tid("x"), "idempotency_key": "x"},
                            {"post_text": "x", "structure_json": "{}"}))
        assert r.outcome == Outcome.NOT_CONFIGURED, name
        assert pub.prerequisites, name
