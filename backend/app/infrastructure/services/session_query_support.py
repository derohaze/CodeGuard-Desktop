from __future__ import annotations

from app.domain.entities.scan import ScanSessionEntity
from app.domain.repositories.scan_repository import ScanSessionRepository


async def list_recent_analysis_sessions(repository: ScanSessionRepository, limit: int = 25) -> list[ScanSessionEntity]:
    if hasattr(repository, "list_recent_light"):
        return await repository.list_recent_light(limit=limit)
    return await repository.list_recent(limit=limit)
