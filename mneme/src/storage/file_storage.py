"""File storage for articles."""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Protocol

from ..models.article import Article

logger = logging.getLogger(__name__)


class UrlParser(Protocol):
    """Protocol for URL parsers."""

    def parse_date(self, url: str) -> datetime | None:
        """Parse date from URL."""
        ...

    def parse_slug(self, url: str) -> str:
        """Parse slug from URL."""
        ...


class MetaUrlParser:
    """URL parser for Meta engineering blog."""

    def parse_date(self, url: str) -> datetime | None:
        """Parse date from URL like https://engineering.fb.com/2025/12/19/..."""
        match = re.match(r"https://engineering\.fb\.com/(\d{4})/(\d{1,2})/(\d{1,2})/", url)
        if not match:
            return None
        year, month, day = match.groups()
        return datetime(int(year), int(month), int(day))

    def parse_slug(self, url: str) -> str:
        """Parse slug from URL."""
        return url.rstrip("/").split("/")[-1]


class FileStorage:
    """File storage for articles."""

    def __init__(self, base_dir: Path, url_parser: UrlParser | None = None):
        """Initialize file storage.

        Args:
            base_dir: Base directory for storing files
            url_parser: URL parser for extracting date/slug from URLs
        """
        self.base_dir = Path(base_dir)
        self.url_parser = url_parser or MetaUrlParser()

    def save(self, article: Article, source: str, extract_title_func=None) -> Path | None:
        """Save an article to file.

        Args:
            article: Article to save
            source: Source name (e.g., "meta")
            extract_title_func: Optional function to extract title from markdown

        Returns:
            Path to saved file, or None if failed
        """
        # 使用今天日期作为保存目录
        today_str = datetime.now().strftime("%Y-%m-%d")

        # 提取标题
        slug = self.url_parser.parse_slug(article.url)
        title = article.title
        if extract_title_func and article.raw_content:
            title = extract_title_func(article.raw_content, slug)

        # 构建保存路径
        save_dir = self.base_dir / source / today_str
        save_dir.mkdir(parents=True, exist_ok=True)

        # 保存为 md 文件（带去重）
        base_name = f"{title}.md"
        save_path = save_dir / base_name
        counter = 1
        while save_path.exists():
            base_name = f"{title}_{counter}.md"
            save_path = save_dir / base_name
            counter += 1

        save_path.write_text(article.raw_content)
        logger.info(f"Saved article to {save_path}")

        return save_path

    def save_batch(self, articles: list[Article], source: str, extract_title_func=None) -> list[Path]:
        """Save multiple articles to files.

        Args:
            articles: Articles to save
            source: Source name
            extract_title_func: Optional function to extract title

        Returns:
            List of saved file paths
        """
        saved_paths = []
        for article in articles:
            path = self.save(article, source, extract_title_func)
            if path:
                saved_paths.append(path)
        return saved_paths
