import asyncio
from datetime import datetime
from pathlib import Path

from src.adapters.adapters import BaseAdapter
from src.models.article import Article


class DummyAdapter(BaseAdapter):
    def __init__(self) -> None:
        super().__init__(output_dir=Path("data/test"))
        self.saved_articles: list[Article] = []

    async def fetch(self) -> list[str]:
        return ["https://example.com/article"]

    async def parse(self, url_list: list[str]) -> list[Article]:
        return [
            Article(
                id="article-1",
                source="dummy",
                title="Dummy Article",
                published_at=datetime(2026, 1, 1),
                url=url_list[0],
                raw_content="# Dummy Article",
            )
        ]

    async def save(self, articles: list[Article]) -> list[Path]:
        self.saved_articles = articles
        return [Path("data/test/dummy.md")]


def test_base_adapter_run_awaits_parse_and_saves_articles() -> None:
    adapter = DummyAdapter()

    articles = asyncio.run(adapter.run())

    assert len(articles) == 1
    assert articles == adapter.saved_articles
