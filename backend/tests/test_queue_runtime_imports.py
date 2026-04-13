import asyncio
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.infrastructure.queue import redis as queue_redis


class QueueRuntimeImportTests(unittest.TestCase):
    def test_initialize_redis_skips_optional_imports_for_in_process_backend(self):
        settings = SimpleNamespace(queue_backend="in_process", redis_url=None)

        with patch("app.infrastructure.queue.redis.get_settings", return_value=settings), patch(
            "app.infrastructure.queue.redis._require_queue_runtime",
            side_effect=AssertionError("optional queue runtime should not be imported"),
        ):
            result = asyncio.run(queue_redis.initialize_redis())

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
