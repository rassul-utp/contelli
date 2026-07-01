import httpx

from api.schemas import AuditResponse
from config.logging import get_logger

logger = get_logger(__name__)


class AuditAPIClient:
    def __init__(self, base_url: str, timeout: float = 90.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    async def audit(self, text: str | None = None, url: str | None = None) -> AuditResponse:
        payload: dict[str, str] = {}
        if text:
            payload["text"] = text
        if url:
            payload["url"] = url

        logger.info("🔄 Sending audit request to %s/api/v1/audit", self._base_url)
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(f"{self._base_url}/api/v1/audit", json=payload)
                response.raise_for_status()
                data = AuditResponse.model_validate(response.json())
                logger.info("✅ Audit response received. post_id=%s", data.post_id)
                return data
        except httpx.HTTPStatusError as exc:
            logger.error("❌ API HTTP error %s: %s", exc.response.status_code, exc.response.text)
            raise
        except httpx.HTTPError as exc:
            logger.exception("❌ API request failed: %s", exc)
            raise
