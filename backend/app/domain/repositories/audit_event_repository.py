from abc import ABC, abstractmethod

from app.domain.entities.audit_event import AuditEventEntity


class AuditEventRepository(ABC):
    @abstractmethod
    async def append(self, event: AuditEventEntity) -> AuditEventEntity:
        raise NotImplementedError

    @abstractmethod
    async def delete_by_session(self, session_id: str) -> int:
        raise NotImplementedError

    @abstractmethod
    async def delete_all(self) -> int:
        raise NotImplementedError
