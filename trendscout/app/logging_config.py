"""Structured JSON logging with secret redaction.

Every line is one JSON object. Values of environment variables whose names
contain KEY/TOKEN/SECRET/PASSWORD are replaced with "[redacted]" wherever
they appear, so an exception that echoes a request never leaks a credential.
"""
from __future__ import annotations

import json
import logging
import re
import sys

from .config import secret_values

_BEARER = re.compile(r"(?i)(bearer\s+|access_token=|api_key=|key=)[A-Za-z0-9._\-~+/=]{8,}")


class Redactor(logging.Filter):
    def __init__(self) -> None:
        super().__init__()
        self.refresh()

    def refresh(self) -> None:
        self.secrets = sorted(set(secret_values()), key=len, reverse=True)

    def scrub(self, text: str) -> str:
        for s in self.secrets:
            text = text.replace(s, "[redacted]")
        return _BEARER.sub(r"\1[redacted]", text)

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = self.scrub(str(record.msg))
        if record.args:
            record.args = tuple(self.scrub(str(a)) for a in record.args) if isinstance(record.args, tuple) else record.args
        return True


class JsonFormatter(logging.Formatter):
    RESERVED = set(vars(logging.LogRecord("", 0, "", 0, "", (), None))) | {"message", "asctime"}

    def __init__(self, redactor: Redactor):
        super().__init__()
        self.redactor = redactor

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        for k, v in vars(record).items():
            if k not in self.RESERVED and not k.startswith("_"):
                payload[k] = v
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return self.redactor.scrub(json.dumps(payload, default=str, ensure_ascii=False))


_redactor: Redactor | None = None


def setup_logging(level: str = "INFO") -> Redactor:
    global _redactor
    _redactor = Redactor()
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JsonFormatter(_redactor))
    handler.addFilter(_redactor)
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level)
    for noisy in ("httpx", "httpcore", "httpx2", "anthropic"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    return _redactor


def scrub(text: str) -> str:
    return (_redactor or Redactor()).scrub(text)
