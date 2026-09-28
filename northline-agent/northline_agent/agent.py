"""The daily loop: plan three posts, get your approval on Telegram, post them on schedule."""

import hashlib
import html
import json
import shutil
from datetime import date, datetime, timedelta
from pathlib import Path

from .config import MEDIA_DIR, STATE_FILE, Config
from .content import Post, generate_day
from .publishers import meta, tiktok
from .render import render_post
from .telegram import Telegram

MAX_ATTEMPTS = 3
KEEP_DAYS = 7
PLATFORM_NAMES = {"instagram": "Instagram", "facebook": "Facebook", "tiktok": "TikTok"}


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"telegram_offset": 0, "paused": False, "hooks": [], "posts": {}}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")


def _esc(text: str) -> str:
    return html.escape(text, quote=False)


def full_caption(post: dict) -> str:
    return f"{post['caption']}\n\n{' '.join(post['hashtags'])}"


class Agent:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.state = load_state()
        s = cfg.secrets
        self.tg = Telegram(s.telegram_bot_token, s.telegram_chat_id) if s.telegram_bot_token and s.telegram_chat_id else None
        self._tiktok_token: str | None = None

    def now(self) -> datetime:
        return datetime.now(self.cfg.tz)

    def notify(self, text: str, buttons=None) -> int | None:
        print(text)
        return self.tg.send(text, buttons) if self.tg else None

    def _time_label(self, rec: dict) -> str:
        return datetime.fromisoformat(rec["due"]).strftime("%-I:%M %p")

    # Planning

    def plan(self, day: date | None = None, force: bool = False) -> None:
        day = day or self.now().date()
        key = day.isoformat()
        existing = [k for k, r in self.state["posts"].items() if r["date"] == key]
        if existing and not force:
            print(f"Posts for {key} already planned: {', '.join(existing)}")
            return
        if self.state["paused"]:
            print("Agent is paused; not planning.")
            return

        label = day.strftime("%A %B %-d, %Y")
        plan = generate_day(self.cfg, label, self.state["hooks"])
        self._queue_posts(day, plan.posts)

    def auto_plan(self) -> None:
        """Plans today's posts once the morning plan time passes, retrying a failed plan up to 3 times."""
        now = self.now()
        key = now.date().isoformat()
        if self.state["paused"] or any(r["date"] == key for r in self.state["posts"].values()):
            return
        hour, minute = map(int, self.cfg.schedule["plan_at"].split(":"))
        if (now.hour, now.minute) < (hour, minute):
            return
        attempts = self.state.setdefault("plan_attempts", {})
        if attempts.get(key, 0) >= 3:
            return
        attempts[key] = attempts.get(key, 0) + 1
        self.state["plan_attempts"] = {k: v for k, v in attempts.items() if k >= key}
        try:
            self.plan(now.date())
        except Exception as exc:
            self.notify(f"\u26a0\ufe0f Couldn't plan today's posts (try {attempts[key]} of 3): {_esc(str(exc)[:300])}")

    def _queue_posts(self, day: date, posts: list[Post], times: list[str] | None = None) -> None:
        key = day.isoformat()
        base = self.cfg.media_base_url()
        times = times or self.cfg.schedule["post_times"]
        new_ids = []
        for i, (post, slot) in enumerate(zip(posts, times), start=1):
            post_id = f"{key}-{i}"
            paths = render_post(self.cfg, post, post_id, MEDIA_DIR / key)
            hour, minute = map(int, slot.split(":"))
            due = datetime(day.year, day.month, day.day, hour, minute, tzinfo=self.cfg.tz)
            self.state["posts"][post_id] = {
                "date": key,
                "due": due.isoformat(),
                "status": "pending",
                "post": post.model_dump(),
                "media": {fmt: [f"{base}/{key}/{p.name}" for p in ps] for fmt, ps in paths.items()},
                "local": {fmt: [str(p) for p in ps] for fmt, ps in paths.items()},
                "results": {},
                "attempts": 0,
                "reminded": False,
                "message_id": None,
            }
            self.state["hooks"] = (self.state["hooks"] + [post.hook])[-60:]
            new_ids.append(post_id)
        self._send_for_approval(day, new_ids)

    def _send_for_approval(self, day: date, post_ids: list[str]) -> None:
        if not self.tg:
            print("Telegram isn't set up, so nothing can be approved yet.")
            return
        platforms = ", ".join(PLATFORM_NAMES[p] for p in self.cfg.enabled_platforms()) or "no platforms connected yet"
        self.tg.send(
            f"<b>Northline posts for {day.strftime('%A %b %-d')}</b>\n"
            f"{len(post_ids)} slideshows ready. Each goes to: {platforms}.\n"
            "Approve each one below, or approve all at the end."
        )
        for post_id in post_ids:
            rec = self.state["posts"][post_id]
            self.tg.send_album_files([Path(p) for p in rec["local"]["feed"]])
            rec["message_id"] = self.tg.send(self._card(post_id), self._buttons(post_id))
        self.tg.send(
            "Happy with all of them?",
            [[("✅ Approve all 3", f"all:{day.isoformat()}")]],
        )

    def _card(self, post_id: str, status_line: str | None = None) -> str:
        rec = self.state["posts"][post_id]
        post = rec["post"]
        n = post_id.rsplit("-", 1)[1]
        status_line = status_line or f"Scheduled for <b>{self._time_label(rec)}</b>. Waiting on your OK."
        return (
            f"<b>Post {n}: {_esc(post['hook'])}</b>\n"
            f"<i>{_esc(post['pillar'])}</i> · {len(rec['local']['feed'])} slides\n\n"
            f"{_esc(full_caption(post))}\n\n{status_line}"
        )

    def _buttons(self, post_id: str):
        time_label = self._time_label(self.state["posts"][post_id])
        return [
            [("✅ Approve for " + time_label, f"ok:{post_id}"), ("\U0001f680 Post now", f"now:{post_id}")],
            [("⏭ Skip", f"skip:{post_id}")],
        ]

    # Approvals

    def read_telegram(self) -> None:
        if not self.tg:
            return
        for update in self.tg.updates(self.state["telegram_offset"]):
            self.state["telegram_offset"] = update["update_id"] + 1
            if not self.tg.from_owner(update):
                continue
            if "callback_query" in update:
                self._handle_button(update["callback_query"])
            elif text := update.get("message", {}).get("text", ""):
                self._handle_command(text.strip().lower())

    def _handle_button(self, cq: dict) -> None:
        action, _, target = cq.get("data", "").partition(":")
        if action == "all":
            ids = [k for k, r in self.state["posts"].items() if r["date"] == target and r["status"] == "pending"]
            for post_id in ids:
                self._set_approval(post_id, "ok")
            self.tg.answer(cq["id"], f"Approved {len(ids)} post(s)")
            return
        rec = self.state["posts"].get(target)
        if not rec or rec["status"] not in ("pending", "approved"):
            self.tg.answer(cq["id"], "That post is already handled.")
            return
        self._set_approval(target, action)
        self.tg.answer(cq["id"], {"ok": "Approved", "now": "Posting now", "skip": "Skipped"}.get(action, ""))

    def _set_approval(self, post_id: str, action: str) -> None:
        rec = self.state["posts"][post_id]
        if action == "skip":
            rec["status"] = "skipped"
            line = "⏭ Skipped."
        elif action == "now":
            rec["status"] = "approved"
            rec["post_now"] = True
            line = "\U0001f680 Approved. Posting within a few minutes."
        else:
            rec["status"] = "approved"
            line = f"✅ Approved. Posting at <b>{self._time_label(rec)}</b>."
            if datetime.fromisoformat(rec["due"]) <= self.now():
                line = "✅ Approved. Posting within a few minutes."
        if rec.get("message_id"):
            self.tg.edit(rec["message_id"], self._card(post_id, line))

    def _handle_command(self, text: str) -> None:
        if text.startswith("/pause"):
            self.state["paused"] = True
            self.notify("Paused. No new posts will be planned or published until you send /resume.")
        elif text.startswith("/resume"):
            self.state["paused"] = False
            self.notify("Resumed.")
        elif text.startswith("/status"):
            self.notify(self.status_text())
        else:
            self.notify("Commands: /status, /pause, /resume. Tap the buttons on a post to approve or skip it.")

    def status_text(self) -> str:
        today = self.now().date().isoformat()
        lines = [f"<b>Status</b>{' (paused)' if self.state['paused'] else ''}"]
        for post_id, rec in sorted(self.state["posts"].items()):
            if rec["date"] == today:
                lines.append(f"{self._time_label(rec)}: {rec['status']} — {_esc(rec['post']['hook'])}")
        if len(lines) == 1:
            lines.append("Nothing planned for today yet.")
        connected = ", ".join(PLATFORM_NAMES[p] for p in self.cfg.enabled_platforms()) or "none"
        lines.append(f"Connected: {connected}")
        return "\n".join(lines)

    # Publishing

    def tick(self) -> None:
        """Runs every few minutes: reads your taps, posts what's due, nudges and expires."""
        self.read_telegram()
        if self.state["paused"]:
            return
        now = self.now()
        expire = timedelta(minutes=self.cfg.schedule["expire_after_minutes"])
        for post_id, rec in sorted(self.state["posts"].items()):
            due = datetime.fromisoformat(rec["due"])
            if rec["status"] == "approved" and (now >= due or rec.get("post_now")):
                self.publish(post_id)
            elif rec["status"] == "retry":
                self.publish(post_id)
            elif rec["status"] == "pending" and now >= due + expire:
                rec["status"] = "expired"
                if rec.get("message_id") and self.tg:
                    self.tg.edit(rec["message_id"], self._card(post_id, "⌛ Not approved in time, so it was skipped."))
            elif rec["status"] == "pending" and now >= due and not rec["reminded"]:
                rec["reminded"] = True
                self.notify(
                    f"The {self._time_label(rec)} post is waiting on you: <b>{_esc(rec['post']['hook'])}</b>",
                    self._buttons(post_id),
                )

    def publish(self, post_id: str) -> None:
        rec = self.state["posts"][post_id]
        post = rec["post"]
        caption = full_caption(post)
        platforms = self.cfg.enabled_platforms()
        s = self.cfg.secrets

        for platform in platforms:
            if rec["results"].get(platform, {}).get("ok"):
                continue
            try:
                if platform == "instagram":
                    result = meta.post_instagram(s.meta_access_token, s.ig_user_id, rec["media"]["feed"], caption)
                elif platform == "facebook":
                    result = meta.post_facebook(s.meta_access_token, s.fb_page_id, rec["media"]["feed"], caption)
                else:
                    result = tiktok.post_photos(self._tiktok(), rec["media"]["tall"], post["tiktok_title"], caption)
                rec["results"][platform] = {"ok": True, **result}
            except Exception as exc:  # one platform failing must not stop the others
                rec["results"][platform] = {"ok": False, "error": str(exc)[:300]}

        rec["attempts"] += 1
        failed = [p for p in platforms if not rec["results"].get(p, {}).get("ok")]
        if not failed:
            rec["status"] = "posted"
        elif rec["attempts"] < MAX_ATTEMPTS:
            rec["status"] = "retry"
        else:
            rec["status"] = "failed"
        self._report(post_id, platforms, failed)

    def _report(self, post_id: str, platforms: list[str], failed: list[str]) -> None:
        rec = self.state["posts"][post_id]
        if not platforms:
            rec["status"] = "posted"
            line = "No platforms are connected yet, so nothing went out. (Setup guide: northline-agent/README.md)"
        else:
            parts = []
            for p in platforms:
                r = rec["results"][p]
                if r.get("ok"):
                    link = f' <a href="{r["url"]}">view</a>' if r.get("url") else ""
                    note = " (private until TikTok approves the app)" if r.get("privacy") == "SELF_ONLY" else ""
                    parts.append(f"✅ {PLATFORM_NAMES[p]}{link}{note}")
                else:
                    parts.append(f"⚠️ {PLATFORM_NAMES[p]}: {_esc(r['error'])}")
            line = "\n".join(parts)
            if failed and rec["status"] == "retry":
                line += "\nI'll retry the failed ones in a few minutes."
            elif failed:
                line += "\nGave up after 3 tries. Check the error above."
        if rec.get("message_id") and self.tg:
            self.tg.edit(rec["message_id"], self._card(post_id, line))
        self.notify(f"<b>{self._time_label(rec)} post:</b> {_esc(rec['post']['hook'])}\n{line}")

    def _tiktok(self) -> str:
        if self._tiktok_token:
            return self._tiktok_token
        s = self.cfg.secrets
        token, refresh = tiktok.access_token(s.tiktok_client_key, s.tiktok_client_secret, s.tiktok_refresh_token)
        if refresh != s.tiktok_refresh_token:
            digest = hashlib.sha256(refresh.encode()).hexdigest()[:12]
            if self.state.get("tiktok_refresh_warned") != digest:
                self.state["tiktok_refresh_warned"] = digest
                self.notify(
                    "TikTok issued a new login token. Replace the TIKTOK_REFRESH_TOKEN secret on GitHub with:\n"
                    f"<code>{_esc(refresh)}</code>"
                )
        self._tiktok_token = token
        return token

    # Housekeeping

    def prune(self) -> None:
        cutoff = self.now().date() - timedelta(days=KEEP_DAYS)
        for post_id in [k for k, r in self.state["posts"].items() if date.fromisoformat(r["date"]) < cutoff]:
            del self.state["posts"][post_id]
        if MEDIA_DIR.exists():
            for folder in MEDIA_DIR.iterdir():
                try:
                    if folder.is_dir() and date.fromisoformat(folder.name) < cutoff:
                        shutil.rmtree(folder)
                except ValueError:
                    continue  # not a dated folder (e.g. a TikTok verification file)

    def save(self) -> None:
        self.prune()
        save_state(self.state)
