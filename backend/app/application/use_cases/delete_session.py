from app.domain.repositories.scan_repository import ScanSessionRepository


class DeleteSessionUseCase:
    def __init__(self, repository: ScanSessionRepository) -> None:
        self.repository = repository

    async def execute(self, session_id: str) -> bool:
        return await self.repository.delete(session_id)
