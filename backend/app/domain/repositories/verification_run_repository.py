from abc import ABC, abstractmethod

from app.domain.entities.verification_run import VerificationRunEntity


class VerificationRunRepository(ABC):
    @abstractmethod
    async def create(self, run: VerificationRunEntity) -> VerificationRunEntity:
        raise NotImplementedError

    @abstractmethod
    async def delete_by_session(self, session_id: str) -> int:
        raise NotImplementedError

    @abstractmethod
    async def delete_all(self) -> int:
        raise NotImplementedError
