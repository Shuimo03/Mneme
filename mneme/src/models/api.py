from __future__ import annotations

from pydantic import BaseModel

from .article import RunRecord, SchedulerState


class StatusCapabilities(BaseModel):
    anthropic_configured: bool
    telegram_enabled: bool
    feishu_enabled: bool


class StatusResponse(BaseModel):
    scheduler: SchedulerState
    last_run: RunRecord | None = None
    capabilities: StatusCapabilities


class SchedulerResponse(BaseModel):
    scheduler: SchedulerState


class RunResponse(BaseModel):
    run: RunRecord


class ResetArticlesResponse(BaseModel):
    deleted: int
