from app.application.dto.scan_contracts import ScanSessionDetailResponse
from app.application.use_cases.scan.scan_mapper import map_session_detail
from app.domain.repositories.scan_repository import ScanSessionRepository


class GetSessionUseCase:
    def __init__(self, repository: ScanSessionRepository) -> None:
        self.repository = repository

    async def execute(self, session_id: str) -> ScanSessionDetailResponse | None:
        session = await self.repository.get_by_id(session_id)
        if session is None:
            return None
        return map_session_detail(session)
