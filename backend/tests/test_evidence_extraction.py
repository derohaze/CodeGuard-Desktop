from pathlib import Path
import sys
import tempfile
import unittest


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.infrastructure.services.repository.evidence_extraction import extract_evidence


class EvidenceExtractionTests(unittest.TestCase):
    def test_extracts_line_window_and_preserves_range(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "sample.py"
            path.write_text(
                "line1\nline2\nline3\nline4\nline5\nline6\n",
                encoding="utf-8",
            )
            evidence = extract_evidence(path, 3, 4, radius=1)

            self.assertEqual(evidence["line_start"], 3)
            self.assertEqual(evidence["line_end"], 4)
            self.assertIn("2: line2", evidence["snippet"])
            self.assertIn("5: line5", evidence["snippet"])


if __name__ == "__main__":
    unittest.main()
