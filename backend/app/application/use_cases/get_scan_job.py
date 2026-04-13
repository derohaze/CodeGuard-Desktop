from app.domain.entities.scan_job import ScanJobEntity
from app.domain.repositories.scan_job_repository import ScanJobRepository


class GetScanJobUseCase:
    def __init__(self, repository: ScanJobRepository) -> None:
        self.repository = repository

    async def execute(self, job_id: str) -> ScanJobEntity | None:
        return await self.repository.get_by_id(job_id)
