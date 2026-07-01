# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.0.0] - 2026-07-01

### Added

- Async FastAPI service with `GET /api/v1/health` and `POST /api/v1/audit`
- Telegram bot (aiogram 3) with `/start`, `/help`, chart + emoji report
- Content scraping for YouTube (Data API), Telegram previews, web pages, and raw text
- Google Gemini analysis (sentiment, entities, engagement triggers) with structured `response_schema`
- Heuristic virality predictor with a TensorFlow-ready integration point
- Async SQLAlchemy 2 models: `posts`, `metrics`, `ai_logs`
- Emoji-tagged logging formatter
- Docker Compose (`web_api`, `tg_bot`, `db`) with healthchecks
- pytest suite (32 tests), `ruff` + `mypy` config in `pyproject.toml`, GitHub Actions CI
- `truststore` SSL injection to support TLS-inspected networks

### Fixed

- Gemini model updated from deprecated `gemini-1.5-flash` to `gemini-2.5-flash`
- `CERTIFICATE_VERIFY_FAILED` on outbound HTTPS resolved via OS trust store
