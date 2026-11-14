from ..agents.writer_base import PlatformWriter


class ThreadsWriter(PlatformWriter):
    platform = "threads"
    char_limit = 500
    lengths = {"short": 160, "medium": 300, "long": 480}
    guide = """Threads: warm, conversational and discussion-friendly. Share a genuine observation or a clear
explanation that people will want to add to. Encourage replies only through substance, never manufactured
controversy or "agree?" bait. Hashtags are unnecessary (Threads supports one topic tag at most)."""
