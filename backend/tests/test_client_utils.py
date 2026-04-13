import json
import sys
import unittest
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.infrastructure.ai.client_utils import json_for_task_prompt


class ClientUtilsTests(unittest.TestCase):
    def test_task_prompt_compaction_respects_size_budget(self) -> None:
        payload = {
            "items": [{"id": index, "text": "x" * 200} for index in range(20)],
            "summary": "y" * 600,
        }

        compacted = json_for_task_prompt("fix_validate", "remediation_draft", payload, max_chars=240)

        self.assertLessEqual(len(compacted), 240)
        parsed = json.loads(compacted)
        self.assertTrue(parsed)

    def test_fix_validate_prompt_keeps_patch_snippets_when_budget_allows(self) -> None:
        payload = {
            "review_summary": "Prepared remediation patch",
            "recommended_strategy_id": "safe-url-validation",
            "strategies": [
                {
                    "id": "safe-url-validation",
                    "label": "Safe URL validation",
                    "kind": "refactor",
                    "summary": "Validate destination host before outbound call.",
                    "rationale": "Grounded in the sink.",
                    "diff": "--- a/file.ts\n+++ b/file.ts\n@@\n-old\n+new",
                    "recommended": True,
                }
            ],
            "patch": {
                "file": "src/lib/api/admin/chat.ts",
                "summary": "Constrain outbound URL construction.",
                "diff": "--- a/file.ts\n+++ b/file.ts\n@@\n-old\n+new",
                "validation_notes": ["Targets sink."],
                "before_snippet": "return authPost(`${API_URL}/admin/chat/close/${convId}`)",
                "after_snippet": "return authPost(buildAdminChatCloseUrl(convId))",
            },
        }

        compacted = json_for_task_prompt("fix_validate", "remediation_draft", payload, max_chars=4000)
        parsed = json.loads(compacted)

        self.assertIn("patch", parsed)
        self.assertIn("before_snippet", parsed["patch"])
        self.assertIn("after_snippet", parsed["patch"])
        self.assertIn("diff", parsed["patch"])


if __name__ == "__main__":
    unittest.main()
