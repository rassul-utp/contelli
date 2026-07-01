import re
from abc import ABC, abstractmethod
from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)

ENGAGEMENT_KEYWORDS: frozenset[str] = frozenset(
    {
        "viral",
        "trending",
        "breaking",
        "exclusive",
        "secret",
        "free",
        "giveaway",
        "shocking",
        "must",
        "urgent",
        "limited",
        "discount",
        "challenge",
        "hack",
        "tips",
        "howto",
        "tutorial",
        "review",
        "launch",
    }
)


class BasePredictor(ABC):
    @abstractmethod
    async def predict_viral_score(self, text_metadata: dict[str, Any]) -> dict[str, Any]:
        pass


class ContentViralPredictor(BasePredictor):
    async def predict_viral_score(self, text_metadata: dict[str, Any]) -> dict[str, Any]:
        content = str(text_metadata.get("content", ""))
        source = str(text_metadata.get("source", "unknown"))

        text_length = len(content)
        keyword_density = self._keyword_density(content)
        length_factor = min(text_length / 1000, 1.0)

        # TODO: TensorFlow Integration
        # Replace heuristic scoring with a trained model:
        # features = self._vectorize(content)
        # viral_score = float(self._model.predict(features)[0])
        viral_score = round(min(1.0, length_factor * 0.45 + keyword_density * 0.55), 3)

        logger.info("📊 ML scoring completed. viral_score=%s", viral_score)
        return {
            "viral_score": viral_score,
            "factors": {
                "text_length": text_length,
                "keyword_density": round(keyword_density, 4),
                "length_factor": round(length_factor, 4),
                "source": source,
                "model": "heuristic_v1",
            },
        }

    @staticmethod
    def _keyword_density(content: str) -> float:
        tokens = re.findall(r"[a-zA-Z0-9]+", content.lower())
        if not tokens:
            return 0.0
        hits = sum(1 for token in tokens if token in ENGAGEMENT_KEYWORDS)
        return hits / len(tokens)
