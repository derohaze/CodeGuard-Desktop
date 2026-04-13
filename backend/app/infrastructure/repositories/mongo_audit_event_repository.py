from bson import ObjectId

from app.domain.entities.audit_event import AuditEventEntity
from app.domain.repositories.audit_event_repository import AuditEventRepository
from app.infrastructure.database.collections import AUDIT_EVENTS_COLLECTION
from app.infrastructure.database.mongo import get_database


class MongoAuditEventRepository(AuditEventRepository):
    def __init__(self) -> None:
        self.collection = get_database()[AUDIT_EVENTS_COLLECTION]

    async def append(self, event: AuditEventEntity) -> AuditEventEntity:
        await self.collection.insert_one(
            {
                "_id": ObjectId(event.id),
                "event_id": event.id,
                "session_id": event.session_id,
                "entity_type": event.entity_type,
                "entity_id": event.entity_id,
                "action": event.action,
                "payload": event.payload,
                "created_at": event.created_at,
            }
        )
        return event

    async def delete_by_session(self, session_id: str) -> int:
        result = await self.collection.delete_many({"session_id": session_id})
        return int(result.deleted_count)

    async def delete_all(self) -> int:
        result = await self.collection.delete_many({})
        return int(result.deleted_count)
