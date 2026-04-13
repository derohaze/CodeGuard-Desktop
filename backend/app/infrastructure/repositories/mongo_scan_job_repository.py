from bson import ObjectId

from app.domain.entities.scan_job import ScanJobEntity
from app.domain.repositories.scan_job_repository import ScanJobRepository
from app.infrastructure.database.collections import SCAN_JOBS_COLLECTION
from app.infrastructure.database.mongo import get_database


class MongoScanJobRepository(ScanJobRepository):
    def __init__(self) -> None:
        self.collection = get_database()[SCAN_JOBS_COLLECTION]

    async def create(self, job: ScanJobEntity) -> ScanJobEntity:
        await self.collection.insert_one(_entity_to_document(job))
        return job

    async def update(self, job_id: str, updates: dict) -> ScanJobEntity | None:
        await self.collection.update_one({"_id": ObjectId(job_id)}, {"$set": dict(updates)})
        return await self.get_by_id(job_id)

    async def get_by_id(self, job_id: str) -> ScanJobEntity | None:
        document = await self.collection.find_one({"_id": ObjectId(job_id)})
        if document is None:
            return None
        return _document_to_entity(document)

    async def list_by_session(self, session_id: str, limit: int = 25) -> list[ScanJobEntity]:
        cursor = self.collection.find({"session_id": session_id}).sort("created_at", -1).limit(limit)
        return [_document_to_entity(document) async for document in cursor]


def _entity_to_document(job: ScanJobEntity) -> dict:
    return {
        "_id": ObjectId(job.id),
        "job_id": job.id,
        "session_id": job.session_id,
        "type": job.job_type,
        "status": job.status,
        "stage": job.stage,
        "progress": job.progress,
        "attempts": job.attempts,
        "error_message": job.error_message,
        "created_at": job.created_at,
        "started_at": job.started_at,
        "finished_at": job.finished_at,
    }


def _document_to_entity(document: dict) -> ScanJobEntity:
    return ScanJobEntity(
        id=str(document["_id"]),
        session_id=document["session_id"],
        job_type=document.get("type", "scan"),
        status=document["status"],
        stage=document["stage"],
        progress=int(document.get("progress", 0)),
        attempts=int(document.get("attempts", 0)),
        error_message=document.get("error_message"),
        created_at=document["created_at"],
        started_at=document.get("started_at"),
        finished_at=document.get("finished_at"),
    )
