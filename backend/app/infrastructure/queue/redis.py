import asyncio
from typing import Any

from app.core.config import get_settings


_redis_health_client: Any | None = None
_arq_pool: Any | None = None
_redis_lock = asyncio.Lock()


def _require_queue_runtime() -> tuple[Any, Any, Any]:
    try:
        from arq import create_pool
        from arq.connections import RedisSettings
        from redis.asyncio import Redis
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "QUEUE_BACKEND='arq' requires the optional queue dependencies. Install backend requirements in this Python environment."
        ) from exc
    return create_pool, RedisSettings, Redis


def _build_redis_settings() -> Any:
    _, redis_settings_type, _ = _require_queue_runtime()
    settings = get_settings()
    if not settings.redis_url:
        raise RuntimeError("REDIS_URL is required when QUEUE_BACKEND is set to 'arq'.")
    return redis_settings_type.from_dsn(settings.redis_url)


async def initialize_redis() -> Any | None:
    global _redis_health_client, _arq_pool
    settings = get_settings()
    if settings.queue_backend != "arq":
        return None

    create_pool, _, redis_client_type = _require_queue_runtime()

    async with _redis_lock:
        if _redis_health_client is None:
            _redis_health_client = redis_client_type.from_url(settings.redis_url)
        await _redis_health_client.ping()

        if _arq_pool is None:
            _arq_pool = await create_pool(
                _build_redis_settings(),
                default_queue_name=settings.scan_queue_name,
            )
        return _arq_pool


async def get_arq_pool() -> Any:
    pool = await initialize_redis()
    if pool is None:
        raise RuntimeError("ARQ pool is unavailable because QUEUE_BACKEND is not set to 'arq'.")
    return pool


async def ping_redis() -> bool:
    settings = get_settings()
    if settings.queue_backend != "arq":
        return True
    try:
        await initialize_redis()
        return True
    except Exception:
        return False


async def close_redis() -> None:
    global _redis_health_client, _arq_pool
    if _arq_pool is not None:
        await _arq_pool.aclose(close_connection_pool=True)
    if _redis_health_client is not None:
        await _redis_health_client.aclose()
    _arq_pool = None
    _redis_health_client = None
