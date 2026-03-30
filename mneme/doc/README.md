# Mneme Docs Map

This directory is the system of record for engineering rules, plans, and operating guidance.

Start here, then drill down by task:

- `python-fastapi-style-guide.md`: code style, layering, typing, testing, and FastAPI conventions.
- `ci-cd.md`: delivery contract, required checks, branch and release expectations.
- `observability.md`: logs, metrics, health checks, run identifiers, and incident debugging signals.
- `plans/`: execution plans for larger refactors and cross-cutting work.

Authoring rules:

- Keep `AGENTS.md` short; use it as a map, not a full handbook.
- Put durable rules in `doc/`, not in chat threads.
- For non-trivial changes, add or update a plan in `doc/plans/`.
- When behavior changes, update the related runbook or standard in the same PR.
