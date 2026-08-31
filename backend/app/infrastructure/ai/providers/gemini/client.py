from __future__ import annotations

import time

import httpx

from app.infrastructure.ai.providers.base import BaseProvider


class GeminiProvider(BaseProvider):
    id = "gemini"
    name = "Gemini"
    default_base_url = "https://generativelanguage.googleapis.com/v1beta"
    docs_url = "https://ai.google.dev/gemini-api/docs"

    async def list_models(self, *, api_key: str, base_url: str | None = None) -> list[dict]:
        base = self.resolve_base_url(base_url)
        url = f"{base}/models?key={api_key}"
        resp = await self._get(url, {})
        resp.raise_for_status()
        data = resp.json()
        models = data.get("models", []) if isinstance(data, dict) else []
        result: list[dict] = []
        for m in models:
            if isinstance(m, dict) and m.get("name"):
                # name is like models/gemini-1.5-pro
                full = m["name"]
                short = full.split("/")[-1] if "/" in full else full
                result.append({"id": short, "name": m.get("displayName") or short, "created": None})
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

        # Fallback generateContent ping
        test_model = model or "gemini-1.5-flash"
        base = self.resolve_base_url(base_url)
        url = f"{base}/models/{test_model}:generateContent?key={api_key}"
        payload = {"contents": [{"parts": [{"text": "ping"}]}]}
        headers = {"Content-Type": "application/json"}
        try:
            start2 = time.monotonic()
            resp = await self._post(url, headers, payload, timeout=20.0)
            resp.raise_for_status()
            latency = int((time.monotonic() - start2) * 1000)
            return {"ok": True, "message": f"Connected — generateContent ping ok ({test_model})", "latency_ms": latency}
        except httpx.HTTPStatusError as e:
            body = e.response.text[:300]
            return {"ok": False, "message": f"Generate ping failed ({e.response.status_code}): {body[:150]}", "latency_ms": int((time.monotonic() - start)*1000)}
        except Exception as e:
            return {"ok": False, "message": f"Connection failed: {str(e)[:150]}", "latency_ms": int((time.monotonic() - start)*1000)}
