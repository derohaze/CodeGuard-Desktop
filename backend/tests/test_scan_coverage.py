import unittest
from pathlib import Path
import sys

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.domain.entities.scan import FindingEntity
from app.infrastructure.services.repository.repository_analysis import build_repository_artifacts, build_repository_profile, collect_files
from app.infrastructure.services.scan.scan_coverage import (
    build_coverage_snapshot,
    build_file_segments,
    build_segment_work_items,
    segment_file,
    score_with_coverage,
)


class ScanCoverageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "vulnerable_demo.py"
        self.source_root = self.fixture_path.parent
        self.files = collect_files(self.fixture_path, "file")
        self.profile = build_repository_profile(self.source_root, self.files)
        self.repository_artifacts = build_repository_artifacts(self.source_root, self.files, self.profile)
        self.file_segments = build_file_segments(self.files, self.source_root)

    def test_file_segmentation_covers_large_text_as_multiple_blocks(self):
        large_text = "\n".join(f"line {index}" for index in range(1, 261))
        blocks = segment_file("large_demo.py", large_text)
        self.assertGreater(len(blocks), 1)
        self.assertTrue(blocks[0]["snippet"])

    def test_segment_work_items_are_generated_from_blocks(self):
        large_text = "\n".join(f"line {index}" for index in range(1, 261))
        synthetic_segment = {
            "file": self.fixture_path.name,
            "line_count": 260,
            "block_count": len(segment_file(self.fixture_path.name, large_text)),
            "blocks": segment_file(self.fixture_path.name, large_text),
            "focuses": ["request flow"],
        }
        work_items = build_segment_work_items(
            files=self.files,
            source_root=self.source_root,
            repository_artifacts=self.repository_artifacts,
            repository_map={"priority_paths": [{"file": self.fixture_path.name, "attack_surface": "api", "review_focus": "security review"}]},
            file_segments=[synthetic_segment],
            target_type="file",
        )
        self.assertGreater(len(work_items), 1)
        self.assertIn("block_id", work_items[0])
        self.assertIn("start_line", work_items[0])

    def test_score_requires_high_coverage_for_perfect_safe_score(self):
        low_coverage = {
            "coverage_percent": 40,
            "reviewed_files_count": 1,
            "eligible_files_count": 5,
            "reviewed_blocks_count": 2,
            "total_blocks_count": 10,
            "reviewed_lines_count": 120,
            "total_lines_count": 900,
            "skipped_files_count": 4,
            "high_risk_files_count": 2,
            "coverage_summary": "partial",
        }
        self.assertLess(score_with_coverage([], low_coverage), 100)
        full_coverage = {**low_coverage, "coverage_percent": 95}
        self.assertEqual(score_with_coverage([], full_coverage), 100)

    def test_coverage_snapshot_reports_review_units(self):
        work_items = build_segment_work_items(
            files=self.files,
            source_root=self.source_root,
            repository_artifacts=self.repository_artifacts,
            repository_map={"priority_paths": [{"file": self.fixture_path.name, "attack_surface": "api", "review_focus": "security review"}]},
            file_segments=self.file_segments,
            target_type="file",
        )
        finding = FindingEntity(
            id="finding-1",
            severity="critical",
            title="Command injection",
            file=self.fixture_path.name,
            line=10,
            line_end=10,
            category="Command injection",
            confidence=91,
            summary="summary",
            impact="impact",
            attack_input="input",
            attack_execution="execution",
            attack_result="result",
            audit_log=["log"],
            explanation="explanation",
            fix_suggestions=[],
            evidence="snippet",
        )
        snapshot = build_coverage_snapshot(
            profile=self.profile,
            repository_artifacts=self.repository_artifacts,
            file_segments=self.file_segments,
            work_items=work_items,
            findings=[finding],
        )
        self.assertGreaterEqual(snapshot["coverage_percent"], 100)
        self.assertEqual(snapshot["confirmed_findings_count"], 1)

    def test_coverage_snapshot_treats_zero_block_files_as_excluded_not_gap(self):
        snapshot = build_coverage_snapshot(
            profile={"file_count": 2},
            repository_artifacts={"hotspot_files": []},
            file_segments=[
                {
                    "file": "main.py",
                    "line_count": 40,
                    "block_count": 1,
                    "blocks": [],
                    "focuses": [],
                },
                {
                    "file": "__init__.py",
                    "line_count": 0,
                    "block_count": 0,
                    "blocks": [],
                    "focuses": [],
                },
            ],
            work_items=[
                {
                    "file": "main.py",
                    "block_id": "main.py:1",
                    "start_line": "1",
                    "end_line": "40",
                }
            ],
            findings=[],
            scan_mode="deep",
            path_units=[],
        )

        self.assertEqual(snapshot["coverage_percent"], 100)
        self.assertEqual(snapshot["reviewed_files_count"], 2)
        self.assertEqual(snapshot["skipped_files_count"], 0)
        self.assertEqual(len(snapshot["excluded_files"]), 1)


if __name__ == "__main__":
    unittest.main()
