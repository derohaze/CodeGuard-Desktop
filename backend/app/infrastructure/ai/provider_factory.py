from __future__ import annotations

from app.core.config import get_settings
from app.core.exceptions import ExternalAIServiceError
from app.domain.services.ai_client import SecurityAnalysisAIClient
from app.infrastructure.ai.nvidia_security_client import NvidiaSecurityClient, RUNTIME_TASK_MODELS
from app.infrastructure.ai.providers.registry import get_provider
from app.infrastructure.services.runtime_safety_policy import ensure_allowed_outbound_url

# Providers whose wire format is OpenAI-compatible (/chat/completions) and can drive
# the scan engine. Anthropic and Gemini use different APIs and are not wired in, so
# saving them as the active provider must fail fast with an honest message.
_SUPPORTED_SCAN_PROVIDERS = {"nvidia", "security", "openai", "deepseek", "grok", "custom"}


def build_ai_client() -> SecurityAnalysisAIClient:
    settings = get_settings()
    provider_order = [item.strip().lower() for item in settings.ai_provider_order if item.strip()]
    unsupported = [provider for provider in provider_order if provider not in {"nvidia", "security"}]
    if unsupported:
        raise RuntimeError("Only the security AI client entrypoint is supported by this backend.")

    for provider in provider_order or ["security"]:
        client = _build_provider(provider, settings)
        if client is not None:
            return client
    raise RuntimeError("No supported AI transport is configured. Set NVIDIA_API_KEY or NVIDIA_API_KEYS.")


def _build_provider(provider: str, settings) -> SecurityAnalysisAIClient | None:
    if provider in {"nvidia", "security"} and NvidiaSecurityClient.is_configured(settings):
        return NvidiaSecurityClient()
    return None


def build_ai_client_from_runtime_config(config: dict) -> SecurityAnalysisAIClient:
    """Build the scan AI client from settings saved in the Settings screen.

    The saved model, base URL, and API key take precedence over env config so the
    scan actually uses what the user configured. Unsupported providers raise so the
    failure is honest and fast instead of silently running on env defaults.
    """
    provider = str(config["provider"]).strip().lower()
    if provider not in _SUPPORTED_SCAN_PROVIDERS:
        raise ExternalAIServiceError(
            f"The {provider} provider is not wired into the scan engine yet — configure NVIDIA or another OpenAI-compatible provider in Settings",
            provider=provider,
            retryable=False,
            failure_kind="configuration",
        )
    settings = get_settings()
    base_url = str(config.get("base_url") or "").strip()
    if not base_url:
        if provider in {"nvidia", "security"}:
            base_url = settings.nvidia_base_url
        else:
            try:
                base_url = get_provider(provider).default_base_url or ""
            except ValueError:
                base_url = ""
    if not base_url:
        raise ExternalAIServiceError(
            f"No base URL is configured for {provider} — open Settings → Providers and save a base URL",
            provider=provider,
            retryable=False,
            failure_kind="configuration",
        )
    try:
        ensure_allowed_outbound_url(base_url, provider=provider)
    except RuntimeError as exc:
        raise ExternalAIServiceError(
            f"The saved {provider} base URL is not allowed — it must use https and a public, non-private host",
            provider=provider,
            retryable=False,
            failure_kind="configuration",
        ) from exc
    api_key = str(config["api_key"]).strip()
    model = str(config["model"]).strip()
    return NvidiaSecurityClient(
        api_keys=(api_key,),
        base_url=base_url,
        task_models={task_name: model for task_name in RUNTIME_TASK_MODELS},
        allow_fallbacks=False,
    )
