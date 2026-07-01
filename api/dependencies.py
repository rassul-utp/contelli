from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import get_settings
from database.session import async_session_factory
from services.gemini_service import GeminiService
from services.ml_service import ContentViralPredictor
from services.scraper import ContentScraper


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    factory = async_session_factory()
    async with factory() as session:
        yield session


def get_scraper() -> ContentScraper:
    return ContentScraper(settings=get_settings())


def get_gemini_service() -> GeminiService:
    return GeminiService(settings=get_settings())


def get_ml_predictor() -> ContentViralPredictor:
    return ContentViralPredictor()
