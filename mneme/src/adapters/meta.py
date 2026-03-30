import logging
import time
import uuid
from datetime import datetime
from pathlib import Path

from crawl4ai import AsyncWebCrawler

from ..logging_config import bind_logger, get_logger
from ..models.article import Article
from ..storage import FileStorage, extract_title
from .adapters import BaseAdapter


class MetaAdapter(BaseAdapter):
    """Adapter for Meta engineering blog."""

    def __init__(self, output_dir: Path, date_format: str = "%Y-%m-%d", run_id: str | None = None):
        super().__init__(output_dir=output_dir)
        self.base_dir = Path(output_dir)
        self.date_format = date_format
        self.storage = FileStorage(base_dir=output_dir)
        self.run_id = run_id or str(uuid.uuid4())

    def _stage_logger(self, stage: str) -> logging.LoggerAdapter[logging.Logger]:
        return bind_logger(get_logger(__name__), run_id=self.run_id, source="meta", stage=stage)

    async def fetch(self) -> list[str]:
        """Fetch article URLs from Meta engineering blog homepage."""
        logger = self._stage_logger("fetch")
        BASE_URL = "https://engineering.fb.com"
        started_at = time.perf_counter()

        async with AsyncWebCrawler() as crawler:
            response = await crawler.arun(BASE_URL)
            if response is None:
                logger.error("Failed to fetch articles from %s", BASE_URL)
                return []

            links_data = response.links
            internal_links = links_data.get("internal", [])

            target_urls = []
            categories = {}

            for link in internal_links:
                href = link.get("href", "")
                text = link.get("text", "").strip()
                title = link.get("title", "").strip()

                if text and title:
                    # text 和 title 都不为空，用 text 作为 key，href 作为 value
                    categories[text] = href
                elif not text and not title:
                    # text 和 title 都为空，只保存 href
                    target_urls.append(href)

            duration_ms = int((time.perf_counter() - started_at) * 1000)
            logger.info(
                "Fetched article URLs: item_count=%s categories=%s duration_ms=%s",
                len(target_urls),
                len(categories),
                duration_ms,
            )
            return target_urls

    async def parse(self, url_list: list[str]) -> list[Article]:
        """Parse URLs into Article objects."""
        logger = self._stage_logger("parse")
        articles = []
        started_at = time.perf_counter()

        for url in url_list:
            logger.info("Parsing article url=%s", url)
            async with AsyncWebCrawler() as crawler:
                response = await crawler.arun(url)
                if response is None:
                    logger.error("Failed to fetch article url=%s", url)
                    continue

                # 提取 markdown 内容
                markdown = response.markdown
                if not markdown:
                    logger.warning("No content extracted url=%s", url)
                    continue

                # 使用 uuid 生成唯一 id
                article_id = str(uuid.uuid4())
                now_time = datetime.now()

                # 从 URL slug 提取标题
                slug = url.rstrip("/").split("/")[-1]
                title = slug.replace("-", " ").title()

                # 创建 Article 对象
                article = Article(
                    id=article_id,
                    source="meta",
                    title=title,
                    published_at=now_time,
                    url=url,
                    raw_content=markdown,
                )
                articles.append(article)

        duration_ms = int((time.perf_counter() - started_at) * 1000)
        logger.info("Parsed articles: item_count=%s duration_ms=%s", len(articles), duration_ms)
        return articles

    async def save(self, articles: list[Article]) -> list[Path]:
        """Save articles to file storage."""
        logger = self._stage_logger("save")
        started_at = time.perf_counter()
        saved_paths = self.storage.save_batch(
            articles, source="meta", extract_title_func=extract_title
        )
        duration_ms = int((time.perf_counter() - started_at) * 1000)
        logger.info("Saved articles: item_count=%s duration_ms=%s", len(saved_paths), duration_ms)
        return saved_paths
