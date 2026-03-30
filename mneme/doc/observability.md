# Mneme Observability Baseline

## 1. Goal

Observability in Mneme is part of the agent feedback loop. A task is not complete if a human or agent cannot tell what ran, what failed, and what data was affected.

## 2. Current State

- The code uses standard library `logging`.
- Logs are not yet structured.
- There are no committed metrics, traces, or health endpoints.

This document defines the minimum signals the project should expose as it grows.

## 3. Logging Contract

Every long-running job or request should emit:

- `run_id`: unique identifier for one ingestion or API request.
- `source`: source name such as `meta`.
- `stage`: `fetch`, `parse`, `save`, `notify`.
- `item_count`: number of URLs or articles being processed.
- `status`: `started`, `succeeded`, `failed`.
- `duration_ms`: elapsed time when a stage completes.

Do not log secrets, tokens, or raw sensitive payloads.

## 4. Minimum Metrics

Once metrics are added, expose at least:

- ingestion runs started / succeeded / failed
- articles fetched per source
- articles parsed per source
- articles saved per source
- stage latency by source
- external request failure count

These metrics should be keyed by source and environment where possible.

## 5. Health Signals

When the FastAPI service is introduced, add:

- liveness: process is up
- readiness: dependencies and configuration are usable
- version: git SHA or release version

For workers, write a simple last-success marker or heartbeat so failed schedules are visible.

## 6. Debugging Workflow

For every incident or failed task, the repo should make it possible to answer:

- Which run failed?
- At which stage did it fail?
- Which inputs were being processed?
- Was anything partially written to `data/`?
- Can the same run be replayed locally?

## 7. Implementation Order

1. Centralize logging configuration in one module.
2. Add `run_id` and per-stage structured fields to ingestion logs.
3. Add health endpoints when the API layer exists.
4. Add metrics export once there is a long-running service or scheduler.
