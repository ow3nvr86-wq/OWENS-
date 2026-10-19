"""Independent review of every draft.

The reviewer is separate from the writers: it gets the draft and the research
and returns APPROVED_FOR_HUMAN_REVIEW, NEEDS_REVISION or REJECTED. The
writers only ever receive its instructions; nothing they return can change
a decision. Approval here never publishes anything; it only lets a person
see the draft in the approval queue.
"""
from __future__ import annotations

import json
import re

from ..config import Settings
from ..llm import LLM, LLMError
from ..models import Draft, Research, Review, ReviewOutput
from ..textutil import find_urls, normalize, similarity, utf8_len
from . import prompts, safety
from .researcher import research_json

BAIT = re.compile(
    r"(?i)\b(you won'?t believe|will shock you|smash (that|the) like|tag a friend|comment below|like and share|"
    r"share if you agree|link in bio|wait (for|till) the end|nobody is talking about|this changes everything|"
    r"must[- ]see|goes viral|breaking:?)\b")
FIRST_PERSON = re.compile(
    r"(?i)\b(i|we)\s+(tried|tested|used|visited|saw|met|spoke to|interviewed|was there|were there|have been using)\b")
NUMBER = re.compile(r"(?<![\w/.])(\d+(?:[.,]\d+)*)(?:\s?(%|percent|k|m|bn|million|billion))?", re.I)
HASHTAG = re.compile(r"(?<!\w)#\w+")


def _numbers(text: str) -> set[str]:
    without_urls = re.sub(r"https?://\S+", " ", text)
    return {m.group(1).replace(",", "") for m in NUMBER.finditer(without_urls)}


def _check(passed: bool, note: str, severity: str = "revise") -> dict:
    return {"passed": passed, "note": note, "severity": severity}


def automated_checks(draft: Draft, research: Research, settings: Settings, recent_posts: list[str],
                     needs_media: bool = False) -> dict[str, dict]:
    checks: dict[str, dict] = {}
    posts = [draft.post_text, *draft.thread_posts]
    over = [i for i, p in enumerate(posts) if len(p) > draft.char_limit]
    checks["length"] = _check(
        draft.char_count <= draft.char_limit and not over and (draft.platform != "bluesky" or utf8_len(draft.post_text) <= 3000),
        f"{draft.char_count}/{draft.char_limit} characters" + (f"; thread posts over limit: {over}" if over else ""))
    checks["not_empty"] = _check(bool(draft.post_text.strip()), "post text is empty")

    known = set(research.source_urls())
    in_text = find_urls(" ".join(posts))
    unknown = [u for u in [*draft.source_urls, *in_text] if u not in known]
    checks["sources_known"] = _check(not unknown, f"URLs not in the research sources: {unknown}" if unknown
                                     else "all URLs come from the research sources")
    status = {s.url: s.http_status for s in research.sources}
    broken = [u for u in in_text if (status.get(u) or 0) >= 400]
    checks["links_reachable"] = _check(not broken, f"links returned an error when fetched: {broken}" if broken else "ok")

    tags = HASHTAG.findall(" ".join(posts))
    checks["hashtags"] = _check(len(tags) <= settings.content.max_hashtags,
                                f"{len(tags)} hashtags (max {settings.content.max_hashtags})")

    text = " ".join(posts)
    banned = [p for p in settings.content.banned_phrases if normalize(p) in normalize(text)]
    bait = BAIT.findall(text)
    checks["no_engagement_bait"] = _check(not banned and not bait,
                                          f"banned or bait phrasing: {banned + [b if isinstance(b, str) else b[0] for b in bait]}"
                                          if banned or bait else "ok")
    checks["no_invented_experience"] = _check(not FIRST_PERSON.search(text),
                                              "claims a first-hand experience the account did not have"
                                              if FIRST_PERSON.search(text) else "ok")

    sentences_ = [normalize(s) for s in re.split(r"(?<=[.!?])\s+", text) if len(s) > 15]
    checks["no_repetition"] = _check(len(sentences_) == len(set(sentences_)), "repeated sentences")

    evidence = " ".join([research.output.summary, *(c.claim + " " + c.evidence for c in research.output.claims),
                         *(s.title + " " + s.text for s in research.sources)])
    unsupported_numbers = sorted(_numbers(text) - _numbers(evidence))
    checks["numbers_supported"] = _check(not unsupported_numbers,
                                         f"numbers not found in the research: {unsupported_numbers}"
                                         if unsupported_numbers else "every number appears in the research")

    dupes = [p for p in recent_posts if similarity(draft.post_text, p) >= settings.publishing.near_duplicate_threshold]
    checks["not_duplicate"] = _check(not dupes, "near-identical to a recent post" if dupes else "ok", "reject")

    flags = safety.rule_flags(normalize(text), settings)
    # Bait phrasing in a draft is fixable by rewording (checked above); other categories mean the content is unsafe.
    blocked = [c for c in flags if settings.safety.policy.get(c) == "exclude" and c != "engagement_bait"]
    checks["safety_rules"] = _check(not blocked, f"draft triggers excluded categories: {blocked}" if blocked else "ok", "reject")
    checks["research_sufficient"] = _check(research.sufficient, research.insufficiency_reason or "ok", "reject")
    if needs_media:
        checks["media_brief"] = _check(bool(draft.media_brief), "this platform needs a media brief")
    return checks


def _decision_from_checks(checks: dict[str, dict]) -> tuple[str, list[str], str]:
    failed = {k: v for k, v in checks.items() if not v["passed"]}
    if not failed:
        return "APPROVED_FOR_HUMAN_REVIEW", [], ""
    reasons = [f"{k}: {v['note']}" for k, v in failed.items()]
    if any(v["severity"] == "reject" for v in failed.values()):
        return "REJECTED", reasons, ""
    return "NEEDS_REVISION", reasons, "Fix these problems: " + "; ".join(reasons)


async def review(draft: Draft, research: Research, settings: Settings, llm: LLM, recent_posts: list[str],
                 needs_media: bool = False) -> Review:
    checks = automated_checks(draft, research, settings, recent_posts, needs_media)
    decision, reasons, instructions = _decision_from_checks(checks)
    if decision != "APPROVED_FOR_HUMAN_REVIEW":
        # Deterministic failures decide on their own; no model call is spent on them.
        return Review(decision=decision, reasons=reasons, revision_instructions=instructions,
                      checks={"automated": checks}, reviewer="automated checks")

    draft_view = {k: v for k, v in draft.model_dump().items()
                  if k in ("platform", "post_text", "thread_posts", "carousel_slides", "script", "shot_list",
                           "media_brief", "source_urls", "hashtags", "claims", "char_count", "char_limit")}
    prompt = "\n\n".join([
        "Draft to review:", json.dumps(draft_view, ensure_ascii=False, indent=1),
        "Research brief:", research_json(research),
        "Automated checks (all passed):", json.dumps({k: v["note"] for k, v in checks.items()}, indent=1),
    ])
    try:
        out: ReviewOutput = await llm.structured(
            task=f"review:{draft.platform}", model=settings.ai.model, effort=settings.ai.effort_review,
            system=prompts.reviewer_system(settings), prompt=prompt, schema=ReviewOutput,
            context={"automated_checks": checks, "draft": draft_view},
        )
    except LLMError as e:
        return Review(decision="REJECTED", reasons=[f"review could not be completed: {e}"],
                      checks={"automated": checks}, reviewer="automated checks", complete=False)
    if out.unsupported_claims and out.decision == "APPROVED_FOR_HUMAN_REVIEW":
        out.decision = "NEEDS_REVISION"
        out.revision_instructions = out.revision_instructions or "Remove or support: " + "; ".join(out.unsupported_claims)
    return Review(
        decision=out.decision, reasons=out.reasons + [f"unsupported: {c}" for c in out.unsupported_claims],
        revision_instructions=out.revision_instructions,
        checks={"automated": checks, "model": [c.model_dump() for c in out.checks]},
        reviewer=llm.name if llm.name == "simulated" else settings.ai.model,
    )

