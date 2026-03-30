"""SQLite persistence for Mneme."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from .models.article import Article, RunRecord, SchedulerState, SourceState


class Database:
    """Simple SQLite-backed persistence layer."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS articles (
                    id TEXT PRIMARY KEY,
                    source TEXT NOT NULL,
                    source_type TEXT NOT NULL DEFAULT 'article',
                    title TEXT NOT NULL,
                    url TEXT NOT NULL UNIQUE,
                    external_id TEXT,
                    published_at TEXT,
                    raw_content TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    source_summary TEXT NOT NULL DEFAULT '',
                    chinese_summary TEXT NOT NULL DEFAULT '',
                    bullets_json TEXT NOT NULL,
                    tags_json TEXT NOT NULL,
                    reading_recommendation TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    notified_at TEXT
                );

                CREATE TABLE IF NOT EXISTS scheduler_settings (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    enabled INTEGER NOT NULL,
                    hour INTEGER NOT NULL,
                    minute INTEGER NOT NULL,
                    timezone TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS run_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    started_at TEXT NOT NULL,
                    finished_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    trigger_source TEXT NOT NULL,
                    message TEXT NOT NULL,
                    processed_count INTEGER NOT NULL,
                    notified_channels INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS source_state (
                    source TEXT PRIMARY KEY,
                    cursor TEXT,
                    status TEXT NOT NULL,
                    message TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )
            self._ensure_column(
                connection,
                "articles",
                "source_type",
                "TEXT NOT NULL DEFAULT 'article'",
            )
            self._ensure_column(connection, "articles", "external_id", "TEXT")
            self._ensure_column(
                connection,
                "articles",
                "source_summary",
                "TEXT NOT NULL DEFAULT ''",
            )
            self._ensure_column(
                connection,
                "articles",
                "chinese_summary",
                "TEXT NOT NULL DEFAULT ''",
            )
            connection.commit()

    def ensure_scheduler_state(self, state: SchedulerState) -> SchedulerState:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT enabled, hour, minute, timezone FROM scheduler_settings WHERE id = 1"
            ).fetchone()

            if row is None:
                connection.execute(
                    """
                    INSERT INTO scheduler_settings (id, enabled, hour, minute, timezone, updated_at)
                    VALUES (1, ?, ?, ?, ?, ?)
                    """,
                    (
                        int(state.enabled),
                        state.hour,
                        state.minute,
                        state.timezone,
                        self._now_iso(),
                    ),
                )
                connection.commit()
                return state

        return self.get_scheduler_state()

    def get_scheduler_state(self) -> SchedulerState:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT enabled, hour, minute, timezone FROM scheduler_settings WHERE id = 1"
            ).fetchone()

        if row is None:
            raise RuntimeError("Scheduler state has not been initialized.")

        return SchedulerState(
            enabled=bool(row["enabled"]),
            hour=int(row["hour"]),
            minute=int(row["minute"]),
            timezone=str(row["timezone"]),
        )

    def update_scheduler_state(self, state: SchedulerState) -> SchedulerState:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO scheduler_settings (id, enabled, hour, minute, timezone, updated_at)
                VALUES (1, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    enabled = excluded.enabled,
                    hour = excluded.hour,
                    minute = excluded.minute,
                    timezone = excluded.timezone,
                    updated_at = excluded.updated_at
                """,
                (
                    int(state.enabled),
                    state.hour,
                    state.minute,
                    state.timezone,
                    self._now_iso(),
                ),
            )
            connection.commit()
        return state

    def article_exists(self, url: str) -> bool:
        with self.connect() as connection:
            row = connection.execute("SELECT 1 FROM articles WHERE url = ?", (url,)).fetchone()
        return row is not None

    def save_article(self, article: Article) -> int:
        with self.connect() as connection:
            cursor = connection.execute(
                """
                INSERT OR REPLACE INTO articles (
                    id,
                    source,
                    source_type,
                    title,
                    url,
                    external_id,
                    published_at,
                    raw_content,
                    summary,
                    source_summary,
                    chinese_summary,
                    bullets_json,
                    tags_json,
                    reading_recommendation,
                    created_at,
                    notified_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    article.id,
                    article.source,
                    article.source_type,
                    article.title,
                    article.url,
                    article.external_id or article.url,
                    article.published_at.isoformat() if article.published_at else None,
                    article.raw_content,
                    article.summary,
                    article.source_summary,
                    article.chinese_summary,
                    json.dumps(article.bullets, ensure_ascii=False),
                    json.dumps(article.tags, ensure_ascii=False),
                    article.reading_recommendation,
                    article.created_at.isoformat(),
                    article.notified_at.isoformat() if article.notified_at else None,
                ),
            )
            connection.commit()
            return int(cursor.lastrowid or 0)

    def list_articles(self, limit: int = 50) -> list[Article]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM articles
                ORDER BY COALESCE(published_at, created_at) DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [self._row_to_article(row) for row in rows]

    def mark_articles_notified(self, article_urls: list[str]) -> None:
        if not article_urls:
            return

        placeholders = ",".join("?" for _ in article_urls)
        with self.connect() as connection:
            connection.execute(
                f"UPDATE articles SET notified_at = ? WHERE url IN ({placeholders})",
                (self._now_iso(), *article_urls),
            )
            connection.commit()

    def clear_articles(self) -> int:
        with self.connect() as connection:
            count = int(connection.execute("SELECT COUNT(*) FROM articles").fetchone()[0])
            connection.execute("DELETE FROM articles")
            connection.commit()
        return count

    def record_run(self, run: RunRecord) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO run_history (
                    started_at,
                    finished_at,
                    status,
                    trigger_source,
                    message,
                    processed_count,
                    notified_channels
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run.started_at.isoformat(),
                    run.finished_at.isoformat(),
                    run.status,
                    run.trigger,
                    run.message,
                    run.processed_count,
                    run.notified_channels,
                ),
            )
            connection.commit()

    def get_last_run(self) -> RunRecord | None:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT started_at, finished_at, status, trigger_source, message,
                       processed_count, notified_channels
                FROM run_history
                ORDER BY id DESC
                LIMIT 1
                """
            ).fetchone()

        if row is None:
            return None

        return RunRecord(
            started_at=datetime.fromisoformat(str(row["started_at"])),
            finished_at=datetime.fromisoformat(str(row["finished_at"])),
            status=str(row["status"]),
            trigger=str(row["trigger_source"]),
            message=str(row["message"]),
            processed_count=int(row["processed_count"]),
            notified_channels=int(row["notified_channels"]),
        )

    def update_source_state(self, state: SourceState) -> SourceState:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO source_state (source, cursor, status, message, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(source) DO UPDATE SET
                    cursor = excluded.cursor,
                    status = excluded.status,
                    message = excluded.message,
                    updated_at = excluded.updated_at
                """,
                (
                    state.source,
                    state.cursor,
                    state.status,
                    state.message,
                    state.updated_at.isoformat(),
                ),
            )
            connection.commit()
        return state

    def get_source_state(self, source: str) -> SourceState | None:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT source, cursor, status, message, updated_at "
                "FROM source_state WHERE source = ?",
                (source,),
            ).fetchone()
        if row is None:
            return None
        return SourceState(
            source=str(row["source"]),
            cursor=str(row["cursor"]) if row["cursor"] is not None else None,
            status=str(row["status"]),
            message=str(row["message"]),
            updated_at=datetime.fromisoformat(str(row["updated_at"])),
        )

    def _row_to_article(self, row: sqlite3.Row) -> Article:
        return Article(
            id=str(row["id"]),
            source=str(row["source"]),
            source_type=str(row["source_type"]),
            title=str(row["title"]),
            url=str(row["url"]),
            external_id=str(row["external_id"]) if row["external_id"] is not None else None,
            published_at=(
                datetime.fromisoformat(str(row["published_at"]))
                if row["published_at"] is not None
                else None
            ),
            raw_content=str(row["raw_content"]),
            summary=str(row["summary"]),
            source_summary=(
                str(row["source_summary"])
                if row["source_summary"] is not None and str(row["source_summary"]).strip()
                else str(row["summary"])
            ),
            chinese_summary=(
                str(row["chinese_summary"]) if row["chinese_summary"] is not None else ""
            ),
            bullets=json.loads(str(row["bullets_json"])),
            tags=json.loads(str(row["tags_json"])),
            reading_recommendation=str(row["reading_recommendation"]),
            created_at=datetime.fromisoformat(str(row["created_at"])),
            notified_at=(
                datetime.fromisoformat(str(row["notified_at"]))
                if row["notified_at"] is not None
                else None
            ),
        )

    def _now_iso(self) -> str:
        return datetime.now(UTC).isoformat()

    def _ensure_column(
        self,
        connection: sqlite3.Connection,
        table: str,
        column: str,
        ddl: str,
    ) -> None:
        columns = {
            str(row["name"])
            for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
        }
        if column not in columns:
            connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")
