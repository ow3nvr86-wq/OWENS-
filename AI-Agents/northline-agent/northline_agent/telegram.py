"""Telegram bot: sends previews with Approve / Skip / Post now buttons and reads your taps."""

import json

import requests

API = "https://api.telegram.org/bot{token}/{method}"


class Telegram:
    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = str(chat_id)

    def _call(self, method: str, **params) -> dict:
        resp = requests.post(API.format(token=self.token, method=method), json=params, timeout=60)
        data = resp.json()
        if not data.get("ok"):
            raise RuntimeError(f"Telegram {method} failed: {data.get('description')}")
        return data["result"]

    def send(self, text: str, buttons: list[list[tuple[str, str]]] | None = None) -> int:
        params = {"chat_id": self.chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
        if buttons:
            params["reply_markup"] = {
                "inline_keyboard": [[{"text": label, "callback_data": data} for label, data in row] for row in buttons]
            }
        return self._call("sendMessage", **params)["message_id"]

    def send_album_files(self, paths) -> None:
        """Uploads local images, so previews work before the files are public."""
        files, media = {}, []
        for i, path in enumerate(paths[:10]):
            key = f"img{i}"
            files[key] = (path.name, path.read_bytes(), "image/jpeg")
            media.append({"type": "photo", "media": f"attach://{key}"})
        resp = requests.post(
            API.format(token=self.token, method="sendMediaGroup"),
            data={"chat_id": self.chat_id, "media": json.dumps(media)},
            files=files,
            timeout=120,
        )
        data = resp.json()
        if not data.get("ok"):
            raise RuntimeError(f"Telegram sendMediaGroup failed: {data.get('description')}")

    def edit(self, message_id: int, text: str) -> None:
        try:
            self._call(
                "editMessageText",
                chat_id=self.chat_id,
                message_id=message_id,
                text=text,
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
        except RuntimeError:
            pass  # message too old or unchanged; not worth failing a run over

    def answer(self, callback_id: str, text: str = "") -> None:
        try:
            self._call("answerCallbackQuery", callback_query_id=callback_id, text=text)
        except RuntimeError:
            pass  # callback expired; the button tap still counts

    def updates(self, offset: int) -> list[dict]:
        return self._call("getUpdates", offset=offset, timeout=0, allowed_updates=["message", "callback_query"])

    def from_owner(self, update: dict) -> bool:
        """Only the configured chat can approve posts."""
        if "callback_query" in update:
            chat = update["callback_query"].get("message", {}).get("chat", {})
        else:
            chat = update.get("message", {}).get("chat", {})
        return str(chat.get("id")) == self.chat_id
