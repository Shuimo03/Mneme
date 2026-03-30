from __future__ import annotations

import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, Field


class ArticleSeed(BaseModel):
    source: str
    source_type: str = "article"
    title: str
    url: str
    published_at: datetime | None = None
    external_id: str | None = None


class Article(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: str
    source_type: str = "article"
    title: str
    published_at: datetime | None = None
    url: str
    external_id: str | None = None
    raw_content: str = ""
    summary: str = ""
    source_summary: str = ""
    chinese_summary: str = ""
    bullets: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    reading_recommendation: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    notified_at: datetime | None = None


class SchedulerState(BaseModel):
    enabled: bool
    hour: int = Field(ge=0, le=23)
    minute: int = Field(ge=0, le=59)
    timezone: str


class SchedulerUpdate(BaseModel):
    enabled: bool
    hour: int = Field(ge=0, le=23)
    minute: int = Field(ge=0, le=59)


class RunRecord(BaseModel):
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    finished_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    status: str
    trigger: str
    message: str
    processed_count: int = 0
    notified_channels: int = 0

    @classmethod
    def succeeded(
        cls,
        trigger: str,
        processed_count: int,
        notified_channels: int,
        message: str,
    ) -> RunRecord:
        finished_at = datetime.now(UTC)
        return cls(
            status="succeeded",
            trigger=trigger,
            message=message,
            processed_count=processed_count,
            notified_channels=notified_channels,
            finished_at=finished_at,
        )

    @classmethod
    def failed(
        cls,
        trigger: str,
        processed_count: int,
        notified_channels: int,
        message: str,
    ) -> RunRecord:
        finished_at = datetime.now(UTC)
        return cls(
            status="failed",
            trigger=trigger,
            message=message,
            processed_count=processed_count,
            notified_channels=notified_channels,
            finished_at=finished_at,
        )

    @classmethod
    def skipped(cls, trigger: str, message: str) -> RunRecord:
        finished_at = datetime.now(UTC)
        return cls(
            status="skipped",
            trigger=trigger,
            message=message,
            finished_at=finished_at,
        )


class SourceState(BaseModel):
    source: str
    cursor: str | None = None
    status: str = "pending"
    message: str = ""
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
