import sys
import unittest
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.infrastructure.services.scan.coverage_calculation import build_progress_state


class ProgressStateTests(unittest.TestCase):
    def test_repository_mapping_progress_blends_artifacts_and_ai_summary(self):
        progress = build_progress_state(
            "Repository mapping",
            {
                "mapping_artifacts_ready": 6,
                "mapping_artifacts_total": 6,
                "mapping_ai_steps_completed": 0,
                "mapping_ai_steps_total": 1,
            },
        )
        self.assertEqual(progress["phase_progress"], 65)
        self.assertEqual(progress["progress"], 23)

    def test_review_progress_depends_on_real_work_units(self):
        progress = build_progress_state(
            "Reviewing paths",
            {
                "blocks_reviewed": 0,
                "blocks_total": 100,
                "paths_reviewed": 0,
                "paths_total": 20,
                "review_batches_completed": 0,
                "review_batches_total": 5,
            },
        )
        self.assertEqual(progress["phase_progress"], 0)
        self.assertEqual(progress["progress"], 50)

    def test_review_progress_uses_batch_completion(self):
        progress = build_progress_state(
            "Reviewing paths",
            {
                "blocks_reviewed": 50,
                "blocks_total": 100,
                "paths_reviewed": 8,
                "paths_total": 16,
                "review_batches_completed": 2,
                "review_batches_total": 4,
            },
        )
        self.assertEqual(progress["phase_progress"], 50)
        self.assertEqual(progress["progress"], 68)

    def test_validation_progress_reaches_expected_weighted_value(self):
        progress = build_progress_state(
            "Validation",
            {
                "candidates_validated": 5,
                "candidates_total": 10,
                "validation_artifacts_ready": 1,
                "validation_artifacts_total": 2,
            },
        )
        self.assertEqual(progress["phase_progress"], 50)
        self.assertEqual(progress["progress"], 90)

    def test_completed_and_failed_states_are_terminal(self):
        self.assertEqual(build_progress_state("Completed")["progress"], 100)
        self.assertEqual(build_progress_state("Failed")["phase_progress"], 100)


if __name__ == "__main__":
    unittest.main()
