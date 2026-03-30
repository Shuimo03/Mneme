"""Application settings for Mneme."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _bool_value(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _int_value(value: Any, default: int) -> int:
    if value is None:
        return default
    return int(value)


def _str_value(value: Any, default: str) -> str:
    if value is None:
        return default
    return str(value)


def _optional_str(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value)


def _load_yaml_config() -> dict[str, Any]:
    config_path = Path(os.getenv("MNEME_CONFIG_PATH", "config.yaml"))
    if not config_path.is_absolute():
        project_root = Path(__file__).resolve().parent.parent
        config_path = project_root / config_path

    if not config_path.exists():
        return {}

    loaded = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if not isinstance(loaded, dict):
        raise ValueError("config.yaml must contain a top-level mapping.")
    return loaded


@dataclass(slots=True)
class Settings:
    app_name: str
    database_path: Path
    anthropic_api_key: str | None
    anthropic_base_url: str | None
    anthropic_model: str
    max_articles_per_source: int
    scheduler_enabled: bool
    scheduler_hour: int
    scheduler_minute: int
    scheduler_timezone: str
    telegram_bot_token: str | None
    telegram_chat_id: str | None
    feishu_app_id: str | None
    feishu_app_secret: str | None
    feishu_user_id: str | None

    @property
    def telegram_enabled(self) -> bool:
        return bool(self.telegram_bot_token and self.telegram_chat_id)

    @property
    def feishu_enabled(self) -> bool:
        return bool(self.feishu_app_id and self.feishu_app_secret and self.feishu_user_id)


def load_settings() -> Settings:
    config = _load_yaml_config()
    app_config = config.get("app", {}) if isinstance(config.get("app"), dict) else {}
    anthropic_config = (
        config.get("anthropic", {}) if isinstance(config.get("anthropic"), dict) else {}
    )
    scheduler_config = (
        config.get("scheduler", {}) if isinstance(config.get("scheduler"), dict) else {}
    )
    notifications_config = (
        config.get("notifications", {})
        if isinstance(config.get("notifications"), dict)
        else {}
    )
    telegram_config = (
        notifications_config.get("telegram", {})
        if isinstance(notifications_config.get("telegram"), dict)
        else {}
    )
    feishu_config = (
        notifications_config.get("feishu", {})
        if isinstance(notifications_config.get("feishu"), dict)
        else {}
    )

    return Settings(
        app_name=os.getenv("MNEME_APP_NAME", _str_value(app_config.get("name"), "Mneme")),
        database_path=Path(
            os.getenv(
                "MNEME_DATABASE_PATH",
                _str_value(app_config.get("database_path"), "data/mneme.db"),
            )
        ),
        anthropic_api_key=os.getenv(
            "ANTHROPIC_API_KEY",
            _optional_str(anthropic_config.get("api_key")),
        ),
        anthropic_base_url=os.getenv(
            "ANTHROPIC_BASE_URL",
            _optional_str(anthropic_config.get("base_url")),
        ),
        anthropic_model=os.getenv(
            "ANTHROPIC_MODEL",
            _str_value(anthropic_config.get("model"), "claude-sonnet-4-20250514"),
        ),
        max_articles_per_source=int(
            os.getenv(
                "MNEME_MAX_ARTICLES_PER_SOURCE",
                _int_value(app_config.get("max_articles_per_source"), 3),
            )
        ),
        scheduler_enabled=_bool_env(
            "MNEME_SCHEDULER_ENABLED",
            _bool_value(scheduler_config.get("enabled"), False),
        ),
        scheduler_hour=int(
            os.getenv(
                "MNEME_SCHEDULER_HOUR",
                _int_value(scheduler_config.get("hour"), 9),
            )
        ),
        scheduler_minute=int(
            os.getenv(
                "MNEME_SCHEDULER_MINUTE",
                _int_value(scheduler_config.get("minute"), 0),
            )
        ),
        scheduler_timezone=os.getenv(
            "MNEME_SCHEDULER_TIMEZONE",
            _str_value(scheduler_config.get("timezone"), "Asia/Shanghai"),
        ),
        telegram_bot_token=os.getenv(
            "TELEGRAM_BOT_TOKEN",
            _optional_str(telegram_config.get("bot_token")),
        ),
        telegram_chat_id=os.getenv(
            "TELEGRAM_CHAT_ID",
            _optional_str(telegram_config.get("chat_id")),
        ),
        feishu_app_id=os.getenv(
            "FEISHU_APP_ID",
            _optional_str(feishu_config.get("app_id")),
        ),
        feishu_app_secret=os.getenv(
            "FEISHU_APP_SECRET",
            _optional_str(feishu_config.get("app_secret")),
        ),
        feishu_user_id=os.getenv(
            "FEISHU_USER_ID",
            _optional_str(feishu_config.get("user_id")),
        ),
    )
