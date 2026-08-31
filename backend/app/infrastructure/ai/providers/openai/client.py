from __future__ import annotations

import time

import httpx

from app.infrastructure.ai.providers.base import BaseProvider


class OpenAIProvider(BaseProvider):
    id = "openai"
    name = "OpenAI"
    default_base_url = "https://api.openai.com/v1"
    docs_url = "https://platform.openai.com/docs"

    async def list_models(self, *, api_key: str, base_url: str | None = None) -> list[dict]:
        url = f"{self.resolve_base_url(base_url)}/models"
        headers = {"Authorization": f"Bearer {api_key}"}
        resp = await self._get(url, headers)
        resp.raise_for_status()
        data = resp.json()
        models = data.get("data", []) if isinstance(data, dict) else []
        result: list[dict] = []
        for m in models:
            if isinstance(m, dict) and m.get("id"):
                result.append({"id": m["id"], "name": m["id"], "created": m.get("created")})
        # Sort: gpt-4, gpt-3.5 first
        result.sort(key=lambda x: (0 if "gpt-4" in x["id"] else 1 if "gpt-3" in x["id"] else 2, x["id"]))
        return result[:100]

    async def test_connection(self, *, api_key: str, base_url: str | None = None, model: str | None = None) -> dict:
        # Try list models first (cheaper), fallback to chat ping
        start = time.monotonic()
        try:
            models = await self.list_models(api_key=api_key, base_url=base_url)
            latency = int((time.monotonic() - start) * 1000)
            if models:
                return {"ok": True, "message": f"Connected — {len(models)} models available", "latency_ms": latency, "models": models[:5]}
            # No models but auth ok, try chat
        except httpx.HTTPStatusError as e:
            if e.response.status_code not in (404, 405):
                # For 401/403, fail fast
                body = e.response.text[:300]
                return {"ok": False, "message": f"Auth failed ({e.response.status_code}): {body[:120]}", "latency_ms": int((time.monotonic() - start)*1000)}
            # Fall through to chat test for providers without /models
        except Exception as e:
            # Try chat as fallback
            pass

        # Chat ping fallback
        test_model = model or "gpt-4o-mini"
        url = f"{self.resolve_base_url(base_url)}/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": test_model,
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 1,
            "temperature": 0,
        }
        try:
            start2 = time.monotonic()
            resp = await self._post(url, headers, payload, timeout=20.0)
            resp.raise_for_status()
            latency = int((time.monotonic() - start2) * 1000)
            return {"ok": True, "message": f"Connected — chat ping ok ({test_model})", "latency_ms": latency}
        except httpx.HTTPStatusError as e:
            body = e.response.text[:300]
            return {"ok": False, "message": f"Chat ping failed ({e.response.status_code}): {body[:150]}", "latency_ms": int((time.monotonic() - start)*1000)}
        except Exception as e:
            return {"ok": False, "message": f"Connection failed: {str(e)[:150]}", "latency_ms": int((time.monotonic() - start)*1000)}
