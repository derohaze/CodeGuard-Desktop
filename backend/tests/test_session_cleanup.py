import asyncio
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.application.use_cases.session.delete_all_sessions import DeleteAllSessionsUseCase
from app.application.use_cases.session.delete_session import DeleteSessionUseCase


class FakeSessionRepository:
    def __init__(self) -> None:
        self.delete = AsyncMock(return_value=True)
        self.delete_all = AsyncMock(return_value=4)


class FakeWorkflowPersistence:
    def __init__(self) -> None:
        self.cleanup_session = AsyncMock()
        self.cleanup_all = AsyncMock()


class SessionCleanupTests(unittest.TestCase):
    def test_delete_session_cleans_side_collections(self):
        repository = FakeSessionRepository()
        persistence = FakeWorkflowPersistence()
        use_case = DeleteSessionUseCase(repository, persistence)

        deleted = asyncio.run(use_case.execute("session-1"))

        self.assertTrue(deleted)
        persistence.cleanup_session.assert_awaited_once_with("session-1")

    def test_delete_all_sessions_cleans_side_collections(self):
        repository = FakeSessionRepository()
        persistence = FakeWorkflowPersistence()
        use_case = DeleteAllSessionsUseCase(repository, persistence)

        deleted = asyncio.run(use_case.execute())

        self.assertEqual(deleted, 4)
        persistence.cleanup_all.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
