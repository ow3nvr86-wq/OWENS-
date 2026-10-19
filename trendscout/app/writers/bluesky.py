from ..agents.writer_base import PlatformWriter


class BlueskyWriter(PlatformWriter):
    platform = "bluesky"
    char_limit = 300  # graphemes; counted conservatively as code points
    lengths = {"short": 140, "medium": 220, "long": 290}
    supports_thread = True
    guide = """Bluesky: concise and conversational, like talking to a smart friend. Lead with the interesting
insight, not the headline. One idea per post. Invite discussion by saying something worth replying to,
not by asking for replies. Hashtags are optional and rarely needed. Put the link at the end on its own
line; it becomes a clickable link and counts toward the 300-character limit."""
