import pytest
from pydantic import ValidationError

from api.schemas import AuditRequest, AuditResponse


def test_audit_request_accepts_text() -> None:
    payload = AuditRequest(text="viral content")
    assert payload.text == "viral content"
    assert payload.url is None


def test_audit_request_accepts_url() -> None:
    payload = AuditRequest(url="https://t.me/channel/1")
    assert payload.url == "https://t.me/channel/1"


def test_audit_request_requires_text_or_url() -> None:
    with pytest.raises(ValidationError):
        AuditRequest()


def test_audit_response_model() -> None:
    response = AuditResponse(
        post_id=10,
        source="text",
        content="hello",
        url=None,
        ai_analysis={"sentiment": "neutral", "entities": [], "engagement_triggers": []},
        ml_prediction={"viral_score": 0.5, "factors": {}},
    )
    assert response.post_id == 10
    assert response.ml_prediction.viral_score == 0.5
