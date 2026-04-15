from bson import ObjectId

from app.domain.entities.audit_event import AuditEventEntity
from app.domain.entities.verification_run import VerificationRunEntity
from app.domain.repositories.audit_event_repository import AuditEventRepository
from app.domain.repositories.verification_run_repository import VerificationRunRepository


class WorkflowPersistenceService:
    def __init__(
        self,
        audit_events: AuditEventRepository,
        verification_runs: VerificationRunRepository,
    ) -> None:
        self.audit_events = audit_events
        self.verification_runs = verification_runs

    async def record_audit(
        self,
        *,
        entity_type: str,
        entity_id: str,
        action: str,
        payload: dict,
        session_id: str | None = None,
    ) -> AuditEventEntity:
        event = AuditEventEntity(
            id=str(ObjectId()),
            session_id=session_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            payload=payload,
        )
        return await self.audit_events.append(event)

    async def record_verification(
        self,
        *,
        session_id: str,
        finding_id: str,
        fix_id: str,
        status: str,
        checks: list[str],
        payload: dict,
        logs_ref: str | None = None,
    ) -> VerificationRunEntity:
        run = VerificationRunEntity(
            id=str(ObjectId()),
            session_id=session_id,
            finding_id=finding_id,
            fix_id=fix_id,
            status=status,
            checks=checks,
            logs_ref=logs_ref,
            payload=payload,
        )
        return await self.verification_runs.create(run)

    async def cleanup_session(self, session_id: str) -> None:
        await self.audit_events.delete_by_session(session_id)
        await self.verification_runs.delete_by_session(session_id)

    async def cleanup_all(self) -> None:
        await self.audit_events.delete_all()
        await self.verification_runs.delete_all()
