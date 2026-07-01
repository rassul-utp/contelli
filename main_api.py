import truststore

truststore.inject_into_ssl()

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from api.router import router
from config.logging import get_logger, setup_logging
from database.session import init_db

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    setup_logging()
    logger.info("🚀 FastAPI app initialization...")
    logger.info("🔄 Connecting to PostgreSQL...")
    try:
        await init_db()
        logger.info("✅ Database connected successfully!")
    except Exception as exc:
        logger.exception("❌ Database connection failed: %s", exc)
        raise
    logger.info("🚀 Uvicorn running...")
    yield


app = FastAPI(title="ConTelli", lifespan=lifespan)
app.include_router(router)


if __name__ == "__main__":
    setup_logging()
    uvicorn.run("main_api:app", host="0.0.0.0", port=8000, reload=False)
