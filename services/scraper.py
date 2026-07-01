import asyncio
import re
from typing import Any
from urllib.parse import urlparse

import httpx

from config.logging import get_logger
from config.settings import Settings, get_settings

logger = get_logger(__name__)

YOUTUBE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)([\w-]{11})"),
    re.compile(r"youtube\.com/embed/([\w-]{11})"),
)


class ContentScraper:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    async def fetch_content(self, text: str | None, url: str | None) -> dict[str, Any]:
        if url:
            logger.info("📥 Incoming Telegram/API payload: url=%s", url)
            return await self._fetch_from_url(url.strip())
        normalized = (text or "").strip()
        logger.info("📥 Incoming Telegram/API payload: text_length=%s", len(normalized))
        return {"source": "text", "content": normalized, "url": None}

    async def _fetch_from_url(self, url: str) -> dict[str, Any]:
        if self._is_youtube(url):
            return await self._fetch_youtube(url)
        if self._is_telegram(url):
            return await self._fetch_telegram(url)
        return await self._fetch_generic(url)

    @staticmethod
    def _is_youtube(url: str) -> bool:
        host = urlparse(url).netloc.lower()
        return "youtube.com" in host or "youtu.be" in host

    @staticmethod
    def _is_telegram(url: str) -> bool:
        host = urlparse(url).netloc.lower().removeprefix("www.")
        return host in {"t.me", "telegram.me"}

    @staticmethod
    def _extract_youtube_id(url: str) -> str | None:
        for pattern in YOUTUBE_PATTERNS:
            match = pattern.search(url)
            if match:
                return match.group(1)
        return None

    async def _fetch_youtube(self, url: str) -> dict[str, Any]:
        video_id = self._extract_youtube_id(url)
        if not video_id:
            logger.warning("⚠️ Could not parse YouTube video id from url=%s", url)
            return self._mock_payload("youtube", url, "Unable to parse YouTube video id.")

        api_key = self._settings.youtube_api_key
        if not api_key:
            logger.warning("⚠️ YOUTUBE_API_KEY is missing, using mock YouTube content.")
            return self._mock_payload(
                "youtube",
                url,
                f"[mock] YouTube video {video_id}. Configure YOUTUBE_API_KEY for live metadata.",
            )

        try:
            snippet = await asyncio.to_thread(self._fetch_youtube_snippet, video_id, api_key)
            title = snippet.get("title", "")
            description = snippet.get("description", "")
            content = f"{title}\n\n{description}".strip()
            logger.info("✅ YouTube metadata fetched for video_id=%s", video_id)
            return {
                "source": "youtube",
                "content": content or self._mock_content("youtube", url),
                "url": url,
            }
        except Exception as exc:
            logger.exception("❌ YouTube API request failed: %s", exc)
            return self._mock_payload("youtube", url, f"[fallback] YouTube video {video_id}.")

    @staticmethod
    def _fetch_youtube_snippet(video_id: str, api_key: str) -> dict[str, str]:
        from googleapiclient.discovery import build

        youtube = build("youtube", "v3", developerKey=api_key)
        response = youtube.videos().list(part="snippet", id=video_id).execute()
        items = response.get("items", [])
        if not items:
            return {}
        snippet = items[0].get("snippet", {})
        return {
            "title": snippet.get("title", ""),
            "description": snippet.get("description", ""),
        }

    async def _fetch_telegram(self, url: str) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()
                title_match = re.search(
                    r'<meta\s+property="og:description"\s+content="([^"]+)"',
                    response.text,
                    flags=re.IGNORECASE,
                )
                if title_match:
                    content = title_match.group(1).strip()
                    logger.info("✅ Telegram public preview fetched.")
                    return {"source": "telegram", "content": content, "url": url}
        except Exception as exc:
            logger.warning("⚠️ Telegram preview fetch failed: %s", exc)

        return self._mock_payload(
            "telegram",
            url,
            self._mock_content("telegram", url),
        )

    async def _fetch_generic(self, url: str) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()
                title_match = re.search(
                    r"<title[^>]*>([^<]+)</title>",
                    response.text,
                    flags=re.IGNORECASE,
                )
                if title_match:
                    content = title_match.group(1).strip()
                    logger.info("✅ Generic URL title fetched.")
                    return {"source": "url", "content": content, "url": url}
        except Exception as exc:
            logger.warning("⚠️ Generic URL fetch failed: %s", exc)

        return self._mock_payload("url", url, self._mock_content("url", url))

    @staticmethod
    def _mock_content(source: str, url: str) -> str:
        return f"[mock] {source} content from {url}. Ready for Pyrogram/Telethon integration."

    def _mock_payload(self, source: str, url: str, content: str) -> dict[str, Any]:
        return {"source": source, "content": content, "url": url}
