import pytest

from config.settings import Settings
from services.scraper import ContentScraper


@pytest.fixture
def scraper() -> ContentScraper:
    return ContentScraper(
        settings=Settings(
            TELEGRAM_BOT_TOKEN="100:TEST",
            TELEGRAM_API_ID=1,
            TELEGRAM_API_HASH="hash",
            GEMINI_API_KEY="key",
            DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost/contelli",
        )
    )


async def test_fetch_text_content(scraper: ContentScraper) -> None:
    result = await scraper.fetch_content(text="viral launch tips", url=None)
    assert result["source"] == "text"
    assert result["content"] == "viral launch tips"
    assert result["url"] is None


async def test_fetch_youtube_without_api_key_uses_mock(scraper: ContentScraper) -> None:
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    result = await scraper.fetch_content(text=None, url=url)
    assert result["source"] == "youtube"
    assert result["url"] == url
    assert "dQw4w9WgXcQ" in result["content"]


def test_extract_youtube_id() -> None:
    video_id = ContentScraper._extract_youtube_id("https://youtu.be/dQw4w9WgXcQ")
    assert video_id == "dQw4w9WgXcQ"


def test_is_telegram_url() -> None:
    assert ContentScraper._is_telegram("https://t.me/channel/1") is True
    assert ContentScraper._is_telegram("https://example.com") is False
