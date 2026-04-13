from app.application.dto.scan_contracts import StartScanRequest
from app.domain.entities.scan import ScanSessionEntity
from app.domain.repositories.scan_repository import ScanSessionRepository
from app.infrastructure.services.scan_execution_service import create_initial_session


class StartScanUseCase:
    def __init__(self, repository: ScanSessionRepository) -> None:
        self.repository = repository

    async def execute(self, request: StartScanRequest) -> ScanSessionEntity:
        session = create_initial_session(
            source_path=request.source_path,
            target_type=request.target_type,
            preset=request.preset,
            scan_mode=request.scan_mode,
        )
        return await self.repository.create(session)
