import sys
import unittest
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.application.use_cases.scan_mapper import map_session_detail
from app.domain.entities.scan import FindingEntity, ScanSessionEntity


class WorkflowContractEnrichmentTests(unittest.TestCase):
    def test_session_and_findings_include_workflow_and_decision_summaries(self):
        finding = FindingEntity(
            id="finding-1",
            severity="high",
            title="Dynamic query construction may allow injection",
            file="app/core/security/validator.py",
            line=40,
            line_end=40,
            category="SQL injection",
            confidence=84,
            summary="Dynamic SQL was detected.",
            impact="Injection may alter query semantics.",
            attack_input="POST /login",
            attack_execution="router -> validator -> query builder",
            attack_result="Authentication behavior may be bypassed.",
            audit_log=["validated"],
            explanation="Untrusted data reaches a dynamic SQL sink.",
            fix_suggestions=[],
            evidence="query = f\"SELECT * FROM users WHERE email = '{email}'\"",
            remediation_status="patch_generated",
            approval_status="pending",
            approval_history=[{"status": "pending", "note": "Pending review", "timestamp": "2026-04-13T00:00:00+00:00"}],
        )
        session = ScanSessionEntity(
            id="session-1",
            title="Scan backend",
            repo="backend",
            source_path=str(Path(__file__).resolve()),
            target_type="file",
            preset="balanced",
            scan_mode="deep",
            status="completed",
            progress=100,
            progress_message="Completed",
            current_phase="Reporting",
            elapsed_seconds=30,
            preview="done",
            findings=[finding],
            coverage_percent=100,
            reviewed_files_count=1,
            eligible_files_count=1,
            reviewed_blocks_count=1,
            total_blocks_count=1,
            traced_paths_count=1,
            total_paths_count=1,
        )

        detail = map_session_detail(session)

        self.assertIsNotNone(detail.session.workflow_summary)
        self.assertEqual(detail.session.workflow_summary["state"], "approval-control")
        self.assertEqual(detail.findings[0].approval_status, "pending")
        self.assertIsNotNone(detail.findings[0].decision_summary)
        self.assertEqual(detail.findings[0].decision_summary["policy_outcome"], "review-required")


if __name__ == "__main__":
    unittest.main()
