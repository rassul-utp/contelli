# Contributing

Thanks for your interest in ConTelli. This guide covers local setup and the checks that must pass before a pull request is merged.

## Development setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    Linux/macOS: source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env   # fill in tokens/keys
```

## Quality gate

All of the following must pass locally and in CI:

```bash
ruff format --check .
ruff check .
mypy api bot config database services main_api.py main_bot.py
pytest -q
```

- `ruff format .` auto-formats; `ruff check . --fix` auto-fixes lint issues.
- Tests run against in-memory SQLite with fake services — no external network needed.

## Conventions

- Python 3.10+ syntax; type hints on all function signatures.
- Keep business logic in `services/` free of FastAPI/aiogram imports.
- Follow the existing emoji-tagged logging style.
- Add or update tests for any behavior change.

## Pull request checklist

- [ ] `ruff format --check .` passes
- [ ] `ruff check .` passes
- [ ] `mypy` passes
- [ ] `pytest -q` is green
- [ ] New/changed behavior is covered by tests
- [ ] No secrets committed (`git check-ignore .env`)
