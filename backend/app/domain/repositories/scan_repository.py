from abc import ABC, abstractmethod

from app.domain.entities.scan import ScanSessionEntity


class ScanSessionRepository(ABC):
    @abstractmethod
    async def create(self, session: ScanSessionEntity) -> ScanSessionEntity:
        raise NotImplementedError

    @abstractmethod
    async def update(self, session_id: str, updates: dict) -> ScanSessionEntity | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, session_id: str) -> ScanSessionEntity | None:
        raise NotImplementedError

    @abstractmethod
    async def list_recent(self, limit: int = 25) -> list[ScanSessionEntity]:
        raise NotImplementedError

    async def list_recent_light(self, limit: int = 25) -> list[ScanSessionEntity]:
        return await self.list_recent(limit=limit)

    @abstractmethod
    async def delete(self, session_id: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def delete_all(self) -> int:
        raise NotImplementedError
