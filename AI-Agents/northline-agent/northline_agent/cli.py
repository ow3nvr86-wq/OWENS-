"""Command line: python -m northline_agent <command>."""

import argparse
import os
import sys
import urllib.parse
from datetime import date, timedelta

from .agent import Agent
from .config import MEDIA_DIR, Config
from .content import Post
from .publishers import meta, tiktok

SAMPLE_POST = {
    "pillar": "Training tips",
    "hook": "5 things serious athletes do before 8am",
    "slides": [
        {"headline": "Water before coffee", "body": "Half a litre first. The caffeine can wait twenty minutes."},
        {"headline": "Move for 10 minutes", "body": "A mobility flow or light jog gets blood moving before the day does."},
        {"headline": "Protein at breakfast", "body": "Aim for 30 grams. Your recovery started when you woke up."},
        {"headline": "Know today's session", "body": "Walk out the door knowing exactly what you're training."},
    ],
    "cta": {"headline": "Train like you mean it", "body": "Gear built for early mornings."},
    "caption": "Win the morning, win the session.\nSave this for tomorrow.",
    "hashtags": ["#training", "#athlete", "#morningroutine", "#northlineathletic"],
    "tiktok_title": "5 things serious athletes do before 8am",
}


def cmd_check(agent: Agent, cfg: Config) -> None:
    """Tests every connection and reports what's working."""
    s = cfg.secrets
    lines = ["<b>Connection check</b>"]
    lines.append("✅ Claude API key set" if s.anthropic_api_key else "❌ ANTHROPIC_API_KEY missing")
    lines.append("✅ Telegram connected" if agent.tg else "❌ Telegram missing (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID)")

    if s.meta_access_token:
        try:
            lines += ["✅ Meta token works. It can see:"] + [f"  • {l}" for l in meta.describe(s.meta_access_token)]
        except Exception as exc:
            lines.append(f"❌ Meta token rejected: {exc}")
        if not s.ig_user_id:
            lines.append("❌ IG_USER_ID missing (copy it from the line above)")
        if not s.fb_page_id:
            lines.append("❌ FB_PAGE_ID missing (copy it from the line above)")
    else:
        lines.append("❌ META_ACCESS_TOKEN missing (Instagram + Facebook)")

    if s.tiktok_client_key and s.tiktok_client_secret and s.tiktok_refresh_token:
        try:
            level = tiktok.privacy_level(agent._tiktok())
            note = "posts will be public" if level == "PUBLIC_TO_EVERYONE" else "posts will be PRIVATE until TikTok approves your app"
            lines.append(f"✅ TikTok connected, {note}")
        except Exception as exc:
            lines.append(f"❌ TikTok: {exc}")
    else:
        lines.append("❌ TikTok not connected (TIKTOK_CLIENT_KEY / TIKTOK_CLIENT_SECRET / TIKTOK_REFRESH_TOKEN)")

    lines.append(f"Slides are served from: {cfg.media_base_url()}")
    agent.notify("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser(prog="northline_agent")
    sub = parser.add_subparsers(dest="command", required=True)
    p_plan = sub.add_parser("plan", help="write, design and send today's 3 posts for approval")
    p_plan.add_argument("--date", help="YYYY-MM-DD, defaults to today")
    p_plan.add_argument("--force", action="store_true", help="plan again even if today already has posts")
    sub.add_parser("tick", help="read approvals and publish anything due")
    sub.add_parser("check", help="test every connection")
    sub.add_parser("sample", help="send a sample post for approval without calling Claude")
    sub.add_parser("tiktok-login-url", help="print the TikTok login link (setup)")
    p_ex = sub.add_parser("tiktok-exchange", help="turn the TikTok login code into a refresh token (setup)")
    p_ex.add_argument("code")
    p_ver = sub.add_parser("tiktok-verify-file", help="publish TikTok's URL-prefix verification file (setup)")
    p_ver.add_argument("filename")
    p_ver.add_argument("contents")
    args = parser.parse_args()

    cfg = Config()
    agent = Agent(cfg)
    s = cfg.secrets

    if args.command == "plan":
        agent.read_telegram()
        agent.plan(date.fromisoformat(args.date) if args.date else None, force=args.force)
        agent.tick()
    elif args.command == "tick":
        agent.tick()
        agent.auto_plan()
    elif args.command == "check":
        cmd_check(agent, cfg)
    elif args.command == "sample":
        post = Post.model_validate(SAMPLE_POST)
        soon = (agent.now() + timedelta(minutes=15)).strftime("%H:%M")
        agent._queue_posts(agent.now().date(), [post], [soon])
    elif args.command == "tiktok-login-url":
        redirect = _redirect_uri()
        query = urllib.parse.urlencode(
            {
                "client_key": s.tiktok_client_key or "YOUR_CLIENT_KEY",
                "scope": "user.info.basic,video.publish",
                "response_type": "code",
                "redirect_uri": redirect,
                "state": "northline",
            }
        )
        print(f"https://www.tiktok.com/v2/auth/authorize/?{query}")
        return
    elif args.command == "tiktok-exchange":
        data = tiktok.exchange_code(s.tiktok_client_key, s.tiktok_client_secret, args.code, _redirect_uri())
        # Sent privately to Telegram; never printed, because workflow logs on a public repo are public.
        if not agent.tg:
            sys.exit("Set up Telegram first so the token can be sent to you privately.")
        agent.tg.send(
            "TikTok is linked. Save this as the TIKTOK_REFRESH_TOKEN secret on GitHub:\n"
            f"<code>{data['refresh_token']}</code>"
        )
        print("Refresh token sent to your Telegram.")
        return
    elif args.command == "tiktok-verify-file":
        MEDIA_DIR.mkdir(parents=True, exist_ok=True)
        (MEDIA_DIR / args.filename).write_text(args.contents.strip() + "\n")
        print(f"Verification file will be at {cfg.media_base_url()}/{args.filename}")
    agent.save()


def _redirect_uri() -> str:
    return os.environ.get("TIKTOK_REDIRECT_URI", "https://ow3nvr86-wq.github.io/OWENS-/")
