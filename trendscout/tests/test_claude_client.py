"""The real Claude client, exercised through the SDK with a mocked HTTP layer:
checks the request we send and how responses (including refusals) are handled.
No network access and no API key are needed."""
import json

import anthropic
import httpx2
import pytest

from app.llm import BudgetExceeded, ClaudeLLM, LLMRefusal
from app.models import ClassificationBatch
from tests.conftest import run


def message(content, stop_reason="end_turn", model="claude-opus-5-5", usage=None):
    return {"id": "msg_test", "type": "message", "role": "assistant", "model": model, "content": content,
            "stop_reason": stop_reason, "stop_sequence": None,
            "usage": usage or {"input_tokens": 1000, "output_tokens": 200}}


def llm_with(db, responder, budget=0):
    seen = []

    def handler(request):
        seen.append({"url": str(request.url), "headers": dict(request.headers), "body": json.loads(request.content)})
        return httpx2.Response(200, json=responder(seen[-1]))

    client = anthropic.DefaultAsyncHttpxClient(transport=httpx2.MockTransport(handler))
    return ClaudeLLM(db, api_key="sk-ant-test", budget_usd=budget, http_client=client), seen


VALID = {"items": [{"candidate_id": 0, "relevance": 80, "value_add": 60, "engagement_potential": 50, "category": "AI",
                    "safety_flags": [], "information_sufficient": True, "reason": "fits"}]}


def test_structured_request_shape_and_usage(db):
    llm, seen = llm_with(db, lambda req: message([{"type": "text", "text": json.dumps(VALID)}]))
    out = run(llm.structured(task="classify", model="claude-opus-5-5", effort="low", system="sys", prompt="p",
                             schema=ClassificationBatch, context={}))
    assert out.items[0].relevance == 80
    body, headers = seen[0]["body"], seen[0]["headers"]
    assert body["model"] == "claude-opus-5-5"
    assert body["output_config"]["effort"] == "low"
    assert body["output_config"]["format"]["type"] == "json_schema"
    assert body["fallbacks"] == "default" and "server-side-fallback-2026-07-01" in headers["anthropic-beta"]
    assert "thinking" not in body and "temperature" not in body
    row = db.query_one("SELECT * FROM llm_usage")
    assert row["input_tokens"] == 1000 and row["cost_usd"] == pytest.approx((1000 * 4 + 200 * 20) / 1e6)


def test_cheap_model_gets_no_fallback(db):
    llm, seen = llm_with(db, lambda req: message([{"type": "text", "text": json.dumps(VALID)}], model="claude-haiku-5-5"))
    run(llm.structured(task="classify", model="claude-haiku-5-5", effort="low", system="s", prompt="p",
                       schema=ClassificationBatch, context={}))
    assert "fallbacks" not in seen[0]["body"]


def test_refusal_is_raised_not_parsed(db):
    llm, _ = llm_with(db, lambda req: {**message([], stop_reason="refusal"),
                                       "stop_details": {"type": "refusal", "category": "cyber", "explanation": "x"}})
    with pytest.raises(LLMRefusal, match="cyber"):
        run(llm.structured(task="research", model="claude-opus-5-5", effort="medium", system="s", prompt="p",
                           schema=ClassificationBatch, context={}))


def test_budget_guard_stops_calls(db):
    db.execute("INSERT INTO llm_usage (ts, task, model, cost_usd) VALUES (strftime('%Y-%m-%dT%H:%M:%fZ','now'), 't', 'm', 50)")
    llm, seen = llm_with(db, lambda req: pytest.fail("should not call the API"), budget=30)
    with pytest.raises(BudgetExceeded):
        run(llm.structured(task="t", model="claude-opus-5-5", effort="low", system="s", prompt="p",
                           schema=ClassificationBatch, context={}))
    assert seen == []


def test_web_research_collects_search_results(db):
    content = [
        {"type": "server_tool_use", "id": "srvtoolu_1", "name": "web_search", "input": {"query": "northwind"}},
        {"type": "web_search_tool_result", "tool_use_id": "srvtoolu_1", "content": [
            {"type": "web_search_result", "url": "https://news.example/a", "title": "A", "page_age": "1 day ago",
             "encrypted_content": "e"}]},
        {"type": "text", "text": "One independent report found."},
    ]
    usage = {"input_tokens": 500, "output_tokens": 100, "server_tool_use": {"web_search_requests": 1}}
    llm, seen = llm_with(db, lambda req: message(content, usage=usage))
    text, results = run(llm.web_research(model="claude-opus-5-5", effort="low", system="s", prompt="p", max_uses=3))
    assert results == [{"url": "https://news.example/a", "title": "A", "page_age": "1 day ago"}]
    assert seen[0]["body"]["tools"] == [{"type": "web_search_20260209", "name": "web_search", "max_uses": 3}]
    assert db.scalar("SELECT web_searches FROM llm_usage") == 1
