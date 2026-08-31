from __future__ import annotations

import time

import httpx

from app.infrastructure.ai.providers.base import BaseProvider


class AnthropicProvider(BaseProvider):
    id = "anthropic"
    name = "Anthropic"
    default_base_url = "https://api.anthropic.com/v1"
    docs_url = "https://docs.anthropic.com"

    async def list_models(self, *, api_key: str, base_url: str | None = None) -> list[dict]:
        url = f"{self.resolve_base_url(base_url)}/models"
        headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01"}
        resp = await self._get(url, headers)
        resp.raise_for_status()
        data = resp.json()
        models = data.get("data", []) if isinstance(data, dict) else []
        result: list[dict] = []
        for m in models:
            if isinstance(m, dict) and m.get("id"):
                result.append({"id": m["id"], "name": m.get("display_name") or m["id"], "created": m.get("created_at")})
        result.sort(key=lambda x: x["id"])
        return result[:100]

    async def test_connection(self, *, api_key: str, base_url: str | None = None, model: str | None = None) -> dict:
        start = time.monotonic()
        try:
            models = await self.list_models(api_key=api_key, base_url=base_url)
            latency = int((time.monotonic() - start) * 1000)
            if models:
                return {"ok": True, "message": f"Connected — {len(models)} models available", "latency_ms": latency, "models": models[:5]}
        except httpx.HTTPStatusError as e:
            body = e.response.text[:300]
            if e.response.status_code in (401, 403):
                return {"ok": False, "message": f"Auth failed ({e.response.status_code}): {body[:120]}", "latency_ms": int((time.monotonic() - start)*1000)}
        except Exception:
            pass

        # Fallback: try messages ping
        test_model = model or "claude-3-5-sonnet-20241022"
        url = f"{self.resolve_base_url(base_url)}/messages"
        headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"}
        payload = {"model": test_model, "max_tokens": 1, "messages": [{"role": "user", "content": "ping"}]}
        try:
            start2 = time.monotonic()
            resp = await self._post(url, headers, payload, timeout=20.0)
            resp.raise_for_status()
            latency = int((time.monotonic() - start2) * 1000)
            return {"ok": True, "message": f"Connected — messages ping ok ({test_model})", "latency_ms": latency}
        except httpx.HTTPStatusError as e:
            body = e.response.text[:300]
            return {"ok": False, "message": f"Messages ping failed ({e.response.status_code}): {body[:150]}", "latency_ms": int((time.monotonic() - start)*1000)}
        except Exception as e:
            return {"ok": False, "message": f"Connection failed: {str(e)[:150]}", "latency_ms": int((time.monotonic() - start)*1000)}
