from pathlib import Path
import sys
import tempfile
import unittest


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.infrastructure.services.scan_execution_service import build_candidate_review_findings


class ScanExecutionHelperTests(unittest.TestCase):
    def test_candidate_review_omits_items_promoted_to_validated(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            sample = root / "router.py"
            sample.write_text("query = request.args.get('q')\nrun(query)\n", encoding="utf-8")

            validated_findings = [
                {
                    "file": "router.py",
                    "line": 1,
                    "line_end": 2,
                    "title": "Dynamic query construction may allow injection",
                    "category": "SQL injection",
                    "path_hint": "request.args -> run(query)",
                    "source_hint": "router.py:1",
                    "sink_hint": "router.py:2",
                }
            ]
            candidate_findings = [
                {
                    "file": "router.py",
                    "line": 2,
                    "line_end": 2,
                    "title": "Dynamic query construction may allow injection",
                    "category": "SQL injection",
                    "path_hint": "request.args -> run(query)",
                    "source_hint": "router.py:1",
                    "sink_hint": "router.py:2",
                    "confidence": 79,
                }
            ]

            review_items = build_candidate_review_findings(
                candidate_findings=candidate_findings,
                validated_findings=validated_findings,
                source_root=root,
                files=[sample],
            )

            self.assertEqual(review_items, [])


if __name__ == "__main__":
    unittest.main()
