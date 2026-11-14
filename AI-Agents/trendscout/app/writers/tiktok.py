from ..agents.writer_base import PlatformWriter


class TikTokWriter(PlatformWriter):
    platform = "tiktok"
    char_limit = 2200  # caption
    lengths = {"short": 100, "medium": 150, "long": 300}
    needs_media = True
    guide = """TikTok: plan a 30-60 second vertical explainer video. post_text is the caption (short, clear,
no clickbait). script is what the presenter says, opening with a 2-second hook that is accurate. shot_list
gives 4-8 shots or on-screen text cards. media_brief summarises the video concept and any visuals that
must be created. A video has to be recorded before this can be published; text alone cannot be posted."""
