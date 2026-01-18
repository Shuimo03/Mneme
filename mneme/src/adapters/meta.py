from datetime import datetime
import logging
import uuid
from pathlib import Path

from crawl4ai import AsyncWebCrawler

from .adapters import BaseAdapter
from ..models.article import Article
from ..storage import FileStorage, extract_title


class MetaAdapter(BaseAdapter):
    """Adapter for Meta engineering blog."""

    def __init__(self, output_dir: Path, date_format: str = "%Y-%m-%d"):
        self.base_dir = Path(output_dir)
        self.date_format = date_format
        self.storage = FileStorage(base_dir=output_dir)

    async def fetch(self) -> list[str]:
        """Fetch article URLs from Meta engineering blog homepage."""
        BASE_URL = "https://engineering.fb.com"

        async with AsyncWebCrawler() as crawler:
            response = await crawler.arun(BASE_URL)
            if response is None:
                logging.error(f"Failed to fetch articles from {BASE_URL}")
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

            logging.info(f"Found {len(target_urls)} article links and {len(categories)} categorized links")
            return target_urls

    async def parse(self, url_list: list[str]) -> list[Article]:
        """Parse URLs into Article objects."""
        articles = []
        for url in url_list:
            logging.info(f"Parsing {url}")
            async with AsyncWebCrawler() as crawler:
                response = await crawler.arun(url)
                if response is None:
                    logging.error(f"Failed to fetch articles from {url}")
                    continue

                # 提取 markdown 内容
                markdown = response.markdown
                if not markdown:
                    logging.warning(f"No content extracted from {url}")
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

        return articles

    async def save(self, articles: list[Article]):
        """Save articles to file storage."""
        self.storage.save_batch(articles, source="meta", extract_title_func=extract_title)
