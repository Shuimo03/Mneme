"""Shared web fetching helpers for source adapters."""

from __future__ import annotations

import re
from html import unescape

import httpx
from crawl4ai import AsyncWebCrawler, BrowserConfig

from ..network import browser_extra_args, create_async_http_client, disable_proxy_env

SCRIPT_PATTERN = re.compile(r"<script.*?>.*?</script>", re.IGNORECASE | re.DOTALL)
STYLE_PATTERN = re.compile(r"<style.*?>.*?</style>", re.IGNORECASE | re.DOTALL)
TAG_PATTERN = re.compile(r"<[^>]+>")
MARKDOWN_IMAGE_PATTERN = re.compile(r"!\[[^\]]*\]\([^)]+\)")
MARKDOWN_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\([^)]+\)")
MARKDOWN_HEADING_PATTERN = re.compile(r"(^|\s)#{1,6}\s*")
MARKDOWN_BULLET_PATTERN = re.compile(r"(^|\s)[*-]\s+")


def normalize_content_text(raw: str) -> str:
    html = raw
    html = MARKDOWN_IMAGE_PATTERN.sub(" ", html)
    html = MARKDOWN_LINK_PATTERN.sub(r"\1", html)
    html = SCRIPT_PATTERN.sub(" ", html)
    html = STYLE_PATTERN.sub(" ", html)
    text = TAG_PATTERN.sub(" ", html)
    text = MARKDOWN_HEADING_PATTERN.sub(" ", text)
    text = MARKDOWN_BULLET_PATTERN.sub(" ", text)
    text = unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def extract_crawl_result_text(result: object) -> str:
    markdown = getattr(result, "markdown", None)
    if markdown is not None:
        fit_markdown = getattr(markdown, "fit_markdown", None)
        if fit_markdown:
            return normalize_content_text(str(fit_markdown))
        raw_markdown = getattr(markdown, "raw_markdown", None)
        if raw_markdown:
            return normalize_content_text(str(raw_markdown))
        if isinstance(markdown, str) and markdown:
            return normalize_content_text(markdown)

    for field in ("cleaned_html", "html", "extracted_content"):
        value = getattr(result, field, None)
        if value:
            return normalize_content_text(str(value))

    return ""


async def fetch_article_with_browser(url: str) -> str:
    disable_proxy_env()
    browser_config = BrowserConfig(
        headless=True,
        proxy=None,
        extra_args=browser_extra_args(),
        verbose=False,
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url)

    if not result or not getattr(result, "success", False):
        error_message = getattr(result, "error_message", None) if result else None
        raise RuntimeError(f"Browser article fetch failed: {error_message or 'unknown error'}")

    text = extract_crawl_result_text(result)
    if not text:
        raise RuntimeError("Browser article fetch returned empty content.")
    return text[:20000]


async def fetch_article_markdown(url: str) -> str:
    """Fetch article content using browser-based extraction for clean article text."""
    return await fetch_article_with_browser(url)


async def fetch_url_text(url: str, *, timeout: float = 20.0) -> str:
    async with create_async_http_client(timeout=timeout, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.text
