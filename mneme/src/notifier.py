"""Notification delivery for Mneme digests."""

from __future__ import annotations

import json
from collections.abc import Iterable

import httpx

from .logging_config import bind_logger, get_logger
from .models.article import Article
from .settings import Settings


class NotifierService:
    """Send digest messages to configured IM channels."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def send_digest(self, articles: list[Article]) -> int:
        if not articles:
            return 0

        telegram_message = self._build_message(articles)
        feishu_message = self._build_feishu_message(articles)
        sent_channels = 0

        async with httpx.AsyncClient(timeout=20.0, trust_env=False) as client:
            if self.settings.telegram_enabled:
                await self._send_telegram(client, telegram_message)
                sent_channels += 1

            if self.settings.feishu_enabled:
                await self._send_feishu(client, feishu_message)
                sent_channels += 1

        bind_logger(get_logger(__name__), source="notifier", stage="send").info(
            "Notification sent channels=%s article_count=%s",
            sent_channels,
            len(articles),
        )
        return sent_channels

    async def _send_telegram(self, client: httpx.AsyncClient, message: str) -> None:
        if not self.settings.telegram_bot_token or not self.settings.telegram_chat_id:
            return

        await client.post(
            f"https://api.telegram.org/bot{self.settings.telegram_bot_token}/sendMessage",
            json={
                "chat_id": self.settings.telegram_chat_id,
                "text": message,
                "disable_web_page_preview": True,
            },
        )

    async def _send_feishu(self, client: httpx.AsyncClient, message: str) -> None:
        if (
            not self.settings.feishu_app_id
            or not self.settings.feishu_app_secret
            or not self.settings.feishu_user_id
        ):
            return

        token_response = await client.post(
            "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
            json={
                "app_id": self.settings.feishu_app_id,
                "app_secret": self.settings.feishu_app_secret,
            },
        )
        token_response.raise_for_status()
        token_payload = token_response.json()
        if int(token_payload.get("code", -1)) != 0:
            raise RuntimeError(f"Feishu token request failed: {token_payload}")

        content = {"text": message}
        message_response = await client.post(
            "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id",
            headers={"Authorization": f"Bearer {token_payload['tenant_access_token']}"},
            json={
                "receive_id": self.settings.feishu_user_id,
                "msg_type": "text",
                "content": json.dumps(content, ensure_ascii=False),
            },
        )
        message_response.raise_for_status()
        message_payload = message_response.json()
        if int(message_payload.get("code", -1)) != 0:
            raise RuntimeError(f"Feishu message request failed: {message_payload}")

    def _build_message(self, articles: Iterable[Article]) -> str:
        lines = ["Mneme Digest", ""]
        for article in articles:
            lines.append(f"{article.title} [{article.source}]")
            lines.append(article.summary or "No summary available.")
            lines.append(article.url)
            lines.append("")
        return "\n".join(lines).strip()

    def _build_feishu_message(self, articles: Iterable[Article]) -> str:
        lines = ["Mneme 飞书摘要", ""]
        for article in articles:
            chinese_summary = article.chinese_summary or article.summary or "暂无摘要。"
            lines.append(article.title)
            lines.append(f"中文摘要：{chinese_summary}")
            lines.append(f"原文链接：{article.url}")
            lines.append("")
        return "\n".join(lines).strip()
