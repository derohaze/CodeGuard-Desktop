from bson import ObjectId

from app.domain.entities.verification_run import VerificationRunEntity
from app.domain.repositories.verification_run_repository import VerificationRunRepository
from app.infrastructure.database.collections import VERIFICATION_RUNS_COLLECTION
from app.infrastructure.database.mongo import get_database


class MongoVerificationRunRepository(VerificationRunRepository):
    def __init__(self) -> None:
        self.collection = get_database()[VERIFICATION_RUNS_COLLECTION]

    async def create(self, run: VerificationRunEntity) -> VerificationRunEntity:
        await self.collection.insert_one(
            {
                "_id": ObjectId(run.id),
                "verification_id": run.id,
                "session_id": run.session_id,
                "finding_id": run.finding_id,
                "fix_id": run.fix_id,
                "status": run.status,
                "checks": run.checks,
                "logs_ref": run.logs_ref,
                "payload": run.payload,
                "created_at": run.created_at,
            }
        )
        return run

    async def delete_by_session(self, session_id: str) -> int:
        result = await self.collection.delete_many({"session_id": session_id})
        return int(result.deleted_count)

    async def delete_all(self) -> int:
        result = await self.collection.delete_many({})
        return int(result.deleted_count)
