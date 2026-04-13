import asyncio
import sys
import time
import unittest
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.infrastructure.ai.groq_key_pool import GroqKeyPool


class GroqKeyPoolTests(unittest.TestCase):
    def test_round_robin_uses_multiple_keys(self):
        pool = GroqKeyPool(["key-1", "key-2"], cooldown_seconds=0.01, quarantine_seconds=0.02)

        async def run_case():
            first = await pool.acquire_key()
            await pool.mark_success(first["label"])
            second = await pool.acquire_key()
            return first, second

        first, second = asyncio.run(run_case())

        self.assertNotEqual(first["label"], second["label"])

    def test_rate_limit_puts_key_on_cooldown(self):
        pool = GroqKeyPool(["key-1"], cooldown_seconds=0.01, quarantine_seconds=0.02)

        async def run_case():
            key = await pool.acquire_key()
            cooldown = await pool.mark_rate_limited(key["label"], headers={"retry-after": "0.02"})
            unavailable = await pool.acquire_key()
            await asyncio.sleep(0.03)
            available = await pool.acquire_key()
            return cooldown, unavailable, available

        cooldown, unavailable, available = asyncio.run(run_case())

        self.assertGreaterEqual(cooldown, 0.02)
        self.assertFalse(bool(unavailable["api_key"]))
        self.assertTrue(bool(available["api_key"]))

    def test_repeated_failures_quarantine_key(self):
        pool = GroqKeyPool(["key-1"], cooldown_seconds=0.01, failure_threshold=2, quarantine_seconds=0.05)
        async def run_case():
            key = await pool.acquire_key()
            await pool.mark_failure(key["label"])
            key = await pool.acquire_key()
            await pool.mark_failure(key["label"], severe=True)
            return await pool.snapshot()

        snapshot = asyncio.run(run_case())
        self.assertEqual(snapshot["keys"][0]["last_status"], "quarantined")
        self.assertGreater(snapshot["keys"][0]["disabled_remaining_seconds"], 0)


if __name__ == "__main__":
    unittest.main()
