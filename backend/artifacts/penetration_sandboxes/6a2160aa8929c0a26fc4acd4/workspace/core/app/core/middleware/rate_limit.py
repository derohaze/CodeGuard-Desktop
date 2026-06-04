from __future__ import annotations

import hashlib
import logging

from fastapi import Request

from core.app.core.config import get_settings
from core.app.core.errors import AppError
from core.app.core.request_context import extract_client_ip

logger = logging.getLogger("commerceops.rate_limit")

WINDOW_SECONDS = 60


def _resolve_scope(path: str, method: str) -> str:
    if path.startswith("/api/v1/integrations/woocommerce/webhooks/"):
        return "webhook"
    if path.startswith("/api/v1/integrations/shopify/webhooks/"):
        return "webhook"
    if path.startswith("/api/v1/auth"):
        return "auth"
    if path.startswith("/api/v1/account/password"):
        return "account_password"
    if path.startswith("/api/v1/team"):
        return "team"
    if path == "/api/v1/products/import":
        return "import"
    if path == "/api/v1/integrations/woocommerce/sync":
        return "sync"
    if path == "/api/v1/orders/bulk-delete-woocommerce":
        return "bulk_ops"
    if path.startswith("/api/v1/orders") and method in {"POST", "PUT", "PATCH", "DELETE"}:
        return "bulk_ops"
    if path.startswith("/api/v1/shipping"):
        return "shipping"
    return "api"


def _limit_for_scope(scope: str, settings: object) -> int:
    if scope == "auth":
        return settings.auth_rate_limit_requests_per_minute
    if scope == "account_password":
        return getattr(settings, "account_password_rate_limit_requests_per_minute", 30)
    if scope == "team":
        return getattr(settings, "team_rate_limit_requests_per_minute", 60)
    if scope == "import":
        return getattr(settings, "import_rate_limit_requests_per_minute", 5)
    if scope == "sync":
        return getattr(settings, "sync_rate_limit_requests_per_minute", 3)
    if scope == "bulk_ops":
        return getattr(settings, "bulk_ops_rate_limit_requests_per_minute", 30)
    if scope == "webhook":
        return getattr(settings, "webhook_rate_limit_requests_per_minute", 120)
    if scope == "shipping":
        return settings.rate_limit_requests_per_minute
    return settings.rate_limit_requests_per_minute


def _redis_key(prefix: str, client: str, scope: str) -> str:
    client_hash = hashlib.sha256(client.encode()).hexdigest()[:16]
    return f"{prefix}:rate_limit:{scope}:{client_hash}"


_FAIL_CLOSED_SCOPES = frozenset({"auth", "account_password", "bulk_ops", "import", "sync", "shipping", "webhook"})
# Webhooks intentionally fail closed when Redis is unavailable. Returning 503
# preserves rate-limit enforcement during outages and relies on upstream
# commerce platforms to retry delivery rather than accepting unmetered traffic.


async def check_rate_limit(request: Request) -> None:
    settings = get_settings()
    if not settings.rate_limit_enabled or settings.app_env == "test":
        return

    client = extract_client_ip(request) or "unknown"
    path = request.url.path
    method = request.method
    scope = _resolve_scope(path, method)
    limit = _limit_for_scope(scope, settings)

    try:
        from core.app.core.redis import get_redis_client

        redis = get_redis_client()
        key = _redis_key(settings.redis_key_prefix, client, scope)
        pipe = redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, WINDOW_SECONDS)
        count, _ = await pipe.execute()
        if count > limit:
            raise AppError("RATE_LIMITED", "Too many requests", 429)
    except AppError:
        raise
    except Exception:
        if scope in _FAIL_CLOSED_SCOPES:
            logger.error(
                "Rate limit check failed (Redis unavailable) for sensitive scope=%s; rejecting request",
                scope,
            )
            raise AppError(
                "SERVICE_UNAVAILABLE",
                "Security service temporarily unavailable",
                503,
            )
        logger.warning("Rate limit check failed (Redis unavailable); allowing request")
