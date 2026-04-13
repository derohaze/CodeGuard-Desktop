from app.domain.repositories.scan_repository import ScanSessionRepository


class DeleteAllSessionsUseCase:
    def __init__(self, repository: ScanSessionRepository) -> None:
        self.repository = repository

    async def execute(self) -> int:
        return await self.repository.delete_all()
