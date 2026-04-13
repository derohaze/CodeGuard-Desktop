import sys
import unittest
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.infrastructure.ai.prompt_loader import load_prompt_pack


class PromptLoaderTests(unittest.TestCase):
    def test_fix_prompt_pack_includes_shared_remediation_rules(self) -> None:
        prompt = load_prompt_pack("fix_prompt.md")

        self.assertIn("Shared remediation policy", prompt)
        self.assertIn("command injection", prompt.lower())
        self.assertIn("NoSQL injection", prompt)

    def test_path_reviewer_prompt_pack_includes_framework_focus(self) -> None:
        prompt = load_prompt_pack("path_reviewer.md")

        self.assertIn("Shared security scan rules", prompt)
        self.assertIn("GraphQL", prompt)
        self.assertIn("Java servlet", prompt)


if __name__ == "__main__":
    unittest.main()
