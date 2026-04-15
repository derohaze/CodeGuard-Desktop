import asyncio
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.infrastructure.services.workflow.workflow_persistence import WorkflowPersistenceService


class FakeAuditRepository:
    def __init__(self) -> None:
        self.append = AsyncMock()
        self.delete_by_session = AsyncMock(return_value=1)
        self.delete_all = AsyncMock(return_value=3)


class FakeVerificationRepository:
    def __init__(self) -> None:
        self.create = AsyncMock()
        self.delete_by_session = AsyncMock(return_value=1)
        self.delete_all = AsyncMock(return_value=2)


class WorkflowPersistenceTests(unittest.TestCase):
    def test_record_audit_appends_event(self):
        audit_repo = FakeAuditRepository()
        verification_repo = FakeVerificationRepository()
        service = WorkflowPersistenceService(audit_repo, verification_repo)

        asyncio.run(
            service.record_audit(
                session_id="session-1",
                entity_type="finding",
                entity_id="finding-1",
                action="remediation.explained",
                payload={"summary": "x"},
            )
        )

        audit_repo.append.assert_awaited_once()
        appended = audit_repo.append.await_args.args[0]
        self.assertEqual(appended.session_id, "session-1")
        self.assertEqual(appended.action, "remediation.explained")

    def test_record_verification_creates_run(self):
        audit_repo = FakeAuditRepository()
        verification_repo = FakeVerificationRepository()
        service = WorkflowPersistenceService(audit_repo, verification_repo)

        asyncio.run(
            service.record_verification(
                session_id="session-1",
                finding_id="finding-1",
                fix_id="fix-1",
                status="verified",
                checks=["ok"],
                payload={"file": "app.py"},
            )
        )

        verification_repo.create.assert_awaited_once()
        created = verification_repo.create.await_args.args[0]
        self.assertEqual(created.session_id, "session-1")
        self.assertEqual(created.status, "verified")


if __name__ == "__main__":
    unittest.main()
