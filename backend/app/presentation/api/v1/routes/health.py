from pathlib import Path

from fastapi import APIRouter, HTTPException, status

from app.core.config import get_settings
from app.infrastructure.database.mongo import ping_mongo
from app.infrastructure.queue.redis import ping_redis


router = APIRouter()


@router.get("/health/live")
async def liveness():
    return {"status": "ok"}


@router.get("/health/ready")
async def readiness():
    settings = get_settings()
    mongo_ready = await ping_mongo()
    redis_ready = await ping_redis()
    artifacts_ready = Path(settings.artifacts_dir).expanduser().resolve().exists()
    payload = {
        "status": "ready" if mongo_ready and artifacts_ready and redis_ready else "degraded",
        "checks": {
            "mongo": mongo_ready,
            "redis": redis_ready,
            "artifacts_dir": artifacts_ready,
            "queue_backend": settings.queue_backend,
        },
    }
    if mongo_ready and artifacts_ready and redis_ready:
        return payload
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=payload)


@router.get("/health")
async def healthcheck():
    return {"status": "ok"}
