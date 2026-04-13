import sys
import unittest
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.infrastructure.services.repository_analysis import adaptive_chunk_work_items, estimate_review_item_tokens


def _item(index: int, *, snippet_size: int) -> dict[str, str]:
    return {
        "file": f"module_{index}.py",
        "signal_score": "5",
        "rationale": "security-relevant code path",
        "imports": "fastapi, motor",
        "related_attack_surface": "public HTTP endpoint",
        "review_focus": "trace untrusted input to sensitive sink",
        "block_id": f"module_{index}.py:{index}",
        "block_kind": "window",
        "start_line": str(index * 10 + 1),
        "end_line": str(index * 10 + 9),
        "snippet": "x" * snippet_size,
    }


class AdaptiveBatchingTests(unittest.TestCase):
    def test_small_items_are_grouped_into_fewer_batches(self) -> None:
        items = [_item(index, snippet_size=300) for index in range(6)]

        batches = adaptive_chunk_work_items(items, scan_mode="deep", support_confidence="medium", target_prompt_tokens=6000)

        self.assertLess(len(batches), len(items))
        self.assertEqual(sum(len(batch) for batch in batches), len(items))
        self.assertTrue(any(len(batch) > 1 for batch in batches))

    def test_large_items_split_across_multiple_batches(self) -> None:
        items = [_item(index, snippet_size=9000) for index in range(4)]

        batches = adaptive_chunk_work_items(items, scan_mode="deep", support_confidence="medium", target_prompt_tokens=6000)

        self.assertGreater(len(batches), 1)
        self.assertEqual(sum(len(batch) for batch in batches), len(items))

    def test_low_confidence_caps_batch_growth(self) -> None:
        items = [_item(index, snippet_size=250) for index in range(10)]

        batches = adaptive_chunk_work_items(items, scan_mode="deep", support_confidence="unknown", target_prompt_tokens=12000)

        self.assertTrue(all(len(batch) <= 6 for batch in batches))

    def test_item_token_estimate_scales_with_snippet_size(self) -> None:
        small = estimate_review_item_tokens(_item(1, snippet_size=200))
        large = estimate_review_item_tokens(_item(2, snippet_size=4000))

        self.assertGreater(large, small)


if __name__ == "__main__":
    unittest.main()
