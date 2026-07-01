import json
import re
from typing import Any

from google import genai
from google.genai import types
from google.genai.errors import APIError

from config.logging import get_logger
from config.settings import Settings, get_settings

logger = get_logger(__name__)

ANALYSIS_PROMPT = """Analyze the media content below and respond with ONLY valid JSON:
{{
  "sentiment": "positive|negative|neutral|mixed",
  "entities": ["entity1", "entity2"],
  "engagement_triggers": ["trigger1", "trigger2"]
}}

Content:
{text}
"""

RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "sentiment": {
            "type": "string",
            "enum": ["positive", "negative", "neutral", "mixed"],
        },
        "entities": {"type": "array", "items": {"type": "string"}},
        "engagement_triggers": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["sentiment", "entities", "engagement_triggers"],
}


class GeminiService:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._client = genai.Client(api_key=self._settings.gemini_api_key)

    async def analyze_content(self, text: str) -> dict[str, Any]:
        if not text.strip():
            logger.warning("⚠️ Empty content passed to Gemini analysis.")
            return self._default_response()

        logger.info("🤖 AI Analysis started...")
        prompt = ANALYSIS_PROMPT.format(text=text[:8000])

        try:
            logger.info("🤖 Gemini API Request sent.")
            response = await self._client.aio.models.generate_content(
                model=self._settings.gemini_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    response_mime_type="application/json",
                    response_schema=RESPONSE_SCHEMA,
                ),
            )
            parsed = self._parse_response(response.text or "")
            logger.info("✅ Gemini analysis completed.")
            return parsed
        except APIError as exc:
            if exc.code == 429:
                logger.error("❌ Error 429: Free Tier Limit reached.")
                return self._default_response()
            logger.exception("❌ Gemini API error: %s", exc)
            return self._default_response()
        except Exception as exc:
            if "429" in str(exc):
                logger.error("❌ Error 429: Free Tier Limit reached.")
                return self._default_response()
            logger.exception("❌ Exception occurred during Gemini analysis: %s", exc)
            return self._default_response()

    @staticmethod
    def _default_response() -> dict[str, Any]:
        return {
            "sentiment": "neutral",
            "entities": [],
            "engagement_triggers": ["api_limit_or_parse_fallback"],
        }

    def _parse_response(self, raw_text: str) -> dict[str, Any]:
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"\s*```$", "", cleaned)

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning("⚠️ Gemini JSON parse failed, using fallback response.")
            return self._default_response()

        return {
            "sentiment": str(data.get("sentiment", "neutral")),
            "entities": [str(item) for item in data.get("entities", [])],
            "engagement_triggers": [str(item) for item in data.get("engagement_triggers", [])],
        }
