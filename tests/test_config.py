import logging

import pytest

from config.logging import EVENT_EMOJI, EmojiFormatter, setup_logging
from config.settings import get_settings


def test_event_emoji_mapping_contains_core_events() -> None:
    assert EVENT_EMOJI["startup"] == "🚀"
    assert EVENT_EMOJI["db_connect"] == "🔄"
    assert EVENT_EMOJI["error"] == "❌"


def test_emoji_formatter_adds_startup_emoji() -> None:
    formatter = EmojiFormatter("%(message)s")
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="FastAPI app initialization...",
        args=(),
        exc_info=None,
    )
    formatted = formatter.format(record)
    assert formatted.startswith("🚀")


def test_emoji_formatter_does_not_duplicate_existing_emoji() -> None:
    formatter = EmojiFormatter("%(message)s")
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="✅ Operation completed.",
        args=(),
        exc_info=None,
    )
    formatted = formatter.format(record)
    assert formatted.count("✅") == 1


def test_settings_loads_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "200:TOKEN")
    monkeypatch.setenv("TELEGRAM_API_ID", "999")
    monkeypatch.setenv("TELEGRAM_API_HASH", "abc")
    monkeypatch.setenv("GEMINI_API_KEY", "key")
    monkeypatch.setenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/contelli")
    get_settings.cache_clear()

    settings = get_settings()
    assert settings.telegram_bot_token == "200:TOKEN"
    assert str(settings.database_url).startswith("postgresql+asyncpg://")

    get_settings.cache_clear()


def test_settings_default_gemini_model() -> None:
    settings = get_settings()
    assert settings.gemini_model == "gemini-2.5-flash"


def test_setup_logging_is_idempotent() -> None:
    setup_logging()
    root = logging.getLogger()
    handler_count = len(root.handlers)
    setup_logging()
    assert len(root.handlers) == handler_count
