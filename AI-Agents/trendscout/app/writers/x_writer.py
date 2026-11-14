from ..agents.writer_base import PlatformWriter


class XWriter(PlatformWriter):
    platform = "x"
    char_limit = 280  # links count as 23 characters each
    lengths = {"short": 120, "medium": 200, "long": 270}
    supports_thread = True
    guide = """X: tight and direct. A clear hook in the first line that states the most interesting true
thing, then the reason it matters. No hashtag stuffing (0-1 is usually right), no "thread 🧵" or
"you won't believe" framing, no repeated phrasing across posts. Every link counts as 23 characters."""
