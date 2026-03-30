from pathlib import Path

from src.database import Database
from src.models.article import Article, RunRecord, SchedulerState


def test_database_persists_articles_and_runs(tmp_path: Path) -> None:
    database = Database(tmp_path / "mneme.db")
    database.initialize()
    database.ensure_scheduler_state(
        SchedulerState(enabled=True, hour=9, minute=30, timezone="Asia/Shanghai")
    )

    article = Article(
        source="openai",
        title="A new model",
        url="https://example.com/articles/1",
        raw_content="model release details",
        summary="A concise summary.",
        bullets=["Point 1"],
        tags=["model"],
        reading_recommendation="Read it.",
    )
    database.save_article(article)
    database.record_run(
        RunRecord.succeeded(
            trigger="manual",
            processed_count=1,
            notified_channels=0,
            message="ok",
        )
    )

    articles = database.list_articles()
    last_run = database.get_last_run()

    assert len(articles) == 1
    assert articles[0].title == "A new model"
    assert last_run is not None
    assert last_run.status == "succeeded"


def test_database_updates_scheduler_state(tmp_path: Path) -> None:
    database = Database(tmp_path / "mneme.db")
    database.initialize()
    database.ensure_scheduler_state(
        SchedulerState(enabled=False, hour=9, minute=0, timezone="Asia/Shanghai")
    )

    updated = database.update_scheduler_state(
        SchedulerState(enabled=True, hour=10, minute=15, timezone="Asia/Shanghai")
    )

    assert updated.enabled is True
    assert database.get_scheduler_state().hour == 10
