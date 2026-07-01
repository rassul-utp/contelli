import os
from collections.abc import AsyncGenerator, Callable
from typing import Any
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.dependencies import get_db, get_gemini_service, get_ml_predictor, get_scraper
from api.router import router
from config.settings import get_settings
from database.models import Base

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "100000:TEST-BOT-TOKEN")
os.environ.setdefault("TELEGRAM_API_ID", "12345678")
os.environ.setdefault("TELEGRAM_API_HASH", "test_api_hash_value")
os.environ.setdefault("GEMINI_API_KEY", "test-gemini-key")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/contelli",
)
os.environ.setdefault("API_BASE_URL", "http://testserver")

get_settings.cache_clear()


class FakeScraper:
    async def fetch_content(self, text: str | None, url: str | None) -> dict[str, Any]:
        if url:
            return {"source": "url", "content": f"content-from-{url}", "url": url}
        return {"source": "text", "content": text or "", "url": None}


class FakeGemini:
    async def analyze_content(self, text: str) -> dict[str, Any]:
        return {
            "sentiment": "positive",
            "entities": ["ConTelli"],
            "engagement_triggers": ["viral", "launch"],
        }


class FakePredictor:
    async def predict_viral_score(self, text_metadata: dict[str, Any]) -> dict[str, Any]:
        return {
            "viral_score": 0.812,
            "factors": {
                "text_length": len(str(text_metadata.get("content", ""))),
                "keyword_density": 0.2,
                "length_factor": 0.1,
                "source": text_metadata.get("source", "text"),
                "model": "heuristic_v1",
            },
        }


@pytest.fixture
def fake_settings() -> Any:
    return get_settings()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def test_app(db_session: AsyncSession) -> AsyncGenerator[FastAPI, None]:
    app = FastAPI(title="ConTelli Test")
    app.include_router(router)

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_scraper] = lambda: FakeScraper()
    app.dependency_overrides[get_gemini_service] = lambda: FakeGemini()
    app.dependency_overrides[get_ml_predictor] = lambda: FakePredictor()

    yield app
    app.dependency_overrides.clear()


@pytest.fixture
async def client(test_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as http_client:
        yield http_client


@pytest.fixture
def make_audit_response() -> Callable[..., Any]:
    from api.schemas import AIAnalysis, AuditResponse, MLPrediction

    def _factory(**overrides: Any) -> AuditResponse:
        payload = {
            "post_id": 1,
            "source": "text",
            "content": "viral launch tips",
            "url": None,
            "ai_analysis": AIAnalysis(
                sentiment="positive",
                entities=["launch"],
                engagement_triggers=["viral"],
            ),
            "ml_prediction": MLPrediction(
                viral_score=0.7,
                factors={"model": "heuristic_v1"},
            ),
        }
        payload.update(overrides)
        if "ai_analysis" in overrides and isinstance(overrides["ai_analysis"], dict):
            payload["ai_analysis"] = AIAnalysis(**overrides["ai_analysis"])
        if "ml_prediction" in overrides and isinstance(overrides["ml_prediction"], dict):
            payload["ml_prediction"] = MLPrediction(**overrides["ml_prediction"])
        return AuditResponse(**payload)

    return _factory


@pytest.fixture
def mock_gemini_client() -> AsyncMock:
    mock_response = AsyncMock()
    mock_response.text = (
        '{"sentiment":"positive","entities":["AI"],"engagement_triggers":["trending"]}'
    )
    mock_models = AsyncMock()
    mock_models.generate_content = AsyncMock(return_value=mock_response)
    mock_aio = AsyncMock()
    mock_aio.models = mock_models
    mock_client = AsyncMock()
    mock_client.aio = mock_aio
    return mock_client
