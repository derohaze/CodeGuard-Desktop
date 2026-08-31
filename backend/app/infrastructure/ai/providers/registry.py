from __future__ import annotations

from app.infrastructure.ai.providers.anthropic.client import AnthropicProvider
from app.infrastructure.ai.providers.custom.client import CustomProvider
from app.infrastructure.ai.providers.deepseek.client import DeepSeekProvider
from app.infrastructure.ai.providers.gemini.client import GeminiProvider
from app.infrastructure.ai.providers.grok.client import GrokProvider
from app.infrastructure.ai.providers.nvidia.client import NvidiaProvider
from app.infrastructure.ai.providers.openai.client import OpenAIProvider

_REGISTRY = {
    "openai": OpenAIProvider(),
    "anthropic": AnthropicProvider(),
    "deepseek": DeepSeekProvider(),
    "gemini": GeminiProvider(),
    "grok": GrokProvider(),
    "nvidia": NvidiaProvider(),
    "custom": CustomProvider(),
}

PROVIDER_IDS = list(_REGISTRY.keys())


def get_provider(provider_id: str):
    pid = provider_id.lower().strip()
    if pid not in _REGISTRY:
        raise ValueError(f"Unknown provider: {provider_id}")
    return _REGISTRY[pid]


def list_providers() -> list[dict]:
    return [
        {"id": p.id, "name": p.name, "default_base_url": p.default_base_url, "docs_url": p.docs_url}
        for p in _REGISTRY.values()
    ]
