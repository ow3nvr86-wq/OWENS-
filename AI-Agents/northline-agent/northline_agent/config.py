"""Loads config.yaml and the secrets the agent reads from environment variables."""

import os
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

ROOT = Path(__file__).resolve().parent.parent
# Generated slides and the post queue live on their own branch (DATA_BRANCH),
# checked out here by the workflow, so the main branch history stays small.
DATA_DIR = ROOT / "data"
MEDIA_DIR = DATA_DIR / "media"
STATE_FILE = DATA_DIR / "state.json"
DATA_BRANCH = "northline-agent-data"
FONTS_DIR = ROOT / "assets" / "fonts"
PHOTOS_DIR = ROOT / "assets" / "photos"


def _env(name: str) -> str | None:
    value = os.environ.get(name, "").strip()
    return value or None


@dataclass
class Secrets:
    anthropic_api_key: str | None
    telegram_bot_token: str | None
    telegram_chat_id: str | None
    meta_access_token: str | None
    ig_user_id: str | None
    fb_page_id: str | None
    tiktok_client_key: str | None
    tiktok_client_secret: str | None
    tiktok_refresh_token: str | None

    @classmethod
    def from_env(cls) -> "Secrets":
        return cls(
            anthropic_api_key=_env("ANTHROPIC_API_KEY"),
            telegram_bot_token=_env("TELEGRAM_BOT_TOKEN"),
            telegram_chat_id=_env("TELEGRAM_CHAT_ID"),
            meta_access_token=_env("META_ACCESS_TOKEN"),
            ig_user_id=_env("IG_USER_ID"),
            fb_page_id=_env("FB_PAGE_ID"),
            tiktok_client_key=_env("TIKTOK_CLIENT_KEY"),
            tiktok_client_secret=_env("TIKTOK_CLIENT_SECRET"),
            tiktok_refresh_token=_env("TIKTOK_REFRESH_TOKEN"),
        )


class Config:
    def __init__(self, path: Path = ROOT / "config.yaml"):
        data = yaml.safe_load(path.read_text())
        self.brand: dict = data["brand"]
        self.schedule: dict = data["schedule"]
        self.platforms: dict = data.get("platforms", {})
        self.model: str = data.get("model", "claude-opus-5-5")
        self.tz = ZoneInfo(self.schedule["timezone"])
        self.secrets = Secrets.from_env()

    def media_base_url(self) -> str:
        """Public URL prefix the platforms download slide images from.

        Defaults to raw.githubusercontent.com for this repo, which needs no setup
        because the repo is public. Override with MEDIA_BASE_URL (for example a
        GitHub Pages URL) if a platform won't fetch from there.
        """
        override = _env("MEDIA_BASE_URL")
        if override:
            return override.rstrip("/")
        repo = _env("GITHUB_REPOSITORY") or "ow3nvr86-wq/OWENS-"
        return f"https://raw.githubusercontent.com/{repo}/{DATA_BRANCH}/media"

    def enabled_platforms(self) -> list[str]:
        """Platforms switched on in config.yaml that also have credentials."""
        s = self.secrets
        ready = {
            "instagram": bool(s.meta_access_token and s.ig_user_id),
            "facebook": bool(s.meta_access_token and s.fb_page_id),
            "tiktok": bool(s.tiktok_client_key and s.tiktok_client_secret and s.tiktok_refresh_token),
        }
        return [p for p in ("instagram", "facebook", "tiktok") if self.platforms.get(p, True) and ready[p]]
