import asyncio
import io
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import seaborn as sns

from config.logging import get_logger

logger = get_logger(__name__)

SENTIMENT_SCORES: dict[str, float] = {
    "positive": 0.85,
    "negative": 0.25,
    "neutral": 0.5,
    "mixed": 0.65,
}


def _build_audit_chart_sync(audit_data: dict[str, Any]) -> io.BytesIO:
    ai_analysis = audit_data.get("ai_analysis", {})
    ml_prediction = audit_data.get("ml_prediction", {})

    sentiment = str(ai_analysis.get("sentiment", "neutral")).lower()
    sentiment_score = SENTIMENT_SCORES.get(sentiment, 0.5)
    viral_score = float(ml_prediction.get("viral_score", 0.0))
    triggers = ai_analysis.get("engagement_triggers") or ["no_triggers"]

    labels = ["Viral Score", "Sentiment Index", *triggers]
    values = [viral_score, sentiment_score, *[1.0] * len(triggers)]

    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(10, 5))
    palette = sns.color_palette("viridis", n_colors=len(labels))
    sns.barplot(x=values, y=labels, hue=labels, palette=palette, ax=ax, legend=False)
    ax.set_xlim(0, 1.05)
    ax.set_xlabel("Score / Trigger Weight")
    ax.set_title("ConTelli Content Analytics")
    fig.tight_layout()

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=140, bbox_inches="tight")
    plt.close(fig)
    buffer.seek(0)
    return buffer


async def build_audit_chart(audit_data: dict[str, Any]) -> io.BytesIO:
    logger.info("📊 Generating report and charts...")
    chart = await asyncio.to_thread(_build_audit_chart_sync, audit_data)
    logger.info("✅ Matplotlib processing completed.")
    return chart
