"""Collection orchestration for Mneme."""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Protocol

from .logging_config import bind_logger, get_logger
from .models.article import Article, ArticleSeed, RunRecord
from .network import disable_proxy_env


class SourceAdapter(Protocol):
    name: str

    async def fetch_latest(self, limit: int) -> list[ArticleSeed]:
        """Fetch the latest article metadata from a source."""

    async def fetch_history(self, until: datetime) -> list[ArticleSeed]:
        """Fetch historical article metadata up to a cutoff."""

    async def fetch_article(self, seed: ArticleSeed) -> Article:
        """Fetch the full article content for one seed."""


class Summarizer(Protocol):
    async def summarize(self, article: Article) -> Article:
        """Return an article enriched with summary fields."""


class Notifier(Protocol):
    async def send_digest(self, articles: list[Article]) -> int:
        """Send a digest notification and return the number of channels used."""


class ArticleRepository(Protocol):
    def article_exists(self, url: str) -> bool:
        """Return whether an article URL is already stored."""

    def save_article(self, article: Article) -> int:
        """Persist one article and return its row id."""

    def mark_articles_notified(self, article_urls: list[str]) -> None:
        """Mark stored articles as notified."""

    def record_run(self, run: RunRecord) -> None:
        """Persist one run record."""


class CollectorService:
    """Run the fetch -> summarize -> notify pipeline."""

    def __init__(
        self,
        repository: ArticleRepository,
        summarizer: Summarizer,
        notifier: Notifier,
        sources: list[SourceAdapter],
        max_articles_per_source: int,
    ) -> None:
        self.repository = repository
        self.summarizer = summarizer
        self.notifier = notifier
        self.sources = sources
        self.max_articles_per_source = max_articles_per_source
        self._lock = asyncio.Lock()

    async def run_once(self, trigger: str) -> RunRecord:
        if self._lock.locked():
            return RunRecord.skipped(
                trigger=trigger,
                message="A collection job is already running.",
            )

        async with self._lock:
            disable_proxy_env()
            logger = bind_logger(
                get_logger(__name__),
                source="collector",
                stage="run",
                run_id=trigger,
            )
            logger.info("Collector run started trigger=%s", trigger)

            processed_articles: list[Article] = []
            errors: list[str] = []

            for source in self.sources:
                try:
                    seeds = await source.fetch_latest(limit=self.max_articles_per_source)
                    logger.info("Fetched seeds source=%s count=%s", source.name, len(seeds))
                except Exception as exc:  # pragma: no cover - network failure path
                    errors.append(f"{source.name}: fetch failed: {exc}")
                    logger.exception("Source fetch failed source=%s", source.name)
                    continue

                for seed in seeds:
                    if self.repository.article_exists(seed.url):
                        continue

                    try:
                        article = await source.fetch_article(seed)
                        article = await self.summarizer.summarize(article)
                        self.repository.save_article(article)
                        processed_articles.append(article)
                    except Exception as exc:  # pragma: no cover - network failure path
                        errors.append(f"{source.name}: article failed: {seed.url} ({exc})")
                        logger.exception("Article processing failed url=%s", seed.url)

            notified_channels = 0
            if processed_articles:
                notified_channels = await self.notifier.send_digest(processed_articles)
                if notified_channels > 0:
                    self.repository.mark_articles_notified(
                        [article.url for article in processed_articles]
                    )

            if errors:
                run = RunRecord.failed(
                    trigger=trigger,
                    processed_count=len(processed_articles),
                    notified_channels=notified_channels,
                    message="; ".join(errors),
                )
            else:
                run = RunRecord.succeeded(
                    trigger=trigger,
                    processed_count=len(processed_articles),
                    notified_channels=notified_channels,
                    message="Run completed successfully.",
                )

            self.repository.record_run(run)
            logger.info(
                "Collector run finished status=%s processed_count=%s notified_channels=%s",
                run.status,
                run.processed_count,
                run.notified_channels,
            )
            return run
