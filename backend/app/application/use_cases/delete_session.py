from app.domain.repositories.scan_repository import ScanSessionRepository
from app.infrastructure.services.workflow_persistence import WorkflowPersistenceService


class DeleteSessionUseCase:
    def __init__(self, repository: ScanSessionRepository, workflow_persistence: WorkflowPersistenceService | None = None) -> None:
        self.repository = repository
        self.workflow_persistence = workflow_persistence

    async def execute(self, session_id: str) -> bool:
        deleted = await self.repository.delete(session_id)
        if deleted and self.workflow_persistence is not None:
            await self.workflow_persistence.cleanup_session(session_id)
        return deleted
