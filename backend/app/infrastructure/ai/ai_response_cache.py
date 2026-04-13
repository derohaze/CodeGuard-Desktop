from __future__ import annotations

import asyncio
import json
import time
from hashlib import sha256


class AIResponseCache:
    def __init__(self, ttl_seconds: int = 900) -> None:
        self.ttl_seconds = ttl_seconds
        self._lock = asyncio.Lock()
        self._entries: dict[str, tuple[float, object]] = {}
        self._inflight: dict[str, asyncio.Event] = {}

    async def get(self, key_parts: object) -> object | None:
        key = self._hash(key_parts)
        now = time.time()
        async with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return None
            expires_at, value = entry
            if expires_at < now:
                self._entries.pop(key, None)
                return None
            return value

    async def set(self, key_parts: object, value: object) -> None:
        key = self._hash(key_parts)
        async with self._lock:
            self._entries[key] = (time.time() + self.ttl_seconds, value)

    async def get_or_compute(self, key_parts: object, compute):
        key = self._hash(key_parts)
        cached = await self.get(key_parts)
        if cached is not None:
            return cached, "hit"

        async with self._lock:
            existing = self._inflight.get(key)
            if existing is not None:
                waiter = existing
                owner = False
            else:
                waiter = asyncio.Event()
                self._inflight[key] = waiter
                owner = True

        if not owner:
            await asyncio.wait_for(waiter.wait(), timeout=30)
            cached = await self.get(key_parts)
            if cached is not None:
                return cached, "coalesced"
            return await compute(), "miss"

        try:
            value = await compute()
            await self.set(key_parts, value)
            return value, "miss"
        finally:
            async with self._lock:
                event = self._inflight.pop(key, None)
            if event is not None:
                event.set()

    def _hash(self, key_parts: object) -> str:
        serialized = json.dumps(key_parts, ensure_ascii=False, sort_keys=True, default=str, separators=(",", ":"))
        return sha256(serialized.encode("utf-8")).hexdigest()
