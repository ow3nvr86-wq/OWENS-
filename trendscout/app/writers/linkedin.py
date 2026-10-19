from ..agents.writer_base import PlatformWriter


class LinkedInWriter(PlatformWriter):
    platform = "linkedin"
    char_limit = 3000
    lengths = {"short": 400, "medium": 900, "long": 1800}
    guide = """LinkedIn: professional and insight-driven. Open with a specific observation (not "I'm excited
to share" or a one-word hook). Explain the implications for the industry or the reader's work, give 2-3
practical takeaways, and be clear about what is still uncertain. No generic motivation, no humblebrags,
no broetry (one sentence per line for effect). Short paragraphs. Up to 3 hashtags at the end."""
