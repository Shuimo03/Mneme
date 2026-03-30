"""Registry for supported article sources."""

from __future__ import annotations

from .adapters.anthropic_news import AnthropicEngineeringAdapter
from .adapters.google_devops_sre import GoogleCloudDevOpsSREAdapter
from .adapters.meta_engineering import MetaEngineeringAdapter
from .adapters.openai_news import OpenAIEngineeringAdapter
from .collector import SourceAdapter


def build_longform_sources() -> list[SourceAdapter]:
    return [
        OpenAIEngineeringAdapter(),
        AnthropicEngineeringAdapter(),
        MetaEngineeringAdapter(),
        GoogleCloudDevOpsSREAdapter(),
    ]
