from __future__ import annotations

from abc import ABC, abstractmethod
import httpx


class BaseProvider(ABC):
    """Abstract provider — each provider implements its own integration."""

    id: str
    name: str
    default_base_url: str | None = None
    docs_url: str | None = None

    @abstractmethod
    async def test_connection(self, *, api_key: str, base_url: str | None = None, model: str | None = None) -> dict:
        """Test API key by doing a minimal request. Returns {ok, message, latency_ms}."""
        raise NotImplementedError

    @abstractmethod
    async def list_models(self, *, api_key: str, base_url: str | None = None) -> list[dict]:
        """List available models. Returns [{id, name, created}]"""
        raise NotImplementedError

    def resolve_base_url(self, base_url: str | None) -> str:
        return (base_url or self.default_base_url or "").rstrip("/")

    async def _get(self, url: str, headers: dict, timeout: float = 15.0) -> httpx.Response:
        async with httpx.AsyncClient(timeout=timeout) as client:
            return await client.get(url, headers=headers)

    async def _post(self, url: str, headers: dict, json: dict, timeout: float = 15.0) -> httpx.Response:
        async with httpx.AsyncClient(timeout=timeout) as client:
            return await client.post(url, json=json, headers=headers)
