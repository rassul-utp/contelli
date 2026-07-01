import contextlib
import logging
import re
import sys
from collections.abc import MutableMapping
from typing import Any, Final

LOG_FORMAT: Final[str] = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT: Final[str] = "%Y-%m-%d %H:%M:%S"

EVENT_EMOJI: Final[dict[str, str]] = {
    "startup": "🚀",
    "db_connect": "🔄",
    "db_ok": "✅",
    "ai": "🤖",
    "incoming": "📥",
    "report": "📊",
    "warning": "⚠️",
    "error": "❌",
}

LEVEL_EMOJI: Final[dict[int, str]] = {
    logging.WARNING: "⚠️",
    logging.ERROR: "❌",
    logging.CRITICAL: "❌",
}

KEYWORD_EMOJI: Final[tuple[tuple[re.Pattern[str], str], ...]] = (
    (re.compile(r"uvicorn running|initialization|polling started|bot initialization", re.I), "🚀"),
    (re.compile(r"connecting to postgresql|reconnecting|connecting bot", re.I), "🔄"),
    (re.compile(r"database connected|operation completed|delivered|completed|fetched", re.I), "✅"),
    (re.compile(r"gemini|ai analysis|analyze_content", re.I), "🤖"),
    (re.compile(r"content received|incoming telegram|incoming payload|payload:", re.I), "📥"),
    (re.compile(r"generating report|matplotlib|chart", re.I), "📊"),
    (re.compile(r"soft limit|validation error|missing|fallback|parse failed", re.I), "⚠️"),
    (re.compile(r"exception|failed|error 429|free tier", re.I), "❌"),
)

KNOWN_EMOJI: Final[frozenset[str]] = frozenset(EVENT_EMOJI.values())


class EmojiFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        message = record.getMessage()
        if not self._has_leading_emoji(message):
            emoji = getattr(record, "emoji", None) or self._resolve_emoji(record, message)
            if emoji:
                record.msg = f"{emoji} {message}"
                record.args = ()
        return super().format(record)

    @staticmethod
    def _has_leading_emoji(message: str) -> bool:
        stripped = message.lstrip()
        return any(stripped.startswith(emoji) for emoji in KNOWN_EMOJI)

    @staticmethod
    def _resolve_emoji(record: logging.LogRecord, message: str) -> str | None:
        event = getattr(record, "event", None)
        if isinstance(event, str) and event in EVENT_EMOJI:
            return EVENT_EMOJI[event]

        for pattern, emoji in KEYWORD_EMOJI:
            if pattern.search(message):
                return emoji

        return LEVEL_EMOJI.get(record.levelno)


class EmojiLoggerAdapter(logging.LoggerAdapter):
    def process(
        self, msg: str, kwargs: MutableMapping[str, Any]
    ) -> tuple[str, MutableMapping[str, Any]]:
        extra = kwargs.setdefault("extra", {})
        event = (self.extra or {}).get("event")
        if event and "emoji" not in extra:
            extra["emoji"] = EVENT_EMOJI.get(str(event), "")
        if event and "event" not in extra:
            extra["event"] = event
        return msg, kwargs


def setup_logging(level: int = logging.INFO) -> None:
    if hasattr(sys.stdout, "reconfigure"):
        with contextlib.suppress(AttributeError, OSError, ValueError):
            sys.stdout.reconfigure(encoding="utf-8")

    root = logging.getLogger()
    if root.handlers:
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(EmojiFormatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT))
    root.addHandler(handler)
    root.setLevel(level)

    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logging.getLogger(name).handlers.clear()
        logging.getLogger(name).propagate = True


def get_logger(name: str, event: str | None = None) -> logging.Logger | EmojiLoggerAdapter:
    logger = logging.getLogger(name)
    if event:
        return EmojiLoggerAdapter(logger, {"event": event})
    return logger
