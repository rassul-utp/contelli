# ConTelli

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![CI](https://github.com/rassul-utp/contelli/actions/workflows/ci.yml/badge.svg)](https://github.com/rassul-utp/contelli/actions/workflows/ci.yml)
[![Lint: Ruff](https://img.shields.io/badge/lint-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Typing: mypy](https://img.shields.io/badge/typing-mypy-2a6db2.svg)](https://mypy-lang.org/)

**AI content intelligence & trend auditor** — a Telegram bot backed by an async FastAPI service that scrapes content from **YouTube / Telegram / the web**, runs **Google Gemini** sentiment, entity, and engagement-trigger analysis, computes a **virality score**, and returns a chart plus an emoji report in seconds.

Built with **Python 3.10+ · FastAPI · aiogram 3 · Google Gemini · SQLAlchemy 2 (async) · PostgreSQL · Matplotlib · Docker**.

> Layered async architecture: the bot talks only to the API over HTTP; the API orchestrates scraping, AI, ML, and persistence in parallel.

---

## Table of contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Quick start](#quick-start)
- [Using the Telegram bot](#using-the-telegram-bot)
- [Screenshots](#screenshots)
- [How it works](#how-it-works)
- [API reference](#api-reference)
- [Configuration](#configuration)
- [Database schema](#database-schema)
- [Repository layout](#repository-layout)
- [Testing & code quality](#testing--code-quality)
- [CI](#ci)
- [Design decisions](#design-decisions)
- [Issues encountered & fixes](#issues-encountered--fixes)
- [Security notes](#security-notes)
- [Contributing & docs](#contributing--docs)
- [Publishing checklist](#publishing-checklist)
- [Disclaimer](#disclaimer)
- [License](#license)

---

## Overview

| | |
|---|---|
| **Domain** | Content analytics · social media intelligence · AI integration |
| **Stack** | Python · FastAPI · aiogram 3 · Google Gemini · SQLAlchemy 2 (async) · PostgreSQL · Pandas · Matplotlib · Seaborn |
| **Platform** | Cross-platform (local) · Docker Compose (API + bot + PostgreSQL) |
| **Output** | Telegram chart + emoji report; REST `POST /api/v1/audit` JSON |

**For hiring managers:** end-to-end delivery — content scraping → Gemini AI analysis → heuristic ML virality scoring → async `asyncio.gather` orchestration → PostgreSQL persistence → Telegram UX with generated charts → Docker Compose → pytest suite with ruff + mypy in CI.

---

## Features

- Multi-source scraping — YouTube (Data API), Telegram public previews, generic web pages, or raw text
- Gemini AI analysis — sentiment, named entities, and engagement triggers via structured JSON (`response_schema`)
- Virality scoring — heuristic predictor (keyword density + length), TensorFlow-ready integration point
- Parallel pipeline — DB write, Gemini call, and ML scoring run concurrently with `asyncio.gather`
- Telegram UX — `/start`, `/help`, chart image + HTML report with emoji indicators
- Persistence — posts, metrics, and raw AI logs in PostgreSQL (async SQLAlchemy 2)
- Resilient — graceful fallbacks on API limits/parse errors; TLS via OS trust store (`truststore`)
- Structured logging — emoji-tagged log formatter for readable multi-service output
- Fully typed — `mypy` clean; linted and formatted with `ruff`; 32 pytest tests; GitHub Actions CI
- Containerized — three services (`web_api`, `tg_bot`, `db`) with healthchecks in Docker Compose

---

## Architecture

**Principle:** loose coupling + async orchestration. The bot never imports Gemini, ML, or the database — it only calls the API over `httpx`.

```mermaid
flowchart LR
    subgraph tg [Telegram layer]
        H[handlers.py]
        CH[charts.py]
        AC[api_client.py]
    end
    subgraph api [API layer]
        R[router.py]
        AU[audit.py]
        SC[schemas.py]
    end
    subgraph svc [Services]
        S[scraper.py]
        G[gemini_service.py]
        M[ml_service.py]
    end
    subgraph data [Persistence]
        DB[(PostgreSQL)]
    end

    H --> AC -->|HTTP| R --> AU
    AU --> S
    AU --> G
    AU --> M
    AU --> DB
    AU --> SC --> AC --> CH --> H
```

**Layer responsibilities**

| Layer | Responsibility |
|-------|----------------|
| `config/` | Environment-driven settings + emoji logging |
| `database/` | SQLAlchemy 2.0 async models and sessions |
| `services/` | Scraping, Gemini AI, ML scoring (no FastAPI/aiogram imports) |
| `api/` | HTTP contracts, validation, audit orchestration |
| `bot/` | Telegram UX, visualization, API client |

**Data flow (audit request)**

```mermaid
sequenceDiagram
    participant U as User (Telegram)
    participant B as tg_bot (aiogram)
    participant A as web_api (FastAPI)
    participant S as ContentScraper
    participant G as GeminiService
    participant M as ContentViralPredictor
    participant D as PostgreSQL

    U->>B: /start, text, or URL
    B->>U: 📥 Content received... 🔄 Analyzing...
    B->>A: POST /api/v1/audit
    A->>S: fetch_content()
    S-->>A: content + source + url

    par Parallel processing
        A->>D: save Post
        A->>G: analyze_content()
        A->>M: predict_viral_score()
    end

    G-->>A: sentiment, entities, triggers
    M-->>A: viral_score, factors
    D-->>A: post_id
    A->>D: save Metric + AILog
    A-->>B: AuditResponse JSON
    B->>B: Matplotlib chart (async thread)
    B->>U: 📊 photo + emoji report
```

---

## Quick start

### Option A — Docker Compose (recommended)

Runs API, bot, and PostgreSQL together.

```bash
git clone https://github.com/rassul-utp/contelli.git
cd contelli
cp .env.example .env        # fill in tokens/keys (see Configuration)
docker compose up --build
```

For Docker, set the container hostnames in `.env`:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/contelli
API_BASE_URL=http://web_api:8000
```

### Option B — Run from source

**Requirements:** Python 3.10+ (tested on 3.12), PostgreSQL 15+ running locally.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    Linux/macOS: source .venv/bin/activate
pip install -r requirements-dev.txt   # runtime + tooling (use requirements.txt for runtime only)
cp .env.example .env
```

Set local hosts in `.env`:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/contelli
API_BASE_URL=http://localhost:8000
```

Run the API and bot in separate terminals:

```bash
python main_api.py    # http://localhost:8000  (docs at /docs)
python main_bot.py    # starts Telegram polling
```

---

## Using the Telegram bot

1. Open your ConTelli bot in Telegram and send `/start`.
2. Send **plain text** (a post idea, caption) or a **URL** (YouTube, `t.me/...`, or any web page).
3. Receive a **bar chart** + a **text report** with emoji indicators.

| Command | Description |
|---------|-------------|
| `/start` | Welcome message and quick guide |
| `/help` | Usage and metric explanation |

**Reading the report**

| Field | Meaning |
|-------|---------|
| 🎯 **Viral Score** | 0.0–1.0 predicted engagement potential (0–0.3 low · 0.3–0.6 moderate · 0.6–1.0 high) |
| 📈 **Sentiment** | `positive`, `negative`, `neutral`, or `mixed` |
| 🤖 **Entities** | Key topics, brands, or names found in the content |
| 🔥 **Engagement Triggers** | Hooks that may drive clicks, shares, or comments |

---

## Screenshots

End-to-end demo: send a link, receive a chart + AI report with entities and engagement triggers.

### 1. Start the bot and send a link

`/start` shows the welcome guide; send any YouTube / Telegram / web URL (or plain text).

![Start and input](docs/screenshots/01-start-and-input.png)

### 2. Audit report with chart

The bot returns a metrics bar chart plus a report: viral score, sentiment, source, and content preview.

![Audit report](docs/screenshots/02-audit-report.png)

### 3. Entities and engagement triggers

Gemini lists key topics/brands/names and the hooks that may drive engagement.

![Entities and triggers](docs/screenshots/03-entities-triggers.png)

### 4. Send another link

Any new content starts a fresh analysis.

![URL input](docs/screenshots/04-url-input.png)

### 5. Second audit report

Sentiment can differ per content (here `mixed` for an ad-heavy video).

![Audit report 2](docs/screenshots/05-audit-report.png)

### 6. Entities and triggers for the second post

![Entities and triggers 2](docs/screenshots/06-entities-triggers.png)

---

## How it works

### Scraping (`services/scraper.py`)

| Source | Method |
|--------|--------|
| YouTube | Extract video id → YouTube Data API v3 `videos.list(snippet)` (title + description) |
| Telegram | Fetch public page → parse `og:description` meta |
| Web | Fetch page → parse `<title>` |
| Text | Used as-is |

If a key is missing or a request fails, the scraper returns a safe mock/fallback payload so the pipeline never crashes.

### AI analysis (`services/gemini_service.py`)

Gemini is called with `response_mime_type="application/json"` **and** a strict `response_schema`, guaranteeing a `{sentiment, entities, engagement_triggers}` object. Markdown fences are stripped and JSON is validated; on API limits (429) or parse errors it degrades to a neutral fallback.

### Virality scoring (`services/ml_service.py`)

Heuristic `heuristic_v1`: `length_factor * 0.45 + keyword_density * 0.55`, clamped to `[0, 1]`. A clearly marked integration point is ready to swap in a trained TensorFlow model.

### Logging (`config/logging.py`)

A custom `EmojiFormatter` prefixes log lines with context emojis (🚀 startup, 🔄 in-progress, ✅ success, 🤖 AI, 📥 incoming, 📊 chart, ⚠️ warning, ❌ error) for readable multi-service output.

---

## API reference

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/health` | Service health check |
| `POST` | `/api/v1/audit` | Run a full content audit |

Interactive docs (Swagger UI): `http://localhost:8000/docs`.

**Example request**

```json
POST /api/v1/audit
{ "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ" }
```

```json
POST /api/v1/audit
{ "text": "Viral launch tips for creators" }
```

**Example response**

```json
{
  "post_id": 1,
  "source": "text",
  "content": "Viral launch tips for creators",
  "url": null,
  "ai_analysis": {
    "sentiment": "positive",
    "entities": ["creators", "launch"],
    "engagement_triggers": ["tips", "viral"]
  },
  "ml_prediction": {
    "viral_score": 0.612,
    "factors": {
      "text_length": 32,
      "keyword_density": 0.125,
      "length_factor": 0.032,
      "source": "text",
      "model": "heuristic_v1"
    }
  }
}
```

---

## Configuration

All settings load from `.env` via `pydantic-settings` (see `.env.example`).

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | yes | Bot token from @BotFather |
| `TELEGRAM_API_ID` | yes | Telegram API id (my.telegram.org) |
| `TELEGRAM_API_HASH` | yes | Telegram API hash |
| `GEMINI_API_KEY` | yes | Google Gemini API key |
| `GEMINI_MODEL` | no | Model name (default `gemini-2.5-flash`) |
| `DATABASE_URL` | yes | Async PostgreSQL DSN (`postgresql+asyncpg://...`) |
| `API_BASE_URL` | no | Bot → API base URL (default `http://localhost:8000`) |
| `YOUTUBE_API_KEY` | no | Enables live YouTube metadata (otherwise mock) |

---

## Database schema

| Table | Purpose |
|-------|---------|
| `posts` | Raw content, source, optional URL, timestamp |
| `metrics` | Viral score + sentiment per post |
| `ai_logs` | Raw Gemini JSON response per post |

---

## Repository layout

```
contelli/
├── main_api.py            # FastAPI entry point (truststore + uvicorn)
├── main_bot.py            # aiogram bot entry point (polling)
├── api/
│   ├── router.py          # /health, /audit endpoints
│   ├── audit.py           # Audit orchestration (parallel pipeline)
│   ├── schemas.py         # Pydantic request/response models
│   └── dependencies.py    # FastAPI DI providers
├── services/
│   ├── scraper.py         # YouTube / Telegram / web content fetch
│   ├── gemini_service.py  # Gemini sentiment / entities / triggers
│   └── ml_service.py      # Heuristic virality predictor (TF-ready)
├── bot/
│   ├── handlers.py        # Commands + message flow
│   ├── charts.py          # Matplotlib chart (async thread)
│   └── api_client.py      # httpx client → API
├── config/                # settings.py (pydantic-settings), logging.py (emoji)
├── database/              # SQLAlchemy 2 async models + session
├── tests/                 # pytest suite (async, in-memory SQLite)
├── docker/                # app.Dockerfile, bot.Dockerfile
├── docs/screenshots/      # README demo images
├── .github/workflows/     # GitHub Actions (CI)
├── docker-compose.yml
├── pyproject.toml         # ruff + mypy + pytest config
├── requirements.txt       # runtime dependencies
└── requirements-dev.txt   # + linting, typing, testing
```

**Not committed** (see `.gitignore`): `.env`, `.venv/`, `__pycache__/`, `.mypy_cache/`, `.ruff_cache/`.

---

## Testing & code quality

Tooling is configured in `pyproject.toml` (`ruff`, `mypy` with the Pydantic plugin, `pytest`). Tests use an in-memory SQLite database and fake services — no real PostgreSQL, Gemini, or network needed.

```bash
pip install -r requirements-dev.txt
ruff format .        # auto-format
ruff check .         # lint
mypy api bot config database services main_api.py main_bot.py   # type check
pytest -q            # 32 tests
```

| Suite | Coverage |
|-------|----------|
| `test_api.py` | Health + audit endpoints, persistence |
| `test_scraper.py` | Source routing, YouTube id extraction |
| `test_gemini_service.py` | JSON parsing, markdown fences, 429 fallback |
| `test_ml_service.py` | Keyword density, score bounds |
| `test_bot.py` | URL detection, report formatting, chart bytes |
| `test_schemas.py` | Request validation, response models |
| `test_config.py` | Settings, emoji formatter, logging idempotency |

> **SSL note (Windows / corporate networks):** if outbound HTTPS to Google/Telegram fails with `CERTIFICATE_VERIFY_FAILED`, the machine is intercepting TLS with a custom root CA. Both entry points call `truststore.inject_into_ssl()` at startup to trust the OS certificate store and resolve this automatically.

---

## CI

GitHub Actions (`.github/workflows/ci.yml`) runs on every push and pull request:

1. `ruff format --check .`
2. `ruff check .`
3. `mypy` on all source packages
4. `pytest -q`

---

## Design decisions

| Decision | Why |
|----------|-----|
| Bot → API over HTTP only | Loose coupling; API and bot are independently deployable |
| `asyncio.gather` pipeline | Parallel DB + Gemini + ML — no blocking the event loop |
| Gemini `response_schema` | Guarantees structured JSON, not just a prompt request |
| Heuristic ML stub | Ships a working score with a clean TensorFlow swap-in point |
| `pydantic-settings` | Type-safe config from `.env`, validated at startup, no hardcoded secrets |
| `truststore` at entry points | Fixes TLS interception without weakening verification |
| Emoji log formatter | Readable, scannable multi-service logs |

---

## Issues encountered & fixes

A short log of problems hit during development and how they were resolved.

| # | Problem | Root cause | Fix |
|---|---------|-----------|-----|
| 1 | API crashed with `ConnectionRefusedError` on startup | PostgreSQL not installed, port 5432 closed | Installed PostgreSQL 17, created the `contelli` database |
| 2 | `CERTIFICATE_VERIFY_FAILED` on all outbound HTTPS (Telegram, YouTube, Gemini) | Local TLS inspection uses a custom root CA absent from `certifi` | Added `truststore.inject_into_ssl()` at both entry points to trust the OS certificate store |
| 3 | Scraper returned `[fallback]` and AI returned `api_limit_or_parse_fallback` | Downstream effect of the SSL failure above | Resolved together with issue #2 |
| 4 | Gemini `404 NOT_FOUND: models/gemini-1.5-flash` | Model deprecated / unavailable on API `v1beta` | Switched to `gemini-2.5-flash` (`.env` + settings default) |
| 5 | `[Errno 10048] bind on 0.0.0.0:8000` on restart | Previous API process still holding the port | Free the port before restart (kill the owning PID) |
| 6 | `test_settings_default_gemini_model` failing | Test asserted the old model name | Updated the expected value to `gemini-2.5-flash` |
| 7 | No lint / type / format gate | Missing tooling config | Added `pyproject.toml` (ruff + mypy + pytest) and CI |

---

## Security notes

- All secrets load from `.env` via `pydantic-settings`
- `.env` is git-ignored; use `.env.example` as a template
- Never commit tokens, API keys, or DB credentials
- User-supplied content is HTML-escaped before being rendered in Telegram

---

## Contributing & docs

| Document | Audience |
|----------|----------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Reviewers — layers, async flow, extension points |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contributors — setup, lint, PR checklist |
| [CHANGELOG.md](CHANGELOG.md) | Release history |

**Suggested code-review path:** `api/audit.py` → `services/*` → `bot/handlers.py` → `tests/`.

---

## Publishing checklist

Before the first push to [rassul-utp/contelli](https://github.com/rassul-utp):

1. Ensure `.env` is **not** tracked (`git check-ignore .env`)
2. Screenshots are in `docs/screenshots/` (done)
3. Create the repo on GitHub and push:

```bash
git init
git add .
git commit -m "Initial commit: ConTelli"
git branch -M main
git remote add origin https://github.com/rassul-utp/contelli.git
git push -u origin main
```

4. Optional repo topics: `python`, `fastapi`, `aiogram`, `telegram-bot`, `gemini`, `content-analytics`, `asyncio`

---

## Disclaimer

Decision-support tool only. Virality scores are heuristic estimates and AI analysis may contain errors; results do not guarantee real-world performance. Respect the terms of service of Telegram, YouTube, and Google Gemini.

---

## License

[MIT](LICENSE) © Rasul Utepbergenov
