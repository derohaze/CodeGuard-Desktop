from bson import ObjectId

from app.application.dto.scan_contracts import StartScanRequest
from app.domain.entities.scan_job import ScanJobEntity, build_scan_job_snapshot
from app.domain.entities.scan import ScanSessionEntity
from app.domain.repositories.scan_job_repository import ScanJobRepository
from app.domain.repositories.scan_repository import ScanSessionRepository
from app.infrastructure.services.scan_execution_service import create_initial_session
from app.infrastructure.services.workflow_persistence import WorkflowPersistenceService


class StartScanUseCase:
    def __init__(
        self,
        repository: ScanSessionRepository,
        job_repository: ScanJobRepository,
        workflow_persistence: WorkflowPersistenceService | None = None,
    ) -> None:
        self.repository = repository
        self.job_repository = job_repository
        self.workflow_persistence = workflow_persistence

    async def execute(self, request: StartScanRequest) -> tuple[ScanSessionEntity, ScanJobEntity]:
        session = create_initial_session(
            source_path=request.source_path,
            target_type=request.target_type,
            preset=request.preset,
            scan_mode=request.scan_mode,
        )
        job = ScanJobEntity(
            id=str(ObjectId()),
            session_id=session.id,
            status="queued",
            stage="queued",
            progress=0,
            attempts=0,
        )
        session.latest_scan_job = build_scan_job_snapshot(job)
        created_session = await self.repository.create(session)
        created_job = await self.job_repository.create(job)
        if self.workflow_persistence is not None:
            await self.workflow_persistence.record_audit(
                session_id=created_session.id,
                entity_type="scan_job",
                entity_id=created_job.id,
                action="scan.queued",
                payload={
                    "repo": created_session.repo,
                    "target_type": created_session.target_type,
                    "scan_mode": created_session.scan_mode,
                },
            )
        return created_session, created_job
