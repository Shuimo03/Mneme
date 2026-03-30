"""Article summarization with the Anthropic SDK."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import httpx
from anthropic import Anthropic, AuthenticationError

from .logging_config import bind_logger, get_logger
from .models.article import Article
from .settings import Settings


class SummarizerService:
    """Summarize articles with Anthropic, falling back to deterministic local summaries."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client = (
            Anthropic(
                api_key=settings.anthropic_api_key,
                base_url=settings.anthropic_base_url,
                http_client=httpx.Client(trust_env=False),
            )
            if settings.anthropic_api_key
            else None
        )

    async def summarize(self, article: Article) -> Article:
        if self._client is None:
            return self._fallback_summary(article)

        try:
            return await asyncio.to_thread(self._summarize_with_anthropic, article)
        except AuthenticationError as exc:  # pragma: no cover - remote auth path
            self._client = None
            bind_logger(get_logger(__name__), source=article.source, stage="summarize").error(
                "Anthropic-compatible summary disabled after authentication failure for url=%s error=%s",
                article.url,
                exc,
            )
            return self._fallback_summary(article)
        except Exception as exc:  # pragma: no cover - network failure path
            bind_logger(get_logger(__name__), source=article.source, stage="summarize").exception(
                "Anthropic summary failed for url=%s error=%s",
                article.url,
                exc,
            )
            return self._fallback_summary(article)

    def _summarize_with_anthropic(self, article: Article) -> Article:
        assert self._client is not None
        response = self._client.messages.create(
            model=self.settings.anthropic_model,
            max_tokens=700,
            system=(
                "You summarize technical news articles for busy engineers. "
                "Return strict JSON with keys: source_summary, chinese_summary, summary, bullets, tags, "
                "reading_recommendation."
            ),
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Write `source_summary` in the article's original language. "
                        "Write `chinese_summary` as a concise Chinese explanation for Chinese readers. "
                        "Keep each summary under 140 words.\n\n"
                        f"Title: {article.title}\n"
                        f"Source: {article.source}\n"
                        f"URL: {article.url}\n\n"
                        f"Content:\n{article.raw_content[:12000]}"
                    ),
                }
            ],
        )
        parsed = self._parse_response(self._extract_response_text(response))
        return article.model_copy(
            update={
                "summary": parsed["summary"],
                "source_summary": parsed["source_summary"],
                "chinese_summary": parsed["chinese_summary"],
                "bullets": parsed["bullets"],
                "tags": parsed["tags"],
                "reading_recommendation": parsed["reading_recommendation"],
            }
        )

    def _extract_response_text(self, response: Any) -> str:
        blocks = getattr(response, "content", [])
        texts = [str(block.text).strip() for block in blocks if getattr(block, "text", None)]
        return "\n".join(texts).strip()

    def _parse_response(self, raw_text: str) -> dict[str, Any]:
        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError:
            summary = raw_text.strip() or "Summary unavailable."
            return {
                "summary": summary,
                "source_summary": summary,
                "chinese_summary": "",
                "bullets": [],
                "tags": [],
                "reading_recommendation": "",
            }

        source_summary = str(data.get("source_summary", "")).strip()
        chinese_summary = str(data.get("chinese_summary", "")).strip()
        summary = (
            str(data.get("summary", "")).strip()
            or source_summary
            or chinese_summary
            or "Summary unavailable."
        )
        bullets = [str(item).strip() for item in data.get("bullets", []) if str(item).strip()]
        tags = [str(item).strip() for item in data.get("tags", []) if str(item).strip()]
        recommendation = str(data.get("reading_recommendation", "")).strip()
        return {
            "summary": summary,
            "source_summary": source_summary or summary,
            "chinese_summary": chinese_summary,
            "bullets": bullets[:5],
            "tags": tags[:5],
            "reading_recommendation": recommendation,
        }

    # Lines that typically indicate navigation/boilerplate content
    BOILERPLATE_KEYWORDS = frozenset([
        "cookie", "privacy", "terms", "contact", "sales", "get started",
        "subscribe", "newsletter", "follow us", "copyright", "all rights reserved",
        "jump to", "skip to", "learn more", "read more", "minute read",
        "by ",  # author lines at top
    ])

    def _is_content_line(self, line: str) -> bool:
        """Check if a line is likely to be article content vs navigation/boilerplate."""
        lower = line.lower()
        # Skip short lines (likely navigation or UI elements)
        if len(line) < 50:
            return False
        # Skip lines containing common boilerplate keywords
        if any(f" {kw}" in lower for kw in self.BOILERPLATE_KEYWORDS):
            return False
        return True

    def _fallback_summary(self, article: Article) -> Article:
        lines = [line.strip() for line in article.raw_content.splitlines() if line.strip()]
        # Find lines that look like actual article content
        content_lines = [line for line in lines if self._is_content_line(line)]
        # If we don't have enough content lines, use what we have
        if len(content_lines) < 3:
            content_lines = [line for line in lines if len(line) >= 50]
        summary_line = content_lines[0] if content_lines else article.title
        bullets = [line[:180] for line in content_lines[1:4]] if len(content_lines) > 1 else [line[:180] for line in lines[:3]]
        # Extract meaningful tags from title (skip common stopwords)
        stopwords = frozenset(["the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"])
        title_words = [w.lower() for w in article.title.split() if w.lower() not in stopwords and len(w) > 2]
        tags = title_words[:3]
        return article.model_copy(
            update={
                "summary": summary_line[:280],
                "source_summary": summary_line[:280],
                "chinese_summary": "当前使用本地降级摘要。建议阅读全文获取完整细节。",
                "bullets": bullets,
                "tags": tags,
                "reading_recommendation": "Read the source article for full context.",
            }
        )
