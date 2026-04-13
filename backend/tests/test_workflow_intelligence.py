import asyncio
import sys
import unittest
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.application.use_cases.get_workflow_repo_hotspots import GetWorkflowRepoHotspotsUseCase
from app.application.use_cases.get_workflow_repo_intelligence_summary import GetWorkflowRepoIntelligenceSummaryUseCase
from app.application.use_cases.get_workflow_service_exposure_feed import GetWorkflowServiceExposureFeedUseCase
from app.application.use_cases.get_workflow_service_exposure_summary import GetWorkflowServiceExposureSummaryUseCase
from app.application.use_cases.get_workflow_team_posture_feed import GetWorkflowTeamPostureFeedUseCase
from app.application.use_cases.get_workflow_team_posture_summary import GetWorkflowTeamPostureSummaryUseCase
from app.domain.entities.scan import FindingEntity, ScanSessionEntity


class FakeRepository:
    def __init__(self, sessions):
        self.sessions = sessions

    async def list_recent(self, limit: int = 25):
        return self.sessions[:limit]

    async def list_recent_light(self, limit: int = 25):
        return self.sessions[:limit]


def build_session(*, repo: str, status: str = "completed", severity: str = "high", category: str = "Path traversal", coverage_percent: int = 80):
    finding = FindingEntity(
        id=f"{repo}-finding",
        severity=severity,
        title="Path issue",
        file=f"{repo}/service.py",
        line=16,
        line_end=16,
        category=category,
        confidence=82,
        summary="summary",
        impact="impact",
        attack_input="input",
        attack_execution="execution",
        attack_result="result",
        audit_log=["validated"],
        explanation="explanation",
        fix_suggestions=[],
        evidence="evidence",
        approval_status="pending" if status == "completed" else "not_required",
        remediation_status="patch_generated" if status == "completed" else "open",
    )
    return ScanSessionEntity(
        id=f"{repo}-session",
        title=repo,
        repo=repo,
        source_path=repo,
        target_type="folder",
        preset="balanced",
        scan_mode="deep",
        status=status,
        progress=100,
        progress_message="Completed" if status == "completed" else "Scanning",
        current_phase="Reporting",
        elapsed_seconds=25,
        preview="preview",
        findings=[finding],
        coverage_percent=coverage_percent,
        skipped_files_count=1 if coverage_percent < 100 else 0,
        security_score=70 if coverage_percent < 100 else 88,
        graph_summary={"external_surfaces": 2, "trust_boundaries": 2},
        segmentation_summary={"identity_surfaces": ["auth"]},
        security_registry={"auth_components": ["session"], "network_boundaries": ["api"], "data_sinks": ["db"], "user_inputs": ["request"]},
        repository_graph={"service_boundaries": ["svc"], "external_calls": ["http"], "public_entrypoints": ["route"]},
        path_summary={"candidate_path_count": 3},
        traced_paths_count=3,
        total_paths_count=3,
        candidate_findings=[],
    )


class WorkflowIntelligenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.sessions = [
            build_session(repo="backend-a"),
            build_session(repo="backend-b", severity="critical", coverage_percent=92),
            build_session(repo="backend-c", status="scanning", coverage_percent=100),
        ]
        self.repository = FakeRepository(self.sessions)

    def test_repo_intelligence_summary_and_feed(self):
        summary = asyncio.run(GetWorkflowRepoIntelligenceSummaryUseCase(self.repository).execute(limit=10))
        feed = asyncio.run(GetWorkflowRepoHotspotsUseCase(self.repository).execute(limit=10))
        self.assertGreaterEqual(summary["hotspot_count"], 1)
        self.assertTrue(feed["items"])
        self.assertIn("top_repositories", summary)

    def test_team_posture_summary_and_feed(self):
        summary = asyncio.run(GetWorkflowTeamPostureSummaryUseCase(self.repository).execute(limit=10))
        feed = asyncio.run(GetWorkflowTeamPostureFeedUseCase(self.repository).execute(limit=10))
        self.assertGreaterEqual(summary["hotspot_count"], 1)
        self.assertTrue(feed["items"])
        self.assertIn(feed["items"][0]["hotspot_class"], {"control-drag", "risk-drag", "coverage-drag", "throughput-drag"})

    def test_service_exposure_summary_and_feed(self):
        summary = asyncio.run(GetWorkflowServiceExposureSummaryUseCase(self.repository).execute(limit=10))
        feed = asyncio.run(GetWorkflowServiceExposureFeedUseCase(self.repository).execute(limit=10))
        self.assertGreaterEqual(summary["hotspot_count"], 1)
        self.assertTrue(feed["items"])
        self.assertIn(feed["items"][0]["hotspot_class"], {"boundary-drag", "network-drag", "path-drag", "entrypoint-drag"})


if __name__ == "__main__":
    unittest.main()
