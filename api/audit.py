import asyncio
import json
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import AIAnalysis, AuditResponse, MLPrediction
from config.logging import get_logger
from database.models import AILog, Metric, Post
from services.gemini_service import GeminiService
from services.ml_service import ContentViralPredictor
from services.scraper import ContentScraper

logger = get_logger(__name__)


async def _save_post(session: AsyncSession, scraped: dict[str, Any]) -> int:
    post = Post(
        source=scraped["source"],
        content=scraped["content"],
        url=scraped.get("url"),
    )
    session.add(post)
    await session.commit()
    await session.refresh(post)
    return post.id


async def _save_results(
    session: AsyncSession,
    post_id: int,
    ai_result: dict[str, Any],
    ml_result: dict[str, Any],
) -> None:
    metric = Metric(
        post_id=post_id,
        viral_score=float(ml_result.get("viral_score", 0.0)),
        sentiment=str(ai_result.get("sentiment", "unknown")),
    )
    ai_log = AILog(
        post_id=post_id,
        provider="gemini",
        raw_response=json.dumps(ai_result, ensure_ascii=False),
    )
    session.add(metric)
    session.add(ai_log)
    await session.commit()


async def run_audit(
    session: AsyncSession,
    scraper: ContentScraper,
    gemini: GeminiService,
    predictor: ContentViralPredictor,
    text: str | None,
    url: str | None,
) -> AuditResponse:
    logger.info("📥 Content received for analysis...")
    scraped = await scraper.fetch_content(text=text, url=url)
    content = scraped["content"]
    metadata = {"content": content, "source": scraped["source"], "url": scraped.get("url")}

    logger.info("🤖 AI Analysis started...")
    post_id, ai_result, ml_result = await asyncio.gather(
        _save_post(session, scraped),
        gemini.analyze_content(content),
        predictor.predict_viral_score(metadata),
    )

    await _save_results(session, post_id, ai_result, ml_result)
    logger.info("✅ Operation completed. post_id=%s", post_id)

    return AuditResponse(
        post_id=post_id,
        source=scraped["source"],
        content=content,
        url=scraped.get("url"),
        ai_analysis=AIAnalysis(**ai_result),
        ml_prediction=MLPrediction(**ml_result),
    )
