import asyncio
from pathlib import Path

import httpx
from anthropic import AuthenticationError

from src.models.article import Article
from src.settings import Settings
from src.summarizer import SummarizerService


def test_summarizer_falls_back_without_anthropic_key() -> None:
    settings = Settings(
        app_name="Mneme",
        database_path=Path("data/test.db"),
        anthropic_api_key=None,
        anthropic_base_url=None,
        anthropic_model="claude-sonnet-4-20250514",
        max_articles_per_source=3,
        scheduler_enabled=False,
        scheduler_hour=9,
        scheduler_minute=0,
        scheduler_timezone="Asia/Shanghai",
        telegram_bot_token=None,
        telegram_chat_id=None,
        feishu_app_id=None,
        feishu_app_secret=None,
        feishu_user_id=None,
    )
    service = SummarizerService(settings)
    article = Article(
        source="openai",
        title="A new launch",
        url="https://example.com/openai-launch",
        raw_content="A meaningful first sentence about the launch.\nSecond detail.\nThird detail.",
    )

    summarized = service._fallback_summary(article)

    assert summarized.summary
    assert summarized.source_summary
    assert summarized.chinese_summary
    assert summarized.reading_recommendation == "Read the source article for full context."


def test_summarizer_disables_remote_client_after_authentication_error() -> None:
    settings = Settings(
        app_name="Mneme",
        database_path=Path("data/test.db"),
        anthropic_api_key="bad-key",
        anthropic_base_url="https://api.minimaxi.com/anthropic",
        anthropic_model="MiniMax-M2.7",
        max_articles_per_source=3,
        scheduler_enabled=False,
        scheduler_hour=9,
        scheduler_minute=0,
        scheduler_timezone="Asia/Shanghai",
        telegram_bot_token=None,
        telegram_chat_id=None,
        feishu_app_id=None,
        feishu_app_secret=None,
        feishu_user_id=None,
    )
    service = SummarizerService(settings)
    article = Article(
        source="openai",
        title="A blocked summary request",
        url="https://example.com/blocked",
        raw_content="This content should still produce a local fallback summary even if auth fails.",
    )

    response = httpx.Response(
        401,
        request=httpx.Request("POST", "https://api.minimaxi.com/anthropic/v1/messages"),
    )

    def raise_auth_error(_: Article) -> Article:
        raise AuthenticationError(
            "invalid x-api-key",
            response=response,
            body={"error": {"message": "invalid x-api-key"}},
        )

    service._summarize_with_anthropic = raise_auth_error  # type: ignore[method-assign]

    summarized = asyncio.run(service.summarize(article))

    assert summarized.summary
    assert summarized.reading_recommendation == "Read the source article for full context."
    assert service._client is None
