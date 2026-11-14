from ..agents.writer_base import PlatformWriter


class InstagramWriter(PlatformWriter):
    platform = "instagram"
    char_limit = 2200
    lengths = {"short": 300, "medium": 700, "long": 1400}
    needs_media = True
    guide = """Instagram: a caption for an image or carousel post. The first line must work on its own
because the rest is collapsed. Then 2-4 short paragraphs of useful explanation. Links in captions are
not clickable, so name the source in words instead of pasting a URL. Up to 5 relevant hashtags at the
end at most. Instagram cannot publish text alone: fill carousel_slides with 3-6 slide outlines (one idea
each) when a carousel suits the topic, and always describe the image or graphic in media_brief."""
