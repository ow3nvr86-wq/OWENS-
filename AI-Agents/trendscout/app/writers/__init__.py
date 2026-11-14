from .bluesky import BlueskyWriter
from .instagram import InstagramWriter
from .linkedin import LinkedInWriter
from .threads import ThreadsWriter
from .tiktok import TikTokWriter
from .x_writer import XWriter

WRITERS = {w.platform: w for w in (BlueskyWriter, XWriter, InstagramWriter, ThreadsWriter, LinkedInWriter, TikTokWriter)}
