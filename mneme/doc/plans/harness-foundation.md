# Harness Foundation Plan

## Goal

Refactor Mneme so the repository can support stable agent execution, not just ad hoc code changes.

## Why Now

Current gaps are structural:

- engineering rules exist, but docs are not yet a navigable system,
- CI/CD expectations are not committed as a delivery contract,
- observability requirements are not defined,
- there is no execution plan history in the repository.

These gaps make the project harder for both humans and agents to change safely.

## Scope

This phase only builds the engineering harness. It does not yet implement full FastAPI APIs, deployment automation, or production metrics infrastructure.

## Deliverables

1. `doc/README.md` as the navigation entrypoint.
2. `doc/ci-cd.md` defining merge and release checks.
3. `doc/observability.md` defining the minimum feedback loop.
4. Follow-up code changes to align `pyproject.toml`, logging, tests, and CI with those docs.

## Next Execution Steps

1. Add Ruff and mypy to `pyproject.toml` and dev dependencies.
2. Create a CI workflow that runs formatting, lint, typing, and tests.
3. Introduce centralized logging with `run_id`, `source`, and `stage`.
4. Split the codebase toward the target app structure in the style guide.
5. Add smoke tests around the Meta adapter and file storage path behavior.

## Exit Criteria

- Every contributor can find the correct rule or plan from repository docs.
- A pull request has a documented validation path.
- A failed ingestion run is diagnosable from logs without manual guesswork.
- The next refactor can proceed with less chat-only context.
