from pathlib import Path

from pytest import MonkeyPatch

from src.settings import load_settings


def test_load_settings_from_yaml(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
app:
  name: YAML Mneme
  database_path: data/yaml.db
  max_articles_per_source: 5
anthropic:
  model: claude-3-7-sonnet-latest
  api_key: yaml-key
  base_url: https://api.minimaxi.com/anthropic
scheduler:
  enabled: true
  hour: 7
  minute: 45
  timezone: Asia/Shanghai
notifications:
  telegram:
    bot_token: telegram-token
    chat_id: chat-1
  feishu:
    app_id: app-id
    app_secret: app-secret
    user_id: user-1
""".strip(),
        encoding="utf-8",
    )
    monkeypatch.setenv("MNEME_CONFIG_PATH", str(config_path))

    settings = load_settings()

    assert settings.app_name == "YAML Mneme"
    assert settings.database_path == Path("data/yaml.db")
    assert settings.anthropic_model == "claude-3-7-sonnet-latest"
    assert settings.anthropic_base_url == "https://api.minimaxi.com/anthropic"
    assert settings.scheduler_enabled is True
    assert settings.scheduler_hour == 7
    assert settings.telegram_bot_token == "telegram-token"
    assert settings.feishu_app_id == "app-id"
    assert settings.feishu_app_secret == "app-secret"
    assert settings.feishu_user_id == "user-1"


def test_environment_variables_override_yaml(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
anthropic:
  model: claude-sonnet-4-20250514
  api_key: yaml-key
  base_url: https://api.minimaxi.com/anthropic
scheduler:
  enabled: false
  hour: 9
  minute: 0
  timezone: Asia/Shanghai
""".strip(),
        encoding="utf-8",
    )
    monkeypatch.setenv("MNEME_CONFIG_PATH", str(config_path))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "env-key")
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://api.override.test/anthropic")
    monkeypatch.setenv("MNEME_SCHEDULER_ENABLED", "true")
    monkeypatch.setenv("MNEME_SCHEDULER_HOUR", "11")

    settings = load_settings()

    assert settings.anthropic_api_key == "env-key"
    assert settings.anthropic_base_url == "https://api.override.test/anthropic"
    assert settings.scheduler_enabled is True
    assert settings.scheduler_hour == 11
