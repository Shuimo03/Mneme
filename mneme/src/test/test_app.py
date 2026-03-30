from pathlib import Path

from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from src.app import create_app
from src.models.article import Article


def test_app_exposes_health_and_status(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("MNEME_DATABASE_PATH", str(tmp_path / "app.db"))
    monkeypatch.setenv("MNEME_SCHEDULER_ENABLED", "false")

    with TestClient(create_app()) as client:
        index = client.get("/")
        health = client.get("/health")
        status = client.get("/api/status")
        missing_api = client.get("/api/missing")

    assert index.status_code == 200
    assert index.headers["content-type"].startswith("text/html")
    assert health.status_code == 200
    assert health.json() == {"status": "ok"}
    assert status.status_code == 200
    assert "scheduler" in status.json()
    assert missing_api.status_code == 404
    assert missing_api.json() == {"detail": "Not Found"}


def test_app_can_reset_articles(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("MNEME_DATABASE_PATH", str(tmp_path / "app.db"))
    monkeypatch.setenv("MNEME_SCHEDULER_ENABLED", "false")

    app = create_app()
    app.state.database.save_article(
        Article(
            source="openai_engineering",
            title="Reset me",
            url="https://example.com/reset-me",
            raw_content="content",
        )
    )

    with TestClient(app) as client:
        before = client.get("/api/articles")
        reset = client.delete("/api/articles")
        after = client.get("/api/articles")

    assert before.status_code == 200
    assert len(before.json()) == 1
    assert reset.status_code == 200
    assert reset.json() == {"deleted": 1}
    assert after.status_code == 200
    assert after.json() == []
