"""Rule-based stand-ins for each model task, used only by SimulatedLLM.

They read the structured `context` the agents pass alongside each prompt,
so offline runs produce realistic, source-grounded records without a
model. Output quality is deliberately plain; the point is to exercise the
workflow, storage, review gates and dashboard."""
from __future__ import annotations

import re

from .llm import sentences
from .models import (
    ClassificationBatch, ClassificationItem, DraftOutput, ResearchClaim, ResearchOutput, ReviewCheck, ReviewOutput,
)

_ATTRIBUTION = re.compile(r"\b(says?|said|reports?|according to|claims?|announced)\b", re.I)


def simulate_ClassificationBatch(ctx: dict) -> ClassificationBatch:
    items = []
    for c in ctx["candidates"]:
        kw = c["keyword_relevance"]
        relevance = 0 if kw == 0 else int(min(100, 45 + 55 * kw))
        has_story = bool(c.get("has_article"))
        items.append(ClassificationItem(
            candidate_id=c["candidate_id"], relevance=relevance,
            value_add=60 if has_story else 20, engagement_potential=55 + min(30, 10 * (c["source_count"] - 1)),
            category=c.get("best_category") or "none", safety_flags=[],
            information_sufficient=has_story,
            reason="simulated: keyword relevance and source coverage",
        ))
    return ClassificationBatch(items=items)


def simulate_ResearchOutput(ctx: dict) -> ResearchOutput:
    claims: list[ResearchClaim] = []
    fetched = [s for s in ctx["sources"] if s.get("fetched") and s.get("text")]
    for s in fetched:
        for sent in sentences(s["text"])[:3]:
            kind = "fact"
            if re.search(r"\b(could|would|may|might|expects?|plans?)\b", sent, re.I):
                kind = "prediction"
            claims.append(ResearchClaim(
                claim=sent, kind=kind, evidence_urls=[s["url"]],
                evidence=f"Stated in {s.get('publisher') or s['domain']}" + (" (attributed)" if _ATTRIBUTION.search(sent) else ""),
                verified=True,
            ))
    summary = " ".join(sentences(fetched[0]["text"])[:2]) if fetched else ctx["topic"]
    domains = {s["domain"] for s in fetched}
    return ResearchOutput(
        summary=summary,
        claims=claims[:8],
        conflicting_evidence=[],
        missing_information=[] if len(domains) > 1 else ["Only one independent source was available."],
        confidence="medium" if len(domains) > 1 else "low",
        angle=f"What {ctx['topic']} means in practice for {ctx['audience']}.",
        suitable=bool(claims),
        unsuitable_reason="" if claims else "No source text was available to verify any claim.",
    )


def _trim(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    cut = text[: limit - 1].rsplit(" ", 1)[0]
    return cut.rstrip(",;:") + "…"


def simulate_DraftOutput(ctx: dict) -> DraftOutput:
    platform, limit = ctx["platform"], ctx["char_limit"]
    claims = [c for c in ctx["verified_claims"] if c["kind"] == "fact"] or ctx["verified_claims"]
    link = claims[0]["evidence_urls"][0] if claims and ctx["include_links"] else ""
    lead = claims[0]["claim"] if claims else ctx["summary"]
    second = claims[1]["claim"] if len(claims) > 1 else ""
    body = f"{lead} {second}".strip()
    if ctx.get("revision_instructions"):
        body = lead  # the simulator "fixes" feedback by saying less
    reserve = (len(link) + 2) if link else 0
    text = _trim(body, max(40, limit - reserve))
    if link:
        text = f"{text}\n\n{link}"
    used = [c["claim"] for c in claims[:2]] if not ctx.get("revision_instructions") else [lead]
    out = DraftOutput(
        post_text=text, thread_posts=[], carousel_slides=[], script="", shot_list=[], media_brief="",
        hashtags=[], source_urls=claims[0]["evidence_urls"][:1] if claims else [],
        claims=used, rationale="simulated: leads with the best-supported fact and links the source",
    )
    if platform == "instagram":
        out.carousel_slides = [_trim(c["claim"], 120) for c in claims[:4]]
        out.media_brief = "Clean text-on-image carousel; one verified fact per slide; source credit on the last slide."
    if platform == "tiktok":
        out.script = " ".join(c["claim"] for c in claims[:3])
        out.shot_list = ["Presenter to camera: hook", "On-screen text: key fact", "Source shown on screen"]
        out.media_brief = "30-45 second explainer filmed vertically; requires recording before it can be published."
    return out


def simulate_ReviewOutput(ctx: dict) -> ReviewOutput:
    failed = [k for k, v in ctx["automated_checks"].items() if not v["passed"]]
    if failed:
        return ReviewOutput(decision="NEEDS_REVISION", reasons=[f"automated check failed: {k}" for k in failed],
                            revision_instructions="Fix: " + "; ".join(ctx["automated_checks"][k]["note"] for k in failed),
                            unsupported_claims=[], checks=[])
    return ReviewOutput(
        decision="APPROVED_FOR_HUMAN_REVIEW",
        reasons=["simulated review: automated checks passed and claims are copied from verified research"],
        revision_instructions="", unsupported_claims=[],
        checks=[ReviewCheck(name="claims_supported", passed=True, note="claims match research text")],
    )
