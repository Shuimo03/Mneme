from datetime import datetime
from pathlib import Path

from src.models.article import Article
from src.storage.file_storage import FileStorage


def test_save_batch_writes_files_under_source_and_today(tmp_path: Path) -> None:
    storage = FileStorage(base_dir=tmp_path)
    article = Article(
        id="article-1",
        source="meta",
        title="Meta Ray Ban",
        published_at=datetime(2026, 1, 18),
        url="https://engineering.fb.com/2025/12/19/meta-ray-ban-display-from-zero-to-polish/",
        raw_content="# Meta Ray Ban Display From Zero To Polish",
    )

    saved_paths = storage.save_batch([article], source="meta")

    assert len(saved_paths) == 1
    saved_path = saved_paths[0]
    assert saved_path.exists()
    assert saved_path.parent.parent == tmp_path / "meta"
    assert saved_path.read_text() == article.raw_content


def test_save_deduplicates_filenames(tmp_path: Path) -> None:
    storage = FileStorage(base_dir=tmp_path)
    article = Article(
        id="article-1",
        source="meta",
        title="Duplicate Title",
        published_at=datetime(2026, 1, 18),
        url="https://engineering.fb.com/2025/12/19/duplicate-title/",
        raw_content="# Duplicate Title",
    )

    first_path = storage.save(article, source="meta")
    second_path = storage.save(article, source="meta")

    assert first_path is not None
    assert second_path is not None
    assert first_path.name == "Duplicate Title.md"
    assert second_path.name == "Duplicate Title_1.md"
