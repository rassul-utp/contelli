from typing import Any

from pydantic import BaseModel, Field, model_validator


class AuditRequest(BaseModel):
    text: str | None = Field(default=None, min_length=1, max_length=10000)
    url: str | None = Field(default=None, min_length=1, max_length=512)

    @model_validator(mode="after")
    def validate_payload(self) -> "AuditRequest":
        if not self.text and not self.url:
            raise ValueError("Either 'text' or 'url' must be provided.")
        return self


class AIAnalysis(BaseModel):
    sentiment: str
    entities: list[str]
    engagement_triggers: list[str]


class MLPrediction(BaseModel):
    viral_score: float = Field(ge=0.0, le=1.0)
    factors: dict[str, Any] = Field(default_factory=dict)


class AuditResponse(BaseModel):
    post_id: int
    source: str
    content: str
    url: str | None
    ai_analysis: AIAnalysis
    ml_prediction: MLPrediction
