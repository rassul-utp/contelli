import html
import re

from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import BufferedInputFile, Message

from api.schemas import AuditResponse
from bot.api_client import AuditAPIClient
from bot.charts import build_audit_chart
from config.logging import get_logger
from config.settings import Settings, get_settings

logger = get_logger(__name__)

router = Router()

URL_PATTERN = re.compile(r"^https?://", re.IGNORECASE)


def create_bot(token: str) -> Bot:
    return Bot(token=token)


def create_dispatcher() -> Dispatcher:
    dispatcher = Dispatcher()
    dispatcher.include_router(router)
    return dispatcher


def _get_api_client(settings: Settings | None = None) -> AuditAPIClient:
    resolved = settings or get_settings()
    return AuditAPIClient(base_url=resolved.api_base_url)


def _is_url(value: str) -> bool:
    return bool(URL_PATTERN.match(value.strip()))


def _format_report(result: AuditResponse) -> str:
    entities = result.ai_analysis.entities or ["—"]
    triggers = result.ai_analysis.engagement_triggers or ["—"]
    preview = result.content[:180] + ("..." if len(result.content) > 180 else "")
    content_preview = html.escape(preview)
    url_line = f"\n🔗 <b>URL:</b> {html.escape(result.url)}" if result.url else ""

    entities_block = "\n".join(f"  • {html.escape(item)}" for item in entities)
    triggers_block = "\n".join(f"  • {html.escape(item)}" for item in triggers)

    return (
        "<b>📊 ConTelli Audit Report</b>\n\n"
        f"🎯 <b>Viral Score:</b> {result.ml_prediction.viral_score:.3f}\n"
        f"📈 <b>Sentiment:</b> {html.escape(result.ai_analysis.sentiment)}\n"
        f"📥 <b>Source:</b> {html.escape(result.source)}\n"
        f"🆔 <b>Post ID:</b> {result.post_id}"
        f"{url_line}\n\n"
        f"📝 <b>Content Preview:</b>\n<i>{content_preview}</i>\n\n"
        f"🤖 <b>Entities:</b>\n{entities_block}\n\n"
        f"🔥 <b>Engagement Triggers:</b>\n{triggers_block}"
    )


@router.message(CommandStart())
async def handle_start(message: Message) -> None:
    await message.answer(
        "<b>👋 Welcome to ConTelli!</b>\n\n"
        "Send me:\n"
        "  • 📝 text content\n"
        "  • 🔗 a URL (YouTube, Telegram, web)\n\n"
        "I will analyze virality, sentiment, and engagement triggers.\n\n"
        "Commands:\n"
        "  • /start — this message\n"
        "  • /help — usage guide",
        parse_mode=ParseMode.HTML,
    )


@router.message(Command("help"))
async def handle_help(message: Message) -> None:
    await message.answer(
        "<b>ℹ️ ConTelli Help</b>\n\n"
        "1️⃣ Send plain text or a link.\n"
        "2️⃣ Wait for analysis.\n"
        "3️⃣ Receive a chart + emoji report.\n\n"
        "<b>📈 How to read results:</b>\n"
        "  • 🎯 <b>Viral Score</b> — 0.0 to 1.0 prediction\n"
        "  • 📈 <b>Sentiment</b> — tone of the content\n"
        "  • 🔥 <b>Triggers</b> — hooks that may boost engagement",
        parse_mode=ParseMode.HTML,
    )


@router.message(F.text)
async def handle_text_content(message: Message) -> None:
    if not message.text:
        return

    raw_text = message.text.strip()
    if raw_text.startswith("/"):
        await message.answer("⚠️ Unknown command. Use /help.", parse_mode=ParseMode.HTML)
        return

    await message.answer(
        "📥 Content received for analysis...\n🔄 Analyzing, please wait...",
    )

    settings = get_settings()
    client = _get_api_client(settings)

    text_payload: str | None = None
    url_payload: str | None = None
    if _is_url(raw_text):
        url_payload = raw_text
        logger.info("📥 Incoming Telegram payload: url")
    else:
        text_payload = raw_text
        logger.info("📥 Incoming Telegram payload: text")

    try:
        result = await client.audit(text=text_payload, url=url_payload)
        chart_buffer = await build_audit_chart(result.model_dump())
        report = _format_report(result)

        photo = BufferedInputFile(chart_buffer.read(), filename="contelli_audit.png")
        await message.answer_photo(
            photo=photo,
            caption=report,
            parse_mode=ParseMode.HTML,
        )
        user_id = message.from_user.id if message.from_user else "unknown"
        logger.info("✅ Telegram report delivered to user_id=%s", user_id)
    except Exception as exc:
        logger.exception("❌ Bot audit flow failed: %s", exc)
        await message.answer(
            "❌ <b>Analysis failed.</b>\nPlease verify that ConTelli API is running and try again.",
            parse_mode=ParseMode.HTML,
        )
