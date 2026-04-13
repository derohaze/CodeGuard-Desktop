from __future__ import annotations

import asyncio
import time


class GroqKeyPool:
    def __init__(
        self,
        api_keys: list[str],
        *,
        cooldown_seconds: float = 8.0,
        failure_threshold: int = 2,
        quarantine_seconds: float = 45.0,
    ) -> None:
        if not api_keys:
            raise ValueError("GroqKeyPool requires at least one API key.")
        self._cooldown_seconds = cooldown_seconds
        self._failure_threshold = max(1, failure_threshold)
        self._quarantine_seconds = max(quarantine_seconds, cooldown_seconds)
        self._guard = asyncio.Lock()
        self._cursor = 0
        self._keys = [
            {
                "secret": key,
                "label": f"groq-key-{index + 1:02d}",
                "request_count": 0,
                "success_count": 0,
                "failure_count": 0,
                "failure_streak": 0,
                "cooldown_until": 0.0,
                "disabled_until": 0.0,
                "last_status": "idle",
            }
            for index, key in enumerate(api_keys)
        ]

    async def acquire_key(self) -> dict:
        async with self._guard:
            now = time.monotonic()
            count = len(self._keys)
            best = None
            shortest_wait = None

            for offset in range(count):
                index = (self._cursor + offset) % count
                key = self._keys[index]
                available_at = max(key["cooldown_until"], key["disabled_until"])
                remaining = available_at - now
                if remaining <= 0:
                    self._cursor = (index + 1) % count
                    key["request_count"] += 1
                    key["last_status"] = "in_use"
                    return {
                        "api_key": key["secret"],
                        "label": key["label"],
                    }
                if shortest_wait is None or remaining < shortest_wait:
                    best = key
                    shortest_wait = remaining

            return {
                "api_key": "",
                "label": best["label"] if best else "groq-key-unavailable",
                "retry_after_seconds": max(0.0, shortest_wait or self._cooldown_seconds),
            }

    async def mark_success(self, label: str, headers: dict[str, str] | None = None) -> None:
        async with self._guard:
            key = self._find(label)
            if key is None:
                return
            key["success_count"] += 1
            key["failure_streak"] = 0
            key["cooldown_until"] = 0.0
            key["disabled_until"] = 0.0
            key["last_status"] = "healthy"
            retry_after = _retry_after_seconds(headers)
            if retry_after > 0:
                key["cooldown_until"] = time.monotonic() + retry_after
                key["last_status"] = "cooldown"

    async def mark_rate_limited(self, label: str, headers: dict[str, str] | None = None) -> float:
        async with self._guard:
            key = self._find(label)
            if key is None:
                return self._cooldown_seconds
            cooldown = max(self._cooldown_seconds, _retry_after_seconds(headers))
            key["failure_count"] += 1
            key["failure_streak"] += 1
            key["cooldown_until"] = time.monotonic() + cooldown
            key["last_status"] = "rate_limited"
            return cooldown

    async def mark_failure(self, label: str, *, severe: bool = False) -> float:
        async with self._guard:
            key = self._find(label)
            if key is None:
                return self._cooldown_seconds
            key["failure_count"] += 1
            key["failure_streak"] += 1
            cooldown = self._cooldown_seconds * min(key["failure_streak"], 3)
            if severe or key["failure_streak"] >= self._failure_threshold:
                cooldown = max(cooldown, self._quarantine_seconds)
                key["disabled_until"] = time.monotonic() + cooldown
                key["last_status"] = "quarantined"
            else:
                key["cooldown_until"] = time.monotonic() + cooldown
                key["last_status"] = "cooldown"
            return cooldown

    async def snapshot(self) -> dict:
        async with self._guard:
            now = time.monotonic()
            return {
                "keys_total": len(self._keys),
                "healthy_keys": sum(1 for key in self._keys if max(key["cooldown_until"], key["disabled_until"]) <= now),
                "keys": [
                    {
                        "label": key["label"],
                        "request_count": key["request_count"],
                        "success_count": key["success_count"],
                        "failure_count": key["failure_count"],
                        "failure_streak": key["failure_streak"],
                        "cooldown_remaining_seconds": round(max(0.0, key["cooldown_until"] - now), 3),
                        "disabled_remaining_seconds": round(max(0.0, key["disabled_until"] - now), 3),
                        "last_status": key["last_status"],
                    }
                    for key in self._keys
                ],
            }

    def _find(self, label: str):
        for key in self._keys:
            if key["label"] == label:
                return key
        return None


def _retry_after_seconds(headers: dict[str, str] | None) -> float:
    if not headers:
        return 0.0
    retry_after = headers.get("retry-after") or headers.get("Retry-After")
    if not retry_after:
        return 0.0
    try:
        return max(0.0, float(retry_after))
    except (TypeError, ValueError):
        return 0.0
