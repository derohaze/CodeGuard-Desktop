import sys
import unittest
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.infrastructure.learning.ingestion.ingestion_validation import (
    sanitize_external_item,
    validate_external_source_spec,
)
from app.infrastructure.learning.common.schemas import ExternalKnowledgeSourceSpec


class LearningIngestionValidationTests(unittest.TestCase):
    def test_validate_source_rejects_invalid_endpoint_scheme(self):
        source = ExternalKnowledgeSourceSpec(
            source_name="cwe",
            source_version="1",
            endpoint="ftp://example.com/data.json",
            item_type="security_pattern",
        )
        with self.assertRaises(ValueError):
            validate_external_source_spec(source)

    def test_sanitize_item_truncates_and_normalizes_tags(self):
        long_text = "A" * 70_000
        sanitized = sanitize_external_item(
            {
                "title": " SQL Injection \x00 ",
                "summary": long_text,
                "tags": [" SQL ", "sql", "INJECTION", "a" * 120],
            }
        ).item
        self.assertEqual(sanitized["title"], "SQL Injection")
        self.assertEqual(len(sanitized["summary"]), 64_000)
        self.assertEqual(sanitized["tags"][0], "sql")
        self.assertIn("injection", sanitized["tags"])

    def test_sanitize_item_requires_title_or_summary(self):
        with self.assertRaises(ValueError):
            sanitize_external_item({"description": "   "})


if __name__ == "__main__":
    unittest.main()
