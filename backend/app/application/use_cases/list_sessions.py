from app.application.dto.scan_contracts import SessionSummaryResponse
from app.application.use_cases.scan_mapper import map_session_summary
from app.domain.repositories.scan_repository import ScanSessionRepository


class ListSessionsUseCase:
    def __init__(self, repository: ScanSessionRepository) -> None:
        self.repository = repository

    async def execute(self) -> list[SessionSummaryResponse]:
        sessions = await self.repository.list_recent()
        return [map_session_summary(session) for session in sessions]
