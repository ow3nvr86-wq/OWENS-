"""Cheap text processing: tokenising, similarity, platform character counts,
untrusted-text sanitising and Bluesky record keys. No model calls here."""
from __future__ import annotations

import hashlib
import html
import re
import time
import unicodedata
from urllib.parse import urlsplit

STOPWORDS = frozenset("""
a about above after again against all am an and any are as at be because been before being below between
both but by can could did do does doing down during each few for from further had has have having he her
here hers herself him himself his how i if in into is it its itself just me more most my myself no nor not
now of off on once only or other our ours ourselves out over own same she should so some such than that the
their theirs them themselves then there these they this those through to too under until up very was we were
what when where which while who whom why will with would you your yours yourself yourselves new says said
says report reports update updates via amp vs one two three first last year years week today day get gets
show hn ask hn tell watch live video news how why what this that just like make makes made use using
""".split())

_WORD = re.compile(r"[a-z0-9][a-z0-9+#.\-']*[a-z0-9+#]|[a-z0-9]")
_TAGS = re.compile(r"<[^>]+>")
_URL = re.compile(r"https?://\S+")
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f​-‏‪-‮⁦-⁩]")


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).lower()
    return text.replace("’", "'").replace("‘", "'")


def _stem(word: str) -> str:
    for suffix in ("ings", "ing", "ies", "es", "s", "ed"):
        if len(word) > len(suffix) + 3 and word.endswith(suffix):
            return word[: -len(suffix)] + ("y" if suffix == "ies" else "")
    return word


def tokens(text: str) -> list[str]:
    words = [w.strip("'").removesuffix("'s") for w in _WORD.findall(normalize(text))]
    return [_stem(w) for w in words if w not in STOPWORDS and len(w) > 1 and not w.isdigit()]


def keywords(text: str, limit: int = 12) -> list[str]:
    seen: dict[str, int] = {}
    for t in tokens(text):
        seen[t] = seen.get(t, 0) + 1
    return [w for w, _ in sorted(seen.items(), key=lambda kv: (-kv[1], kv[0]))][:limit]


def jaccard(a: set[str] | list[str], b: set[str] | list[str]) -> float:
    a, b = set(a), set(b)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def overlap(a: set[str] | list[str], b: set[str] | list[str]) -> float:
    """Overlap coefficient: how much of the smaller set is in the larger one."""
    a, b = set(a), set(b)
    if not a or not b:
        return 0.0
    return len(a & b) / min(len(a), len(b))


def similarity(a: str, b: str) -> float:
    ta, tb = set(tokens(a)), set(tokens(b))
    return max(jaccard(ta, tb), 0.85 * overlap(ta, tb) if min(len(ta), len(tb)) >= 3 else 0.0)


def strip_html(text: str) -> str:
    return " ".join(html.unescape(_TAGS.sub(" ", text or "")).split())


def sanitize_untrusted(text: str, limit: int) -> str:
    """Make collected text safe to embed in a prompt as data: drop control and
    bidi characters, neutralise tags that could close our delimiters, cap length."""
    text = _CONTROL.sub("", strip_html(text))
    text = text.replace("<", "‹").replace(">", "›")
    return text[:limit]


def domain_of(url: str | None) -> str:
    if not url:
        return ""
    host = (urlsplit(url).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def credibility_for(url: str | None, table: dict[str, float], default: float = 0.5) -> float:
    host = domain_of(url)
    while host:
        if host in table:
            return table[host]
        if "." not in host:
            break
        host = host.split(".", 1)[1]
    return default


# ---- character counting per platform ---------------------------------------------------------

X_URL_LENGTH = 23


def count_chars(text: str, platform: str) -> int:
    if platform == "x":
        # X counts every URL as 23 characters regardless of its length.
        return len(_URL.sub("x" * X_URL_LENGTH, text))
    # Bluesky's limit is in graphemes; code points are never fewer than graphemes,
    # so counting code points can only be stricter than the real limit.
    return len(text)


def utf8_len(text: str) -> int:
    return len(text.encode("utf-8"))


def find_urls(text: str) -> list[str]:
    return [u.rstrip(".,;:!?)]'\"") for u in _URL.findall(text)]


# ---- Bluesky record keys ---------------------------------------------------------------------

_B32 = "234567abcdefghijklmnopqrstuvwxyz"


def make_tid(seed: str, micros: int | None = None) -> str:
    """A valid AT Protocol TID (timestamp identifier).

    Generated once per publishing job and stored, so every retry of that job
    writes the same record key; the PDS then refuses a second copy instead of
    creating a duplicate post.
    """
    micros = micros if micros is not None else int(time.time() * 1_000_000)
    clock = int(hashlib.sha256(seed.encode()).hexdigest(), 16) & 0x3FF
    value = ((micros & ((1 << 53) - 1)) << 10) | clock
    out = []
    for _ in range(13):
        out.append(_B32[value & 31])
        value >>= 5
    return "".join(reversed(out))


def tid_micros(tid: str) -> int:
    value = 0
    for ch in tid:
        value = (value << 5) | _B32.index(ch)
    return value >> 10


def stable_hash(*parts: str, length: int = 16) -> str:
    return hashlib.sha256("\x1f".join(parts).encode()).hexdigest()[:length]


# ---- prompt-injection hygiene ----------------------------------------------------------------

_INJECTION = re.compile(
    r"(?i)\b(ignore|disregard|forget|override)\b[^.!?]{0,60}\b(instructions?|prompts?|rules|guidelines)\b"
    r"|\b(system prompt|you are now|new instructions|act as (an?|the) )"
)


def remove_injections(text: str) -> tuple[str, int]:
    """Drop sentences that read like instructions to an AI. Collected text is
    data; this removes the obvious attempts before a model ever sees them."""
    parts = re.split(r"(?<=[.!?])\s+", text)
    kept = [p for p in parts if not _INJECTION.search(p)]
    return " ".join(kept), len(parts) - len(kept)
