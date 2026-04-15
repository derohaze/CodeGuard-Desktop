from app.domain.repositories.scan_repository import ScanSessionRepository
from app.infrastructure.services.workflow.workflow_persistence import WorkflowPersistenceService


class DeleteAllSessionsUseCase:
    def __init__(self, repository: ScanSessionRepository, workflow_persistence: WorkflowPersistenceService | None = None) -> None:
        self.repository = repository
        self.workflow_persistence = workflow_persistence

    async def execute(self) -> int:
        deleted = await self.repository.delete_all()
        if self.workflow_persistence is not None:
            await self.workflow_persistence.cleanup_all()
        return deleted
