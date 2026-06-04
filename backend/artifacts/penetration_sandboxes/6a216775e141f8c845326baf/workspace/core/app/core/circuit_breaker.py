from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from time import time as wall_time
from typing import Any, Callable

from core.app.core.config import get_settings
from core.app.core.redis import get_redis_client

logger = logging.getLogger("commerceops.circuit_breaker")

# circuit state constants
STATE_CLOSED = "closed"
STATE_OPEN = "open"
STATE_HALF_OPEN = "half_open"

# Lua script for atomic OPEN -> HALF_OPEN transition.
# Only one caller succeeds; resets half-open call counter.
_LUA_TRY_HALF_OPEN = """
local state_key = KEYS[1]
local opened_at_key = KEYS[2]
local half_open_calls_key = KEYS[3]
local current_state = redis.call('get', state_key)
if current_state == 'open' then
    redis.call('set', state_key, 'half_open')
    redis.call('set', half_open_calls_key, '0')
    return 1
end
return 0
"""


@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    recovery_timeout_seconds: int = 30
    half_open_max_calls: int = 1
    recovery_jitter_seconds: float = 5.0


class CircuitBreaker:
    """Redis-backed circuit breaker for external service calls.

    Tracks failures per service endpoint across all workers.
    Uses atomic Lua scripts for state transitions to prevent race conditions.
    """

    def __init__(self, name: str, config: CircuitBreakerConfig | None = None) -> None:
        self.name = name
        if config is None:
            config = CircuitBreakerConfig()
        self.config = config
        settings = get_settings()
        self._prefix = f"{settings.redis_key_prefix}:circuit:{name}"

    def _state_key(self) -> str:
        return f"{self._prefix}:state"

    def _failures_key(self) -> str:
        return f"{self._prefix}:failures"

    def _opened_at_key(self) -> str:
        return f"{self._prefix}:opened_at"

    def _half_open_calls_key(self) -> str:
        return f"{self._prefix}:half_open_calls"

    def _recovery_timeout_with_jitter(self) -> float:
        jitter = random.uniform(0, self.config.recovery_jitter_seconds)
        return self.config.recovery_timeout_seconds + jitter

    async def call(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Execute ``fn`` if circuit is closed or half-open."""
        state = await self._get_state()
        if state == STATE_OPEN:
            opened_at = await self._get_opened_at()
            if opened_at and (wall_time() - opened_at) >= self._recovery_timeout_with_jitter():
                transitioned = await self._try_transition_to_half_open()
                if transitioned:
                    logger.info("Circuit breaker %s moved to half-open (atomic)", self.name)
                else:
                    # Another worker already transitioned; re-read state
                    state = await self._get_state()
                    if state == STATE_OPEN:
                        logger.warning("Circuit breaker %s is OPEN; rejecting call", self.name)
                        raise CircuitBreakerOpenError(self.name)
            else:
                logger.warning("Circuit breaker %s is OPEN; rejecting call", self.name)
                raise CircuitBreakerOpenError(self.name)

        if state == STATE_HALF_OPEN:
            half_calls = await self._get_half_open_calls()
            if half_calls >= self.config.half_open_max_calls:
                logger.warning("Circuit breaker %s half-open quota exceeded", self.name)
                raise CircuitBreakerOpenError(self.name)
            await self._incr_half_open_calls()

        try:
            result = await fn(*args, **kwargs)
            await self._on_success()
            return result
        except Exception:
            await self._on_failure()
            raise

    async def _try_transition_to_half_open(self) -> bool:
        """Atomically transition OPEN -> HALF_OPEN. Returns True if this caller succeeded."""
        try:
            redis = get_redis_client()
            result = await redis.eval(
                _LUA_TRY_HALF_OPEN,
                3,
                self._state_key(),
                self._opened_at_key(),
                self._half_open_calls_key(),
            )
            return bool(result)
        except Exception:
            # If Redis is down, we can't coordinate. Default to allowing the call.
            return True

    async def _get_state(self) -> str:
        try:
            redis = get_redis_client()
            state = await redis.get(self._state_key())
            return state or STATE_CLOSED
        except Exception:
            return STATE_CLOSED

    async def _set_state(self, state: str) -> None:
        try:
            redis = get_redis_client()
            await redis.set(self._state_key(), state)
        except Exception:
            pass

    async def _get_opened_at(self) -> float | None:
        try:
            redis = get_redis_client()
            val = await redis.get(self._opened_at_key())
            return float(val) if val else None
        except Exception:
            return None

    async def _set_opened_at(self, timestamp: float) -> None:
        try:
            redis = get_redis_client()
            await redis.set(self._opened_at_key(), str(timestamp))
        except Exception:
            pass

    async def _get_half_open_calls(self) -> int:
        try:
            redis = get_redis_client()
            val = await redis.get(self._half_open_calls_key())
            return int(val) if val else 0
        except Exception:
            return 0

    async def _incr_half_open_calls(self) -> None:
        try:
            redis = get_redis_client()
            await redis.incr(self._half_open_calls_key())
        except Exception:
            pass

    async def _on_success(self) -> None:
        try:
            redis = get_redis_client()
            pipe = redis.pipeline()
            pipe.set(self._state_key(), STATE_CLOSED)
            pipe.delete(self._failures_key(), self._opened_at_key(), self._half_open_calls_key())
            await pipe.execute()
        except Exception:
            pass

    async def _on_failure(self) -> None:
        try:
            redis = get_redis_client()
            failures = await redis.incr(self._failures_key())
            if failures == 1:
                await redis.expire(self._failures_key(), self.config.recovery_timeout_seconds * 2)
            if failures >= self.config.failure_threshold:
                try:
                    redis = get_redis_client()
                    pipe = redis.pipeline()
                    pipe.set(self._state_key(), STATE_OPEN)
                    pipe.set(self._opened_at_key(), str(wall_time()))
                    await pipe.execute()
                except Exception:
                    pass
                logger.warning("Circuit breaker %s opened after %s failures", self.name, failures)
        except Exception:
            pass


class CircuitBreakerOpenError(Exception):
    def __init__(self, name: str) -> None:
        super().__init__(f"Circuit breaker '{name}' is OPEN")
        self.name = name
