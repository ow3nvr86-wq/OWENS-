"""Model access.

`ClaudeLLM` calls the Claude API with structured outputs (the response is
constrained to a Pydantic schema and validated). `SimulatedLLM` is a
deterministic stand-in used by offline mode and tests; it builds outputs
from the same inputs with simple rules and never calls the network. Both
record usage so cost is visible on the dashboard.

No client-side tools are ever given to a model, so nothing a model reads
from a collected web page can trigger an action. Research may use the
Anthropic-hosted web search tool, which only returns search results.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any, Protocol, TypeVar

from pydantic import BaseModel

from .database import Database
from .timeutil import iso, utcnow

log = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)

# USD per million tokens (input, output). Estimates for the cost column only;
# check current pricing before relying on them.
PRICES = {
    "claude-opus-5-5": (4.00, 20.00),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-haiku-5-5": (0.10, 0.50),
    "claude-fable-5-1": (10.00, 50.00),
}
WEB_SEARCH_USD = 0.01  # per search
# Models that accept the server-side refusal fallback in its "default" form.
FALLBACK_MODELS = {"claude-opus-5-5", "claude-opus-5", "claude-sonnet-5-5", "claude-fable-5-1", "claude-fable-5"}
FALLBACK_BETA = "server-side-fallback-2026-07-01"


class LLMError(Exception):
    pass


class LLMRefusal(LLMError):
    pass


class BudgetExceeded(LLMError):
    pass


def estimate_cost(model: str, input_tokens: int, output_tokens: int, cache_read: int = 0, searches: int = 0) -> float:
    price_in, price_out = PRICES.get(model, (0.0, 0.0))
    return round((input_tokens * price_in + cache_read * price_in * 0.1 + output_tokens * price_out) / 1e6
                 + searches * WEB_SEARCH_USD, 6)


def month_spend(db: Database, now: datetime | None = None) -> float:
    start = (now or utcnow()).strftime("%Y-%m-01T00:00:00")
    return float(db.scalar("SELECT COALESCE(SUM(cost_usd), 0) FROM llm_usage WHERE ts >= ?", (start,)) or 0)


class LLM(Protocol):
    name: str

    async def structured(self, *, task: str, model: str, effort: str, system: str, prompt: str,
                         schema: type[T], context: dict[str, Any], max_tokens: int = 16000) -> T: ...

    async def web_research(self, *, model: str, effort: str, system: str, prompt: str,
                           max_uses: int) -> tuple[str, list[dict[str, str]]]: ...


class ClaudeLLM:
    name = "claude"

    def __init__(self, db: Database, *, api_key: str = "", timeout: float = 300, budget_usd: float = 0,
                 run_id: int | None = None, http_client: Any = None):
        import anthropic
        self._anthropic = anthropic
        kwargs: dict[str, Any] = {"timeout": timeout, "max_retries": 3}
        if api_key:
            kwargs["api_key"] = api_key
        if http_client is not None:  # tests inject a mock transport here
            kwargs["http_client"] = http_client
        self.client = anthropic.AsyncAnthropic(**kwargs)
        self.db = db
        self.budget = budget_usd
        self.run_id = run_id

    def _check_budget(self) -> None:
        if self.budget and month_spend(self.db) >= self.budget:
            raise BudgetExceeded(f"monthly AI budget of ${self.budget:.2f} reached; raise ai.monthly_budget_usd to continue")

    def _record(self, task: str, model: str, usage: Any) -> None:
        if usage is None:
            return
        inp = int(getattr(usage, "input_tokens", 0) or 0)
        out = int(getattr(usage, "output_tokens", 0) or 0)
        cache = int(getattr(usage, "cache_read_input_tokens", 0) or 0)
        stu = getattr(usage, "server_tool_use", None)
        searches = int(getattr(stu, "web_search_requests", 0) or 0) if stu else 0
        self.db.execute(
            """INSERT INTO llm_usage (ts, run_id, task, model, input_tokens, output_tokens, cache_read_tokens,
                   web_searches, cost_usd) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (iso(), self.run_id, task, model, inp, out, cache, searches, estimate_cost(model, inp, out, cache, searches)),
        )

    def _common(self, model: str, effort: str) -> dict[str, Any]:
        kwargs: dict[str, Any] = {"model": model, "output_config": {"effort": effort}}
        if model in FALLBACK_MODELS:
            kwargs["betas"] = [FALLBACK_BETA]
            kwargs["fallbacks"] = "default"
        return kwargs

    async def structured(self, *, task, model, effort, system, prompt, schema, context, max_tokens=16000):
        self._check_budget()
        a = self._anthropic
        try:
            resp = await self.client.beta.messages.parse(
                max_tokens=max_tokens, system=system, messages=[{"role": "user", "content": prompt}],
                output_format=schema, **self._common(model, effort),
            )
        except a.BadRequestError as e:
            raise LLMError(f"{task}: request rejected: {e.message}") from e
        except a.AuthenticationError as e:
            raise LLMError("ANTHROPIC_API_KEY is missing or invalid") from e
        except a.RateLimitError as e:
            raise LLMError(f"{task}: rate limited by the Claude API; try again later") from e
        except a.APIStatusError as e:
            raise LLMError(f"{task}: Claude API error {e.status_code}") from e
        except a.APIConnectionError as e:
            raise LLMError(f"{task}: could not reach the Claude API ({type(e).__name__})") from e
        self._record(task, model, resp.usage)
        if resp.stop_reason == "refusal":
            category = getattr(resp.stop_details, "category", None) if resp.stop_details else None
            raise LLMRefusal(f"{task}: the model declined (category: {category})")
        if resp.stop_reason == "max_tokens":
            raise LLMError(f"{task}: response hit max_tokens before finishing")
        parsed = resp.parsed_output
        if parsed is None:
            raise LLMError(f"{task}: response did not match the schema")
        return parsed

    async def web_research(self, *, model, effort, system, prompt, max_uses):
        self._check_budget()
        a = self._anthropic
        messages: list[dict[str, Any]] = [{"role": "user", "content": prompt}]
        tools = [{"type": "web_search_20260209", "name": "web_search", "max_uses": max_uses}]
        text_parts: list[str] = []
        results: list[dict[str, str]] = []
        for _ in range(4):  # server tools may pause a long turn; resume a bounded number of times
            try:
                resp = await self.client.beta.messages.create(
                    max_tokens=16000, system=system, messages=messages, tools=tools, **self._common(model, effort))
            except a.APIError as e:
                raise LLMError(f"web research failed: {type(e).__name__}") from e
            self._record("web_research", model, resp.usage)
            if resp.stop_reason == "refusal":
                raise LLMRefusal("web research: the model declined")
            for block in resp.content:
                if block.type == "text":
                    text_parts.append(block.text)
                elif block.type == "web_search_tool_result" and isinstance(block.content, list):
                    for r in block.content:
                        if getattr(r, "type", "") == "web_search_result":
                            results.append({"url": r.url, "title": r.title or "", "page_age": r.page_age or ""})
            if resp.stop_reason != "pause_turn":
                break
            messages.append({"role": "assistant", "content": resp.content})
        return "\n".join(text_parts), results


# ---- Offline simulator --------------------------------------------------------------------------

_SENTENCE = re.compile(r"(?<=[.!?])\s+")


def sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE.split(text) if len(s.strip()) > 20]


class SimulatedLLM:
    """Deterministic, rule-based outputs so the whole workflow can run with
    no API key. Every draft it produces is labelled as simulated."""
    name = "simulated"

    def __init__(self, db: Database | None = None, run_id: int | None = None):
        self.db = db
        self.run_id = run_id

    async def structured(self, *, task, model, effort, system, prompt, schema, context, max_tokens=16000):
        from . import simulated
        handler = getattr(simulated, f"simulate_{schema.__name__}")
        result = handler(context)
        if self.db:
            self.db.execute(
                "INSERT INTO llm_usage (ts, run_id, task, model, cost_usd) VALUES (?, ?, ?, ?, 0)",
                (iso(), self.run_id, task, "simulated"))
        return schema.model_validate(result.model_dump() if isinstance(result, BaseModel) else result)

    async def web_research(self, *, model, effort, system, prompt, max_uses):
        return "", []


class UnavailableLLM:
    """Used when no API key is configured: every call fails with a clear
    reason, so discovery still collects and ranks trends but nothing is
    researched or written."""
    name = "unavailable"

    def __init__(self, reason: str):
        self.reason = reason

    async def structured(self, **kwargs):
        raise LLMError(self.reason)

    async def web_research(self, **kwargs):
        raise LLMError(self.reason)
