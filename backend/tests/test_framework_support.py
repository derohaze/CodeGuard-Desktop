import sys
import unittest
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.infrastructure.services.scan.score_calibration import build_support_matrix


class FrameworkSupportTests(unittest.TestCase):
    def test_python_language_without_framework_markers_uses_python_support_profile(self):
        support = build_support_matrix(
            {
                "primary_framework": "unknown",
                "frameworks": [],
                "languages": ["python"],
            }
        )

        self.assertEqual(support["primary"]["stack"], "python")
        self.assertEqual(support["primary"]["confidence"], "medium")

    def test_typescript_language_without_framework_markers_uses_node_support_profile(self):
        support = build_support_matrix(
            {
                "primary_framework": "unknown",
                "frameworks": [],
                "languages": ["typescript"],
            }
        )

        self.assertEqual(support["primary"]["stack"], "node_ts")
        self.assertEqual(support["primary"]["confidence"], "high")


if __name__ == "__main__":
    unittest.main()
