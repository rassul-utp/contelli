import pytest

from services.ml_service import ContentViralPredictor


@pytest.fixture
def predictor() -> ContentViralPredictor:
    return ContentViralPredictor()


async def test_predict_viral_score_with_keywords(predictor: ContentViralPredictor) -> None:
    result = await predictor.predict_viral_score(
        {"content": "viral trending launch exclusive tips", "source": "text"}
    )
    assert 0.0 <= result["viral_score"] <= 1.0
    assert result["factors"]["keyword_density"] > 0.0
    assert result["factors"]["model"] == "heuristic_v1"


async def test_predict_viral_score_empty_content(predictor: ContentViralPredictor) -> None:
    result = await predictor.predict_viral_score({"content": "", "source": "text"})
    assert result["viral_score"] == 0.0
    assert result["factors"]["keyword_density"] == 0.0


def test_keyword_density_calculation(predictor: ContentViralPredictor) -> None:
    density = predictor._keyword_density("viral viral neutral")
    assert density == pytest.approx(2 / 3)
