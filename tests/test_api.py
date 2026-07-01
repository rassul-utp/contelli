import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.audit import run_audit
from database.models import AILog, Metric, Post
from tests.conftest import FakeGemini, FakePredictor, FakeScraper


async def test_run_audit_persists_records(db_session: AsyncSession) -> None:
    result = await run_audit(
        session=db_session,
        scraper=FakeScraper(),
        gemini=FakeGemini(),
        predictor=FakePredictor(),
        text="viral launch tips",
        url=None,
    )

    assert result.post_id == 1
    assert result.ai_analysis.sentiment == "positive"
    assert result.ml_prediction.viral_score == pytest.approx(0.812)

    posts = (await db_session.execute(select(Post))).scalars().all()
    metrics = (await db_session.execute(select(Metric))).scalars().all()
    logs = (await db_session.execute(select(AILog))).scalars().all()

    assert len(posts) == 1
    assert len(metrics) == 1
    assert len(logs) == 1
    assert metrics[0].viral_score == pytest.approx(0.812)
    assert metrics[0].sentiment == "positive"


async def test_health_endpoint(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "ConTelli"}


async def test_audit_endpoint_with_text(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/audit",
        json={"text": "viral launch tips for creators"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "text"
    assert body["post_id"] == 1
    assert body["ai_analysis"]["sentiment"] == "positive"
    assert body["ml_prediction"]["viral_score"] == pytest.approx(0.812)


async def test_audit_endpoint_with_url(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/audit",
        json={"url": "https://example.com/article"},
    )
    assert response.status_code == 200
    assert response.json()["url"] == "https://example.com/article"


async def test_audit_endpoint_requires_payload(client: AsyncClient) -> None:
    response = await client.post("/api/v1/audit", json={})
    assert response.status_code == 422
