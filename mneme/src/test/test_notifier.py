from pathlib import Path

from src.models.article import Article
from src.notifier import NotifierService
from src.settings import Settings


def build_settings() -> Settings:
    return Settings(
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


def test_build_feishu_message_uses_chinese_summary_and_original_url() -> None:
    notifier = NotifierService(build_settings())
    articles = [
        Article(
            source="openai_engineering",
            title="Harness engineering",
            url="https://openai.com/index/harness-engineering",
            raw_content="content",
            summary="English summary",
            chinese_summary="中文解释内容",
        )
    ]

    message = notifier._build_feishu_message(articles)

    assert "Mneme 飞书摘要" in message
    assert "Harness engineering" in message
    assert "中文摘要：中文解释内容" in message
    assert "原文链接：https://openai.com/index/harness-engineering" in message


def test_build_feishu_message_falls_back_to_summary_when_chinese_missing() -> None:
    notifier = NotifierService(build_settings())
    articles = [
        Article(
            source="meta_engineering",
            title="Meta article",
            url="https://example.com/meta",
            raw_content="content",
            summary="Fallback summary",
            chinese_summary="",
        )
    ]

    message = notifier._build_feishu_message(articles)

    assert "中文摘要：Fallback summary" in message
