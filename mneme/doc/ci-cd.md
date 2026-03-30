# Mneme CI/CD Baseline

## 1. Purpose

This document defines the minimum delivery contract for Mneme. The goal is not just to run checks, but to give humans and agents a repeatable way to validate changes before merge and before release.

## 2. Current State

- The repository has `uv`, `pytest`, and a draft Python/FastAPI style guide.
- A formal CI pipeline is not committed yet.
- Lint, type check, and release automation are not implemented yet.

This document is therefore the target baseline to implement next.

## 3. Required Local Commands

All commands run from `mneme/`.

```bash
uv sync --extra dev
uv run pytest
python main.py
```

Target additions once tooling is committed:

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy .
```

## 4. CI Stages

Every pull request should run these stages in order:

1. Environment setup: install dependencies with `uv sync --extra dev`.
2. Static checks: formatting, lint, and type checking.
3. Tests: unit and integration tests that do not require manual intervention.
4. Smoke run: execute the ingestion entrypoint or a narrow adapter smoke test.

The main branch should reject merges when any required stage fails.

## 5. PR Rules

- Small PRs are preferred; split refactors from feature work where possible.
- Each PR must include scope, risk, and verification steps.
- Behavior changes must update related docs in `doc/`.
- Scraper changes should note sample input URLs and expected saved output paths.

## 6. Release Baseline

Before introducing deployment automation, each release should still have:

- a tagged commit or release note entry,
- a reproducible verification command,
- a rollback path,
- a record of config changes.

## 7. Implementation Order

1. Commit Ruff and mypy configuration to `pyproject.toml`.
2. Add a CI workflow for static checks and `pytest`.
3. Add a smoke test job for the ingestion path.
4. Add release tagging and deployment steps after the web service exists.
