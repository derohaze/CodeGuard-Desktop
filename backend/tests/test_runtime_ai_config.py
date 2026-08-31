from __future__ import annotations

import pytest

from app.core.exceptions import ExternalAIServiceError
from app.infrastructure.ai.nvidia_security_client import RUNTIME_TASK_MODELS
from app.infrastructure.ai.provider_factory import build_ai_client_from_runtime_config
from app.infrastructure.ai.providers.encryption import encrypt_api_key
from app.infrastructure.services.scan.scan_execution_service import ScanExecutionService
from app.infrastructure.settings.runtime_settings_service import RuntimeSettingsService


class _FakeRuntimeSettingsRepository:
    def __init__(self, document: dict) -> None:
        self.document = document

    async def get(self) -> dict:
        return self.document


def _runtime_service(document: dict) -> RuntimeSettingsService:
    return RuntimeSettingsService(_FakeRuntimeSettingsRepository(document))


def test_runtime_config_builds_client_with_saved_model_key_and_url() -> None:
    client = build_ai_client_from_runtime_config(
        {
            "provider": "nvidia",
            "api_key": "saved-key",
            "base_url": "https://integrate.api.nvidia.com/v1",
            "model": "deepseek-ai/deepseek-v4-flash-0731",
        }
    )

    assert client.api_keys == ("saved-key",)
    assert client.base_url == "https://integrate.api.nvidia.com/v1"
    # The saved model must win over env defaults (which previously used a
    # different model that 404'd) for every scan task
    for task_name in RUNTIME_TASK_MODELS:
        assert client.model_router.route(task_name) == "deepseek-ai/deepseek-v4-flash-0731"
    # No env-configured fallback models may leak into a runtime-configured client
    assert client.model_router.route_candidates("repository_map") == ["deepseek-ai/deepseek-v4-flash-0731"]


def test_runtime_config_uses_registry_default_base_url_when_saved_url_is_empty() -> None:
    client = build_ai_client_from_runtime_config(
        {
            "provider": "deepseek",
            "api_key": "saved-key",
            "base_url": "",
            "model": "deepseek-chat",
        }
    )

    assert client.base_url == "https://api.deepseek.com/v1"
    assert client.api_keys == ("saved-key",)
    assert client.model_router.route("path_review") == "deepseek-chat"


def test_runtime_config_rejects_unsupported_provider() -> None:
    with pytest.raises(ExternalAIServiceError) as exc_info:
        build_ai_client_from_runtime_config(
            {
                "provider": "anthropic",
                "api_key": "saved-key",
                "base_url": "",
                "model": "claude-3-5-sonnet",
            }
        )

    assert exc_info.value.retryable is False
    assert exc_info.value.failure_kind == "configuration"


def test_runtime_config_rejects_disallowed_base_url() -> None:
    with pytest.raises(ExternalAIServiceError) as exc_info:
        build_ai_client_from_runtime_config(
            {
                "provider": "nvidia",
                "api_key": "saved-key",
                "base_url": "http://127.0.0.1:8000/v1",
                "model": "some-model",
            }
        )

    assert exc_info.value.retryable is False
    assert exc_info.value.failure_kind == "configuration"


def test_runtime_config_requires_base_url_for_custom_provider() -> None:
    with pytest.raises(ExternalAIServiceError) as exc_info:
        build_ai_client_from_runtime_config(
            {
                "provider": "custom",
                "api_key": "saved-key",
                "base_url": "",
                "model": "my-model",
            }
        )

    assert exc_info.value.failure_kind == "configuration"


@pytest.mark.asyncio
async def test_get_ai_client_config_returns_none_when_unconfigured() -> None:
    service = _runtime_service(
        {
            "ai_provider": None,
            "ai_model": None,
            "ai_base_url": None,
            "ai_api_key_encrypted": "",
        }
    )

    assert await service.get_ai_client_config() is None


@pytest.mark.asyncio
async def test_get_ai_client_config_decrypts_saved_key() -> None:
    plain_key = "sk-test-secret-value"
    service = _runtime_service(
        {
            "ai_provider": "nvidia",
            "ai_model": "deepseek-ai/deepseek-v4-flash-0731",
            "ai_base_url": "https://integrate.api.nvidia.com/v1",
            "ai_api_key_encrypted": encrypt_api_key(plain_key),
        }
    )

    assert await service.get_ai_client_config() == {
        "provider": "nvidia",
        "api_key": plain_key,
        "base_url": "https://integrate.api.nvidia.com/v1",
        "model": "deepseek-ai/deepseek-v4-flash-0731",
    }


def _scan_service_with_runtime(document: dict | None) -> ScanExecutionService:
    service = object.__new__(ScanExecutionService)
    service.ai_client = object()
    if document is None:
        service.runtime_settings_service = None
    else:
        service.runtime_settings_service = _runtime_service(document)
    return service


@pytest.mark.asyncio
async def test_scan_resolves_runtime_ai_client_when_configured() -> None:
    service = _scan_service_with_runtime(
        {
            "ai_provider": "nvidia",
            "ai_model": "saved-model",
            "ai_base_url": "",
            "ai_api_key_encrypted": encrypt_api_key("saved-key"),
        }
    )

    client = await service._resolve_ai_client()

    assert client.api_keys == ("saved-key",)
    assert client.model_router.route("repository_map") == "saved-model"


@pytest.mark.asyncio
async def test_scan_keeps_env_client_when_no_runtime_config() -> None:
    service = _scan_service_with_runtime(None)

    assert await service._resolve_ai_client() is service.ai_client


@pytest.mark.asyncio
async def test_scan_keeps_env_client_when_runtime_not_configured() -> None:
    service = _scan_service_with_runtime(
        {
            "ai_provider": None,
            "ai_model": None,
            "ai_base_url": None,
            "ai_api_key_encrypted": "",
        }
    )

    assert await service._resolve_ai_client() is service.ai_client


@pytest.mark.asyncio
async def test_scan_fails_fast_for_unsupported_runtime_provider() -> None:
    service = _scan_service_with_runtime(
        {
            "ai_provider": "anthropic",
            "ai_model": "claude-3-5-sonnet",
            "ai_base_url": "",
            "ai_api_key_encrypted": encrypt_api_key("saved-key"),
        }
    )

    with pytest.raises(ExternalAIServiceError) as exc_info:
        await service._resolve_ai_client()

    assert exc_info.value.retryable is False
    assert exc_info.value.failure_kind == "configuration"
