"""Research a selected topic from its original sources (and, optionally,
independent reporting found with web search), then check every claim
against what was actually retrieved."""
from __future__ import annotations

import asyncio
import json
import logging
from html.parser import HTMLParser

import httpx

from ..config import Settings
from ..database import Database
from ..llm import LLM, LLMError
from ..models import Cluster, Research, ResearchOutput, SourceDoc
from ..services.deduplication import POINTER_SOURCES, canonical_url
from ..textutil import credibility_for, domain_of, remove_injections, sanitize_untrusted, stable_hash
from ..timeutil import ago, iso, parse_any
from . import prompts

log = logging.getLogger(__name__)
# Pages that are discussions, videos or search listings rather than articles.
NO_FETCH = {"reddit.com", "youtube.com", "youtu.be", "x.com", "twitter.com", "news.ycombinator.com",
            "trends.google.com", "instagram.com", "tiktok.com", "facebook.com"}
MAX_FETCH = 5
MAX_PAGE_BYTES = 2_000_000


class _ArticleParser(HTMLParser):
    SKIP = {"script", "style", "nav", "footer", "header", "aside", "form", "noscript", "svg", "figure"}
    KEEP = {"p", "h1", "h2", "h3", "li", "blockquote"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.skip_depth = 0
        self.keep_depth = 0
        self.in_title = False
        self.title = ""
        self.meta: dict[str, str] = {}
        self.blocks: list[tuple[str, str]] = []
        self._buf: list[str] = []
        self._tag = ""

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "meta":
            key = (a.get("property") or a.get("name") or "").lower()
            if key and a.get("content"):
                self.meta[key] = a["content"]
        elif tag == "title":
            self.in_title = True
        elif tag in self.SKIP:
            self.skip_depth += 1
        elif tag in self.KEEP and not self.skip_depth:
            if not self.keep_depth:
                self._tag = tag
            self.keep_depth += 1

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        elif tag in self.SKIP and self.skip_depth:
            self.skip_depth -= 1
        elif tag in self.KEEP and self.keep_depth and not self.skip_depth:
            self.keep_depth -= 1
            if not self.keep_depth:
                text = " ".join("".join(self._buf).split())
                if text and tag != "p" and not text.endswith((".", "!", "?", ":", '"', "”")):
                    text += "."  # keep headings and list items from running into the next sentence
                if text:
                    self.blocks.append((self._tag, text))
                self._buf = []

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        elif self.keep_depth and not self.skip_depth:
            self._buf.append(data)


def extract_article(html: str) -> dict[str, str]:
    p = _ArticleParser()
    try:
        p.feed(html)
    except Exception:  # malformed markup: keep whatever was parsed
        pass
    def keep(tag: str, text: str) -> bool:
        if tag in ("h1", "h2", "h3"):
            return True
        if tag in ("li", "blockquote"):
            return len(text) >= 40  # short list items are usually menus and tags
        return len(text) > 30 or text.endswith((".", "!", "?"))

    text = " ".join(t for tag, t in p.blocks if keep(tag, t))
    return {
        "title": (p.meta.get("og:title") or p.title).strip(),
        "publisher": p.meta.get("og:site_name", "").strip(),
        "published_at": p.meta.get("article:published_time", "").strip(),
        "text": text,
    }


async def fetch_page(client: httpx.AsyncClient, url: str) -> tuple[int | None, dict[str, str] | None]:
    try:
        resp = await client.get(url)
    except (httpx.TimeoutException, httpx.TransportError) as e:
        log.info("source fetch failed", extra={"url": url, "error": type(e).__name__})
        return None, None
    if resp.status_code >= 400 or "html" not in resp.headers.get("content-type", "text/html"):
        return resp.status_code, None
    return resp.status_code, extract_article(resp.text[:MAX_PAGE_BYTES])


def initial_sources(cluster: Cluster, settings: Settings) -> list[SourceDoc]:
    seen: dict[str, SourceDoc] = {}

    def add(url: str | None, title: str, publisher: str, published: str | None, origin: str = "trend") -> None:
        key = canonical_url(url)
        if not url or not key or key in seen:
            return
        seen[key] = SourceDoc(url=url, title=title, publisher=publisher, domain=domain_of(url),
                              published_at=published, origin=origin)

    for it in cluster.items:
        if it.source == "google_trends":
            for n in it.raw.get("news_items", []):
                add(n.get("url"), n.get("title", ""), n.get("source", ""), it.published_at)
            continue
        if it.source in POINTER_SOURCES:
            continue
        add(it.source_url, it.topic, it.raw.get("publisher") or domain_of(it.source_url), it.published_at)
        if it.raw.get("discussion_url"):
            add(it.raw["discussion_url"], f"Discussion: {it.topic}", "Hacker News", it.published_at)
    return sorted(seen.values(), key=lambda s: -credibility_for(s.url, settings.source_credibility))


async def gather_sources(cluster: Cluster, settings: Settings, llm: LLM, client: httpx.AsyncClient) -> tuple[list[SourceDoc], int]:
    sources = initial_sources(cluster, settings)
    removed_total = 0

    if settings.ai.use_web_search and settings.ai.web_search_max_uses > 0:
        try:
            _, results = await llm.web_research(
                model=settings.ai.model, effort="low", system=prompts.web_search_system(),
                max_uses=settings.ai.web_search_max_uses,
                prompt=(f"Find independent, credible reporting on this story and any primary source:\n"
                        f"<untrusted_source>{sanitize_untrusted(cluster.title, 300)}</untrusted_source>\n"
                        f"Known coverage: {', '.join(s.url for s in sources[:5])}"),
            )
        except LLMError as e:
            log.info("web search unavailable", extra={"error": str(e)})
            results = []
        known = {canonical_url(s.url) for s in sources}
        for r in results[:6]:
            if r.get("url", "").startswith("http") and canonical_url(r["url"]) not in known:
                known.add(canonical_url(r["url"]))
                sources.append(SourceDoc(url=r["url"], title=r.get("title", ""), domain=domain_of(r["url"]),
                                         publisher=domain_of(r["url"]), origin="web_search",
                                         published_at=r.get("page_age") or None))

    to_fetch = [s for s in sources if s.domain not in NO_FETCH][:MAX_FETCH]

    async def one(s: SourceDoc) -> None:
        nonlocal removed_total
        status, page = await fetch_page(client, s.url)
        s.http_status = status
        if not page or len(page["text"]) < 200:
            return
        clean, removed = remove_injections(page["text"])
        removed_total += removed
        s.text = sanitize_untrusted(clean, settings.ai.max_source_chars)
        s.fetched = True
        s.title = s.title or page["title"]
        s.publisher = page["publisher"] or s.publisher
        if page["published_at"] and (dt := parse_any(page["published_at"])):
            s.published_at = iso(dt)

    await asyncio.gather(*(one(s) for s in to_fetch))
    return sources, removed_total


def _prompt(cluster: Cluster, sources: list[SourceDoc]) -> str:
    lines = [f"Topic: {sanitize_untrusted(cluster.title, 300)}", "", "Sources:"]
    for n, s in enumerate(sources, 1):
        lines.append(f"[{n}] url: {s.url}\n    publisher: {s.publisher or s.domain} | published: {s.published_at or 'unknown'}"
                     f" | body retrieved: {'yes' if s.fetched else 'no (headline only)'}")
        lines.append(f"<untrusted_source id=\"{n}\">\ntitle: {sanitize_untrusted(s.title, 300)}\n"
                     f"{s.text if s.fetched else '(no body text available)'}\n</untrusted_source>")
    return "\n".join(lines)


def validate(output: ResearchOutput, sources: list[SourceDoc]) -> tuple[ResearchOutput, bool, str]:
    """Enforce the evidence rules in code, whatever the model returned."""
    by_url = {s.url: s for s in sources}
    for claim in output.claims:
        claim.evidence_urls = [u for u in claim.evidence_urls if u in by_url]
        docs = [by_url[u] for u in claim.evidence_urls]
        backed = any(d.fetched for d in docs) or len({d.domain for d in docs}) >= 2
        if claim.verified and not backed:
            claim.verified = False
            claim.evidence += " [unverified: no retrieved source text supports it]"
    facts = [c for c in output.claims if c.verified and c.kind == "fact"]
    if not output.suitable:
        return output, False, output.unsuitable_reason or "research judged the topic unsuitable"
    if not any(s.fetched for s in sources):
        return output, False, "no source article could be retrieved; headlines alone are not evidence"
    if not facts:
        return output, False, "no factual claim could be verified against the sources"
    return output, True, ""


async def research_topic(cluster: Cluster, settings: Settings, llm: LLM, db: Database,
                         client: httpx.AsyncClient) -> Research:
    base = initial_sources(cluster, settings)
    cache_key = stable_hash(cluster.key, *sorted(s.url for s in base), llm.name)
    cached = db.query_one("SELECT data_json FROM research WHERE cache_key = ? AND created_at >= ?",
                          (cache_key, ago(hours=24)))
    if cached:
        log.info("research cache hit", extra={"cluster": cluster.key})
        return Research.model_validate_json(cached["data_json"])

    sources, removed = await gather_sources(cluster, settings, llm, client)
    context = {"topic": cluster.title, "audience": settings.account.audience,
               "sources": [s.model_dump() for s in sources]}
    output = await llm.structured(
        task="research", model=settings.ai.model, effort=settings.ai.effort_research,
        system=prompts.research_system(settings), prompt=_prompt(cluster, sources),
        schema=ResearchOutput, context=context,
    )
    output, sufficient, reason = validate(output, sources)
    if removed:
        output.missing_information.append(f"{removed} instruction-like passage(s) were removed from source pages before analysis.")
    research = Research(cache_key=cache_key, topic=cluster.title, output=output, sources=sources,
                        sufficient=sufficient, insufficiency_reason=reason, generated_by=llm.name)
    return research


def store_research(db: Database, research: Research, cluster_id: int) -> int:
    for_storage = research.model_copy(deep=True)
    for s in for_storage.sources:
        s.text = s.text[:4000]  # enough to audit; the full page stays at its URL
    return db.execute(
        """INSERT INTO research (cluster_id, cache_key, summary, data_json, confidence, sufficient, generated_by, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(cache_key) DO UPDATE SET cluster_id = excluded.cluster_id""",
        (cluster_id, research.cache_key, research.output.summary, for_storage.model_dump_json(),
         research.output.confidence, int(research.sufficient), research.generated_by, iso()),
    ) or db.scalar("SELECT id FROM research WHERE cache_key = ?", (research.cache_key,))


def research_json(research: Research) -> str:
    """The brief writers and the reviewer see: verified claims and source list, no raw page text."""
    return json.dumps({
        "topic": research.topic,
        "summary": research.output.summary,
        "angle": research.output.angle,
        "confidence": research.output.confidence,
        "verified_claims": [c.model_dump() for c in research.output.claims if c.verified],
        "unverified_claims_do_not_use": [c.claim for c in research.output.claims if not c.verified],
        "conflicting_evidence": research.output.conflicting_evidence,
        "missing_information": research.output.missing_information,
        "sources": [{"url": s.url, "publisher": s.publisher or s.domain, "published_at": s.published_at,
                     "body_retrieved": s.fetched} for s in research.sources],
    }, ensure_ascii=False, indent=1)

