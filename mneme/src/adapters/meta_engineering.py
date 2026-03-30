"""Meta engineering source adapter with historical support."""

from __future__ import annotations

from datetime import UTC, datetime
from html import unescape

from ..models.article import Article, ArticleSeed
from ..network import create_async_http_client
from .web import fetch_article_markdown


class MetaEngineeringAdapter:
    """Fetch Meta Engineering posts via the WordPress API."""

    name = "meta_engineering"
    api_url = "https://engineering.fb.com/wp-json/wp/v2/posts"

    async def fetch_latest(self, limit: int) -> list[ArticleSeed]:
        seeds = await self.fetch_history(until=datetime.now(UTC))
        return seeds[:limit]

    async def fetch_history(self, until: datetime) -> list[ArticleSeed]:
        seeds: list[ArticleSeed] = []
        page = 1

        async with create_async_http_client(timeout=20.0) as client:
            while True:
                response = await client.get(
                    self.api_url,
                    params={"per_page": 100, "page": page},
                )
                response.raise_for_status()
                items = response.json()
                if not items:
                    break

                page_had_results = False
                for item in items:
                    published_at = datetime.fromisoformat(item["date_gmt"]).replace(tzinfo=UTC)
                    if published_at > until:
                        continue
                    page_had_results = True
                    seeds.append(
                        ArticleSeed(
                            source=self.name,
                            source_type="article",
                            title=unescape(str(item["title"]["rendered"])),
                            url=str(item["link"]),
                            external_id=str(item["id"]),
                            published_at=published_at,
                        )
                    )

                if not page_had_results:
                    break
                page += 1

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
