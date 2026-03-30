"""Google Cloud DevOps & SRE source adapter."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from html import unescape

from playwright.async_api import async_playwright

from ..logging_config import bind_logger, get_logger
from ..models.article import Article, ArticleSeed
from ..network import browser_extra_args, create_async_http_client, disable_proxy_env
from .web import fetch_article_markdown

ARTICLE_PATH_PATTERN = re.compile(r"https://cloud\.google\.com/blog/products/devops-sre/[^\"'#?]+")
TITLE_PATTERN = re.compile(r"<[^>]+>")


class GoogleCloudDevOpsSREAdapter:
    """Fetch Google Cloud DevOps & SRE articles from the listing page."""

    name = "google_cloud_devops_sre"
    index_url = "https://cloud.google.com/blog/products/devops-sre"

    async def fetch_latest(self, limit: int) -> list[ArticleSeed]:
        seeds = await self.fetch_history(until=datetime.now(UTC))
        return seeds[:limit]

    async def fetch_history(self, until: datetime) -> list[ArticleSeed]:
        seeds = await self._fetch_with_playwright()
        if not seeds:
            seeds = await self._fetch_from_html()
        return [seed for seed in seeds if seed.published_at is None or seed.published_at <= until]

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

    async def _fetch_with_playwright(self) -> list[ArticleSeed]:
        seeds: list[ArticleSeed] = []
        seen_urls: set[str] = set()

        try:
            disable_proxy_env()
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(
                    headless=True,
                    args=browser_extra_args(),
                )
                page = await browser.new_page(viewport={"width": 1440, "height": 2400})
                await page.goto(self.index_url, wait_until="domcontentloaded", timeout=120000)
                await page.wait_for_timeout(1500)

                for _ in range(12):
                    button = page.get_by_text("Load more stories")
                    if await button.count() == 0:
                        break
                    try:
                        await button.scroll_into_view_if_needed(timeout=5000)
                        await button.click(timeout=5000)
                        await page.wait_for_timeout(1500)
                    except Exception:
                        break

                anchors = await page.eval_on_selector_all(
                    "a[href*='/blog/products/devops-sre/']",
                    "els => els.map(a => ({href: a.href, text: (a.textContent || '').trim()}))",
                )
                await browser.close()
        except Exception as exc:
            bind_logger(
                get_logger(__name__),
                source=self.name,
                stage="fetch",
            ).warning("Playwright listing fetch failed; falling back to HTML. error=%s", exc)
            return []

        for item in anchors:
            url = str(item.get("href", ""))
            title = re.sub(r"\s+", " ", str(item.get("text", ""))).strip()
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            seeds.append(
                ArticleSeed(
                    source=self.name,
                    source_type="article",
                    title=title or self._title_from_url(url),
                    url=url,
                    external_id=url,
                )
            )
        return seeds

    async def _fetch_from_html(self) -> list[ArticleSeed]:
        async with create_async_http_client(timeout=20.0) as client:
            response = await client.get(self.index_url)
            response.raise_for_status()
            html = response.text

        seeds: list[ArticleSeed] = []
        seen_urls: set[str] = set()
        for match in ARTICLE_PATH_PATTERN.finditer(html):
            url = match.group(0)
            if url in seen_urls:
                continue
            seen_urls.add(url)
            seeds.append(
                ArticleSeed(
                    source=self.name,
                    source_type="article",
                    title=self._title_from_url(url),
                    url=url,
                    external_id=url,
                )
            )
        return seeds

    def _title_from_url(self, url: str) -> str:
        slug = url.rstrip("/").split("/")[-1]
        return unescape(re.sub(r"\s+", " ", slug.replace("-", " ").title())).strip()
