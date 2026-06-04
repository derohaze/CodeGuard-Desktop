from __future__ import annotations

import time

import httpx
import pytest

from app.core.exceptions import ExternalAIServiceError
import app.infrastructure.ai.nvidia_security_client as nvidia_client_module
from app.infrastructure.ai.nvidia_security_client import (
    NvidiaSecurityClient,
    _ProviderTarget,
    _map_provider_http_error,
    _should_wait_for_rate_limit_cooldown,
)


def test_rate_limit_error_preserves_retry_after_seconds() -> None:
    response = httpx.Response(
        429,
        headers={"Retry-After": "12"},
        json={"error": {"message": "quota exceeded"}},
        request=httpx.Request("POST", "https://integrate.api.nvidia.com/v1/chat/completions"),
    )

    error = _map_provider_http_error("nvidia", response)

    assert error.failure_kind == "rate_limit"
    assert error.retryable is True
    assert error.status_code == 429
    assert error.retry_after_seconds == 12


def test_rate_limit_cooldown_short_circuits_later_scan_requests(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(nvidia_client_module, "_PROVIDER_RATE_LIMIT_COOLDOWN_UNTIL", 0.0)
    monkeypatch.setattr(nvidia_client_module, "_PROVIDER_RATE_LIMIT_COOLDOWN_UNTIL_BY_KEY", {})
    client = object.__new__(NvidiaSecurityClient)
    client._runtime_events = []
    client._runtime_metrics = {}
    api_key = "test-key"

    client._record_rate_limit_if_needed(
        ExternalAIServiceError(
            "rate limited",
            provider="nvidia",
            retryable=True,
            status_code=429,
            failure_kind="rate_limit",
            retry_after_seconds=10,
        ),
        api_key=api_key,
    )

    target = _ProviderTarget(
        provider_name="nvidia",
        base_url="https://integrate.api.nvidia.com/v1",
        api_keys=(api_key,),
        timeout_seconds=30.0,
        model="test-model",
    )

    with pytest.raises(ExternalAIServiceError) as exc_info:
        client._raise_if_rate_limited(target)

    assert exc_info.value.failure_kind == "rate_limit"
    assert exc_info.value.status_code == 429
    assert client.snapshot_runtime_metrics()["rate_limit_short_circuits"] == 1


def test_key_specific_rate_limit_keeps_second_key_available(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(nvidia_client_module, "_PROVIDER_RATE_LIMIT_COOLDOWN_UNTIL", 0.0)
    monkeypatch.setattr(nvidia_client_module, "_PROVIDER_RATE_LIMIT_COOLDOWN_UNTIL_BY_KEY", {})
    client = object.__new__(NvidiaSecurityClient)
    client._runtime_events = []
    client._runtime_metrics = {}
    limited_key = "test-key-a"
    available_key = "test-key-b"
    target = _ProviderTarget(
        provider_name="nvidia",
        base_url="https://integrate.api.nvidia.com/v1",
        api_keys=(limited_key, available_key),
        timeout_seconds=30.0,
        model="test-model",
    )

    client._record_rate_limit_if_needed(
        ExternalAIServiceError(
            "rate limited",
            provider="nvidia",
            retryable=True,
            status_code=429,
            failure_kind="rate_limit",
            retry_after_seconds=10,
        ),
        api_key=limited_key,
    )

    with pytest.raises(ExternalAIServiceError):
        client._raise_if_rate_limited(target, api_key=limited_key)

    client._raise_if_rate_limited(target, api_key=available_key)
    client._raise_if_rate_limited(target)


def test_remediation_tasks_are_allowed_to_wait_for_cooldown() -> None:
    assert _should_wait_for_rate_limit_cooldown("explain")
    assert _should_wait_for_rate_limit_cooldown("fix_draft")
    assert _should_wait_for_rate_limit_cooldown("fix_validate_json_repair")
    assert not _should_wait_for_rate_limit_cooldown("repository_map")
    assert not _should_wait_for_rate_limit_cooldown("path_review")


@pytest.mark.asyncio
async def test_remediation_cooldown_wait_does_not_short_circuit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(nvidia_client_module, "_PROVIDER_RATE_LIMIT_COOLDOWN_UNTIL", 0.0)
    monkeypatch.setattr(nvidia_client_module, "_PROVIDER_RATE_LIMIT_COOLDOWN_UNTIL_BY_KEY", {})
    client = object.__new__(NvidiaSecurityClient)
    client._runtime_events = []
    client._runtime_metrics = {}
    api_key = "test-key"
    target = _ProviderTarget(
        provider_name="nvidia",
        base_url="https://integrate.api.nvidia.com/v1",
        api_keys=(api_key,),
        timeout_seconds=30.0,
        model="test-model",
    )
    sleep_calls: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        sleep_calls.append(seconds)
        nvidia_client_module._PROVIDER_RATE_LIMIT_COOLDOWN_UNTIL_BY_KEY[api_key] = time.monotonic() - 1

    nvidia_client_module._PROVIDER_RATE_LIMIT_COOLDOWN_UNTIL_BY_KEY[api_key] = time.monotonic() + 10
    monkeypatch.setattr(nvidia_client_module.asyncio, "sleep", fake_sleep)

    await client._wait_for_rate_limit_cooldown(target, task_name="fix_draft", api_key=api_key)

    assert sleep_calls
    assert 0 < sleep_calls[0] <= 10
    assert client.snapshot_runtime_metrics()["rate_limit_waits"] == 1
