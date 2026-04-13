from __future__ import annotations

from app.core.config import get_settings
from app.domain.services.ai_client import SecurityAnalysisAIClient
from app.infrastructure.ai.ai_response_cache import AIResponseCache
from app.infrastructure.ai.execution_policy import AIExecutionPolicy
from app.infrastructure.ai.fallback_security_client import FallbackSecurityClient
from app.infrastructure.ai.groq_security_client import GroqSecurityClient
from app.infrastructure.ai.modal_security_client import ModalSecurityClient
from app.infrastructure.ai.nvidia_security_client import NvidiaSecurityClient
from app.infrastructure.ai.provider_scheduler import ProviderScheduler
from app.infrastructure.ai.runtime_metrics import RuntimeMetrics


def build_ai_client() -> SecurityAnalysisAIClient:
    settings = get_settings()
    provider_order = [item.strip().lower() for item in settings.ai_provider_order if item.strip()]
    clients: list[SecurityAnalysisAIClient] = []

    for provider in provider_order:
        client = _build_provider(provider, settings)
        if client is not None:
            clients.append(client)

    if not clients:
        raise RuntimeError("No AI provider is configured. Set AI_PROVIDER_ORDER and provider credentials.")
    return FallbackSecurityClient(
        clients,
        execution_policy=AIExecutionPolicy(),
        scheduler=ProviderScheduler(
            concurrency_limit=settings.ai_provider_concurrency_limit,
            cooldown_seconds=settings.ai_provider_cooldown_seconds,
            failure_threshold=settings.ai_provider_failure_threshold,
            quarantine_seconds=settings.ai_provider_quarantine_seconds,
        ),
        response_cache=AIResponseCache(ttl_seconds=settings.ai_response_cache_ttl_seconds),
        runtime_metrics=RuntimeMetrics(),
    )


def _build_provider(provider: str, settings) -> SecurityAnalysisAIClient | None:
    if provider == "modal" and settings.modal_api_key:
        return ModalSecurityClient()
    if provider == "groq" and ((settings.groq_api_keys and len(settings.groq_api_keys) > 0) or settings.groq_api_key):
        return GroqSecurityClient()
    if provider == "nvidia" and settings.nvidia_api_key:
        return NvidiaSecurityClient()
    return None
