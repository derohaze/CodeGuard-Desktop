from __future__ import annotations

import asyncio
import time


class ProviderScheduler:
    def __init__(
        self,
        concurrency_limit: int = 2,
        cooldown_seconds: float = 8.0,
        *,
        failure_threshold: int = 2,
        quarantine_seconds: float = 30.0,
    ) -> None:
        self._concurrency_limit = max(1, concurrency_limit)
        self._cooldown_seconds = cooldown_seconds
        self._failure_threshold = max(1, failure_threshold)
        self._quarantine_seconds = max(quarantine_seconds, cooldown_seconds)
        self._locks: dict[str, asyncio.Semaphore] = {}
        self._cooldowns: dict[str, float] = {}
        self._failure_streaks: dict[str, int] = {}
        self._guard = asyncio.Lock()

    async def run(self, provider_name: str, callback):
        semaphore = await self._get_semaphore(provider_name)
        await self._wait_for_cooldown(provider_name)
        async with semaphore:
            return await callback()

    async def mark_failure(self, provider_name: str) -> float:
        async with self._guard:
            streak = self._failure_streaks.get(provider_name, 0) + 1
            self._failure_streaks[provider_name] = streak
            cooldown = self._cooldown_seconds * min(streak, 3)
            if streak >= self._failure_threshold:
                cooldown = max(cooldown, self._quarantine_seconds)
            until = time.monotonic() + cooldown
            self._cooldowns[provider_name] = until
            return cooldown

    async def mark_success(self, provider_name: str) -> None:
        async with self._guard:
            self._failure_streaks[provider_name] = 0
            self._cooldowns.pop(provider_name, None)

    async def availability(self, provider_name: str) -> tuple[bool, float]:
        async with self._guard:
            until = self._cooldowns.get(provider_name, 0.0)
        remaining = until - time.monotonic()
        return remaining <= 0, max(0.0, remaining)

    async def snapshot(self) -> dict:
        async with self._guard:
            streaks = dict(self._failure_streaks)
            cooldowns = {
                provider: max(0.0, until - time.monotonic())
                for provider, until in self._cooldowns.items()
            }
        return {
            "failure_streaks": streaks,
            "cooldowns": cooldowns,
        }

    async def _wait_for_cooldown(self, provider_name: str) -> None:
        while True:
            async with self._guard:
                until = self._cooldowns.get(provider_name, 0.0)
            remaining = until - time.monotonic()
            if remaining <= 0:
                return
            await asyncio.sleep(min(remaining, 0.25))

    async def _get_semaphore(self, provider_name: str) -> asyncio.Semaphore:
        async with self._guard:
            if provider_name not in self._locks:
                self._locks[provider_name] = asyncio.Semaphore(self._concurrency_limit)
            return self._locks[provider_name]
