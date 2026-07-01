# Architecture

Technical overview of ConTelli for reviewers and contributors.

## Principles

- **Loose coupling** — the Telegram bot never imports Gemini, ML, or the database. It communicates with the API over HTTP (`httpx`) only.
- **Async everywhere** — FastAPI, aiogram 3, SQLAlchemy 2 async, `google-genai` async client, and `httpx.AsyncClient`. Blocking work (Matplotlib, YouTube client) is offloaded with `asyncio.to_thread`.
- **Typed & validated** — Pydantic v2 schemas at the API boundary, `pydantic-settings` for config, `mypy` clean.

## Layers

| Layer | Package | Responsibility |
|-------|---------|----------------|
| Config | `config/` | `settings.py` (env-driven, cached), `logging.py` (emoji formatter) |
| Data | `database/` | SQLAlchemy 2 declarative models, async engine/session factory |
| Services | `services/` | `scraper.py`, `gemini_service.py`, `ml_service.py` — pure business logic, no web framework imports |
| API | `api/` | `router.py` (endpoints), `audit.py` (orchestration), `schemas.py` (contracts), `dependencies.py` (DI) |
| Bot | `bot/` | `handlers.py` (UX), `charts.py` (visualization), `api_client.py` (HTTP client) |

## Audit pipeline

`api/audit.py::run_audit` runs three coroutines concurrently with `asyncio.gather`:

1. `_save_post` — persist the scraped `Post`, return `post_id`
2. `gemini.analyze_content` — sentiment / entities / triggers
3. `predictor.predict_viral_score` — heuristic virality score

Then `_save_results` writes the `Metric` and `AILog` rows and the endpoint returns an `AuditResponse`.

## Entry points

- `main_api.py` — injects `truststore` into SSL, sets up logging, starts uvicorn with a lifespan that initializes the database schema.
- `main_bot.py` — injects `truststore`, builds the aiogram `Bot`/`Dispatcher`, and starts long polling.

## Extension points

- **ML model** — replace the heuristic in `services/ml_service.py::ContentViralPredictor.predict_viral_score` with a trained TensorFlow model at the marked integration point. `BasePredictor` defines the interface.
- **New sources** — add a branch in `services/scraper.py::_fetch_from_url` and a matching detector.
- **New AI provider** — implement a service with an `async analyze_content(text) -> dict` method and wire it through `api/dependencies.py`.

## Configuration & secrets

Settings are read once (`functools.lru_cache`) from `.env` via `pydantic-settings`. The `database_url` validator normalizes `postgresql://` to the async `postgresql+asyncpg://` driver. No secrets are hardcoded.
