import asyncio
import sys
import unittest
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.exceptions import ExternalAIServiceError
from app.infrastructure.ai.ai_response_cache import AIResponseCache
from app.infrastructure.ai.execution_policy import AIExecutionPolicy
from app.infrastructure.ai.fallback_security_client import FallbackSecurityClient
from app.infrastructure.ai.provider_scheduler import ProviderScheduler
from app.infrastructure.ai.runtime_metrics import RuntimeMetrics


class StubProvider:
    def __init__(self, provider_name: str, responses: list[object]) -> None:
        self.provider_name = provider_name
        self.responses = list(responses)
        self.model_router = None
        self.calls = 0

    async def map_repository(self, *args, **kwargs):
        self.calls += 1
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    async def review_paths(self, *args, **kwargs):
        return {"review_note": "", "repository_summary": "", "findings": []}

    async def validate_findings(self, *args, **kwargs):
        return {"review_note": "", "safe_summary": "", "findings": []}

    async def summarize_verdict(self, *args, **kwargs):
        return {"review_note": "", "repository_summary": "", "coverage_summary": ""}

    async def explain_finding(self, *args, **kwargs):
        return {}

    async def draft_fix_strategies(self, *args, **kwargs):
        return {}

    async def validate_remediation(self, *args, **kwargs):
        return {}


class RuntimeResilienceTests(unittest.TestCase):
    def test_gateway_failure_falls_back_to_next_provider(self):
        primary = StubProvider(
            "modal",
            [
                ExternalAIServiceError(
                    "Modal provider error: upstream 502",
                    provider="modal",
                    retryable=True,
                    status_code=502,
                    failure_kind="gateway",
                )
            ],
        )
        fallback = StubProvider("groq", [{"repository_summary": "ok"}])
        client = FallbackSecurityClient(
            [primary, fallback],
            execution_policy=AIExecutionPolicy(),
            scheduler=ProviderScheduler(cooldown_seconds=0.01, quarantine_seconds=0.02),
            response_cache=AIResponseCache(ttl_seconds=60),
            runtime_metrics=RuntimeMetrics(),
        )

        result = asyncio.run(client.map_repository("repo", "/tmp", {}, {}, "balanced"))

        self.assertEqual(result["repository_summary"], "ok")
        metrics = client.snapshot_runtime_metrics()
        self.assertEqual(metrics["fallback_activations"], 1)
        self.assertEqual(metrics["provider_failures_by_provider"]["modal"], 1)
        self.assertEqual(metrics["provider_successes_by_provider"]["groq"], 1)
        self.assertIn("Fallback activated", " ".join(client.drain_runtime_events()))

    def test_output_format_failure_does_not_fallback(self):
        primary = StubProvider(
            "modal",
            [
                ExternalAIServiceError(
                    "Modal returned malformed output.",
                    provider="modal",
                    retryable=False,
                    failure_kind="output_format",
                )
            ],
        )
        fallback = StubProvider("groq", [{"repository_summary": "ok"}])
        client = FallbackSecurityClient([primary, fallback])

        with self.assertRaises(ExternalAIServiceError):
            asyncio.run(client.map_repository("repo", "/tmp", {}, {}, "balanced"))

        self.assertEqual(fallback.calls, 0)

    def test_cache_reuses_duplicate_request(self):
        provider = StubProvider("groq", [{"repository_summary": "cached"}])
        client = FallbackSecurityClient([provider])

        async def run_twice():
            first = await client.map_repository("repo", "/tmp", {}, {}, "balanced")
            second = await client.map_repository("repo", "/tmp", {}, {}, "balanced")
            return first, second

        first, second = asyncio.run(run_twice())

        self.assertEqual(first, second)
        self.assertEqual(provider.calls, 1)
        metrics = client.snapshot_runtime_metrics()
        self.assertGreaterEqual(metrics["cache_hits"], 1)

    def test_output_format_failure_does_not_trigger_provider_cooldown(self):
        provider = StubProvider(
            "nvidia",
            [
                ExternalAIServiceError(
                    "NVIDIA returned malformed output.",
                    provider="nvidia",
                    retryable=True,
                    failure_kind="output_format",
                ),
                {"repository_summary": "recovered"},
            ],
        )
        client = FallbackSecurityClient([provider], scheduler=ProviderScheduler(cooldown_seconds=10.0, quarantine_seconds=10.0))

        async def run_case():
            with self.assertRaises(ExternalAIServiceError):
                await client.map_repository("repo", "/tmp", {}, {}, "balanced")
            return await client.map_repository("repo", "/tmp", {}, {}, "balanced")

        result = asyncio.run(run_case())

        self.assertEqual(result["repository_summary"], "recovered")
        self.assertEqual(provider.calls, 2)


if __name__ == "__main__":
    unittest.main()
