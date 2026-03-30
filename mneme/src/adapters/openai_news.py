"""OpenAI engineering source adapter."""

from __future__ import annotations

import re
import time
from datetime import UTC, datetime

import feedparser
from crawl4ai import AsyncWebCrawler, BrowserConfig

from ..models.article import Article, ArticleSeed
from ..network import browser_extra_args, disable_proxy_env
from .web import fetch_article_markdown, fetch_url_text

DATE_PATTERN = re.compile(r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4}")


class OpenAIEngineeringAdapter:
    """Fetch OpenAI engineering posts from the engineering listing page."""

    name = "openai_engineering"
    listing_url = "https://openai.com/news/engineering/"
    feed_url = "https://openai.com/news/rss.xml"

    async def fetch_latest(self, limit: int) -> list[ArticleSeed]:
        seeds = await self.fetch_history(until=datetime.now(UTC))
        return seeds[:limit]

    async def fetch_history(self, until: datetime) -> list[ArticleSeed]:
        disable_proxy_env()
        browser_config = BrowserConfig(
            headless=True,
            proxy=None,
            extra_args=browser_extra_args(),
            verbose=False,
        )
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(self.listing_url)

        seeds: list[ArticleSeed] = []
        seen_urls: set[str] = set()
        if result and result.links:
            for item in result.links.get("internal", []):
                href = item.get("href", "")
                if not href.startswith("https://openai.com/index/") or href in seen_urls:
                    continue
                text = (item.get("text") or "").strip()
                if not text:
                    continue
                seen_urls.add(href)
                published_at = self._extract_date(text)
                if published_at and published_at > until:
                    continue
                seeds.append(
                    ArticleSeed(
                        source=self.name,
                        source_type="article",
                        title=self._extract_title(text),
                        url=href,
                        external_id=href,
                        published_at=published_at,
                    )
                )

        if seeds:
            return seeds

        # Fallback: filter the general RSS feed by Engineering category.
        feed_xml = await fetch_url_text(self.feed_url)
        feed = feedparser.parse(feed_xml)
        for entry in feed.entries:
            categories = {
                getattr(tag, "term", "")
                for tag in getattr(entry, "tags", [])
                if getattr(tag, "term", "")
            }
            if "Engineering" not in categories:
                continue
            published_at = None
            if getattr(entry, "published_parsed", None):
                published_at = datetime.fromtimestamp(time.mktime(entry.published_parsed), UTC)
                if published_at > until:
                    continue
            seeds.append(
                ArticleSeed(
                    source=self.name,
                    source_type="article",
                    title=str(getattr(entry, "title", "Untitled OpenAI article")),
                    url=str(getattr(entry, "link", "")),
                    external_id=str(getattr(entry, "link", "")),
                    published_at=published_at,
                )
            )
        return [seed for seed in seeds if seed.url]

    async def fetch_article(self, seed: ArticleSeed) -> Article:
        raw_content = await fetch_article_markdown(seed.url)
        return Article(
            source=seed.source,
            source_type=seed.source_type,
            title=seed.title,
            url=seed.url,
            external_id=seed.external_id or seed.url,
            published_at=seed.published_at,
            raw_content=raw_content,
        )

    def _extract_date(self, text: str) -> datetime | None:
        match = DATE_PATTERN.search(text)
        if match is None:
            return None
        try:
            return datetime.strptime(match.group(0), "%b %d, %Y").replace(tzinfo=UTC)
        except ValueError:
            return None

    def _extract_title(self, text: str) -> str:
        match = DATE_PATTERN.search(text)
        cleaned = text[: match.start()] if match else text
        return re.sub(r"\s+", " ", cleaned).strip()
