from __future__ import annotations

import json
import sys
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


class BenchmarkProvider:
    def __init__(self, provider_name: str, response_plan: list[object]) -> None:
        self.provider_name = provider_name
        self.response_plan = list(response_plan)
        self.model_router = None
        self.calls = 0

    def map_repository(self, *args, **kwargs):
        self.calls += 1
        planned = self.response_plan.pop(0)
        if isinstance(planned, Exception):
            raise planned
        return planned

    def review_paths(self, *args, **kwargs):
        return {"review_note": "", "repository_summary": "", "findings": []}

    def validate_findings(self, *args, **kwargs):
        return {"review_note": "", "safe_summary": "", "findings": []}

    def summarize_verdict(self, *args, **kwargs):
        return {"review_note": "", "repository_summary": "", "coverage_summary": ""}

    def explain_finding(self, *args, **kwargs):
        return {}

    def draft_fix_strategies(self, *args, **kwargs):
        return {}

    def validate_remediation(self, *args, **kwargs):
        return {}


def run_runtime_benchmark() -> dict:
    scenarios = [
        {
            "name": "gateway_fallback_success",
            "providers": [
                BenchmarkProvider(
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
                ),
                BenchmarkProvider("groq", [{"repository_summary": "ok"}]),
            ],
        },
        {
            "name": "rate_limit_fallback_success",
            "providers": [
                BenchmarkProvider(
                    "modal",
                    [
                        ExternalAIServiceError(
                            "Modal rate limited the request.",
                            provider="modal",
                            retryable=True,
                            status_code=429,
                            failure_kind="rate_limit",
                        )
                    ],
                ),
                BenchmarkProvider("groq", [{"repository_summary": "ok"}]),
            ],
        },
        {
            "name": "all_providers_fail",
            "providers": [
                BenchmarkProvider(
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
                ),
                BenchmarkProvider(
                    "groq",
                    [
                        ExternalAIServiceError(
                            "Groq returned 503.",
                            provider="groq",
                            retryable=True,
                            status_code=503,
                            failure_kind="gateway",
                        )
                    ],
                ),
            ],
        },
    ]

    results = []
    for scenario in scenarios:
        client = FallbackSecurityClient(
            scenario["providers"],
            execution_policy=AIExecutionPolicy(),
            scheduler=ProviderScheduler(cooldown_seconds=0.01, quarantine_seconds=0.02),
            response_cache=AIResponseCache(ttl_seconds=60),
            runtime_metrics=RuntimeMetrics(),
        )
        status = "completed"
        error = None
        try:
            client.map_repository("repo", "/tmp", {}, {}, "balanced")
        except ExternalAIServiceError as exc:
            status = "failed"
            error = {
                "provider": exc.provider,
                "failure_kind": exc.failure_kind,
                "status_code": exc.status_code,
                "message": str(exc),
            }
        results.append(
            {
                "name": scenario["name"],
                "status": status,
                "runtime_metrics": client.snapshot_runtime_metrics(),
                "events": client.drain_runtime_events(),
                "error": error,
            }
        )

    completion_rate = round(sum(1 for result in results if result["status"] == "completed") / len(results), 3)
    average_provider_calls = round(
        sum(result["runtime_metrics"]["provider_calls_total"] for result in results) / len(results),
        3,
    )
    average_retries = round(
        sum(result["runtime_metrics"]["retries_total"] for result in results) / len(results),
        3,
    )
    fallback_rate = round(
        sum(result["runtime_metrics"]["fallback_activations"] for result in results) / len(results),
        3,
    )

    return {
        "summary": {
            "scenarios_total": len(results),
            "completion_rate": completion_rate,
            "average_provider_calls_per_run": average_provider_calls,
            "average_retries_per_run": average_retries,
            "fallback_activation_rate": fallback_rate,
        },
        "scenarios": results,
    }


if __name__ == "__main__":
    print(json.dumps(run_runtime_benchmark(), indent=2))
