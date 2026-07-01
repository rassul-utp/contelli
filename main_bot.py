import truststore

truststore.inject_into_ssl()

import asyncio

from aiogram import Bot, Dispatcher

from bot.handlers import create_bot, create_dispatcher
from config.logging import get_logger, setup_logging
from config.settings import get_settings

logger = get_logger(__name__)


async def main() -> None:
    setup_logging()
    logger.info("🚀 Telegram bot initialization...")
    settings = get_settings()
    bot: Bot = create_bot(settings.telegram_bot_token)
    dp: Dispatcher = create_dispatcher()
    logger.info("🔄 Connecting bot to ConTelli API at %s", settings.api_base_url)
    logger.info("🚀 Bot polling started...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
