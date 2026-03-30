"""Anthropic engineering source adapter."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from html import unescape

from ..models.article import Article, ArticleSeed
from ..network import create_async_http_client
from .web import fetch_article_markdown


class AnthropicEngineeringAdapter:
    """Fetch Anthropic engineering posts directly from the engineering page."""

    name = "anthropic_engineering"
    index_url = "https://www.anthropic.com/engineering"
    link_pattern = re.compile(
        r'href="(/engineering/[^"]+)"[^>]*>(.*?)</a>',
        re.IGNORECASE | re.DOTALL,
    )
    tag_pattern = re.compile(r"<[^>]+>")

    async def fetch_latest(self, limit: int) -> list[ArticleSeed]:
        seeds = await self.fetch_history(until=datetime.now(UTC))
        return seeds[:limit]

    async def fetch_history(self, until: datetime) -> list[ArticleSeed]:
        async with create_async_http_client(timeout=20.0) as client:
            response = await client.get(self.index_url)
            response.raise_for_status()
            html = response.text

        seeds: list[ArticleSeed] = []
        seen_urls: set[str] = set()
        for match in self.link_pattern.finditer(html):
            url = f"https://www.anthropic.com{match.group(1)}"
            if url in seen_urls:
                continue
            title = self.tag_pattern.sub(" ", unescape(match.group(2)))
            title = re.sub(r"\s+", " ", title).strip()
            if title:
                seen_urls.add(url)
                seeds.append(
                    ArticleSeed(
                        source=self.name,
                        source_type="article",
                        title=title,
                        url=url,
                        external_id=url,
                    )
                )
        return seeds

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
