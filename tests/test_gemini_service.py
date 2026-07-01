from unittest.mock import MagicMock

import pytest
from google.genai.errors import APIError

from config.settings import Settings
from services.gemini_service import GeminiService


@pytest.fixture
def gemini() -> GeminiService:
    settings = Settings(
        TELEGRAM_BOT_TOKEN="100:TEST",
        TELEGRAM_API_ID=1,
        TELEGRAM_API_HASH="hash",
        GEMINI_API_KEY="key",
        DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost/contelli",
    )
    service = GeminiService(settings=settings)
    service._client = MagicMock()
    service._client.aio.models.generate_content = MagicMock()
    return service


def test_parse_response_from_json(gemini: GeminiService) -> None:
    raw = '{"sentiment":"positive","entities":["AI"],"engagement_triggers":["launch"]}'
    parsed = gemini._parse_response(raw)
    assert parsed["sentiment"] == "positive"
    assert parsed["entities"] == ["AI"]
    assert parsed["engagement_triggers"] == ["launch"]


def test_parse_response_from_markdown_json(gemini: GeminiService) -> None:
    raw = '```json\n{"sentiment":"neutral","entities":[],"engagement_triggers":[]}\n```'
    parsed = gemini._parse_response(raw)
    assert parsed["sentiment"] == "neutral"


def test_parse_response_invalid_json_returns_fallback(gemini: GeminiService) -> None:
    parsed = gemini._parse_response("not-json")
    assert parsed["sentiment"] == "neutral"
    assert parsed["engagement_triggers"] == ["api_limit_or_parse_fallback"]


async def test_analyze_content_empty_text_returns_default(gemini: GeminiService) -> None:
    result = await gemini.analyze_content("   ")
    assert result["sentiment"] == "neutral"


async def test_analyze_content_success(gemini: GeminiService) -> None:
    mock_response = MagicMock()
    mock_response.text = (
        '{"sentiment":"positive","entities":["test"],"engagement_triggers":["viral"]}'
    )

    async def _generate(**kwargs: object) -> MagicMock:
        return mock_response

    gemini._client.aio.models.generate_content = _generate
    result = await gemini.analyze_content("viral launch")
    assert result["sentiment"] == "positive"
    assert "viral" in result["engagement_triggers"]


async def test_analyze_content_429_returns_fallback(gemini: GeminiService) -> None:
    async def _raise_429(**kwargs: object) -> None:
        raise APIError(429, {"error": {"message": "quota exceeded"}})

    gemini._client.aio.models.generate_content = _raise_429
    result = await gemini.analyze_content("viral launch")
    assert result["sentiment"] == "neutral"
    assert result["engagement_triggers"] == ["api_limit_or_parse_fallback"]
