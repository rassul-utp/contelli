from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.audit import run_audit
from api.dependencies import get_db, get_gemini_service, get_ml_predictor, get_scraper
from api.schemas import AuditRequest, AuditResponse
from config.logging import get_logger
from services.gemini_service import GeminiService
from services.ml_service import ContentViralPredictor
from services.scraper import ContentScraper

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["audit"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "ConTelli"}


@router.post("/audit", response_model=AuditResponse)
async def audit_content(
    payload: AuditRequest,
    session: AsyncSession = Depends(get_db),
    scraper: ContentScraper = Depends(get_scraper),
    gemini: GeminiService = Depends(get_gemini_service),
    predictor: ContentViralPredictor = Depends(get_ml_predictor),
) -> AuditResponse:
    logger.info("🚀 Audit request received")
    try:
        return await run_audit(
            session=session,
            scraper=scraper,
            gemini=gemini,
            predictor=predictor,
            text=payload.text,
            url=payload.url,
        )
    except ValueError as exc:
        logger.warning("⚠️ Validation error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("❌ Audit failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Audit processing failed.",
        ) from exc
