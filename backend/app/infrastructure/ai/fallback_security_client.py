from __future__ import annotations

from app.core.exceptions import ExternalAIServiceError
from app.domain.services.ai_client import SecurityAnalysisAIClient
from app.infrastructure.ai.ai_response_cache import AIResponseCache
from app.infrastructure.ai.execution_policy import AIExecutionPolicy
from app.infrastructure.ai.provider_scheduler import ProviderScheduler
from app.infrastructure.ai.runtime_metrics import RuntimeMetrics


class FallbackSecurityClient(SecurityAnalysisAIClient):
    def __init__(
        self,
        clients: list[SecurityAnalysisAIClient],
        *,
        execution_policy: AIExecutionPolicy | None = None,
        scheduler: ProviderScheduler | None = None,
        response_cache: AIResponseCache | None = None,
        runtime_metrics: RuntimeMetrics | None = None,
    ) -> None:
        self.clients = clients
        self.execution_policy = execution_policy or AIExecutionPolicy()
        self.scheduler = scheduler or ProviderScheduler()
        self.response_cache = response_cache or AIResponseCache()
        self.runtime_metrics = runtime_metrics or RuntimeMetrics()
        self.model_router = next((getattr(client, "model_router", None) for client in clients if getattr(client, "model_router", None) is not None), None)

    def reset_runtime_state(self) -> None:
        self.runtime_metrics.reset()

    def drain_runtime_events(self) -> list[str]:
        events = self.runtime_metrics.drain_events()
        for client in self.clients:
            events.extend(getattr(client, "drain_runtime_events", lambda: [])())
        return events

    def snapshot_runtime_metrics(self, *, reset: bool = False) -> dict | None:
        snapshot = {
            **self.runtime_metrics.snapshot(),
            "provider_scheduler": {},
            "provider_runtime": {
                getattr(client, "provider_name", f"provider_{index}"): (
                    getattr(client, "snapshot_runtime_metrics", lambda **_: None)(reset=False)
                )
                for index, client in enumerate(self.clients)
            },
        }
        if reset:
            self.runtime_metrics.reset()
        return snapshot

    async def map_repository(self, project_name: str, source_path: str, repository_profile: dict, repository_artifacts: dict, preset: str) -> dict:
        return await self._call("map_repository", project_name, source_path, repository_profile, repository_artifacts, preset)

    async def review_paths(self, project_name: str, source_path: str, repository_profile: dict, repository_map: dict, work_items: list[dict[str, str]], batch_index: int, total_batches: int, preset: str) -> dict:
        return await self._call("review_paths", project_name, source_path, repository_profile, repository_map, work_items, batch_index, total_batches, preset)

    async def validate_findings(self, project_name: str, source_path: str, repository_profile: dict, repository_map: dict, findings: list[dict], preset: str) -> dict:
        return await self._call("validate_findings", project_name, source_path, repository_profile, repository_map, findings, preset)

    async def summarize_verdict(self, project_name: str, source_path: str, repository_profile: dict, repository_map: dict, findings: list[dict], security_score: int | None, preset: str) -> dict:
        return await self._call("summarize_verdict", project_name, source_path, repository_profile, repository_map, findings, security_score, preset)

    async def explain_finding(self, remediation_context: dict) -> dict:
        return await self._call("explain_finding", remediation_context)

    async def draft_fix_strategies(self, remediation_context: dict, mode: str) -> dict:
        return await self._call("draft_fix_strategies", remediation_context, mode)

    async def validate_remediation(self, remediation_context: dict, remediation_draft: dict, mode: str) -> dict:
        return await self._call("validate_remediation", remediation_context, remediation_draft, mode)

    async def _call(self, method_name: str, *args, **kwargs):
        cache_key = {
            "method": method_name,
            "args": args,
            "kwargs": kwargs,
        }
        if self.execution_policy.cacheable(method_name):
            cached = await self.response_cache.get(cache_key)
            if cached is not None:
                self.runtime_metrics.record_cache_hit()
                self.runtime_metrics.add_event("Reused cached AI result.")
                return cached

        last_error: ExternalAIServiceError | None = None
        skipped_due_to_cooldown = False
        clients_by_provider = {
            getattr(client, "provider_name", f"provider_{index}"): client
            for index, client in enumerate(self.clients)
        }
        ordered_provider_names = self.execution_policy.provider_order_for(method_name, list(clients_by_provider.keys()))
        attempts_left = self.execution_policy.max_attempts(method_name)

        for provider_index, provider_name in enumerate(ordered_provider_names):
            client = clients_by_provider[provider_name]
            method = getattr(client, method_name)
            available, remaining = await self.scheduler.availability(provider_name)
            if not available:
                skipped_due_to_cooldown = True
                self.runtime_metrics.add_event("An AI provider is cooling down after recent failures; retrying.")
                continue

            self.runtime_metrics.record_call(
                provider_name,
                method_name,
                budget_tokens=self.execution_policy.task_token_budget(method_name),
            )
            started_at = self.runtime_metrics.start_span()
            try:
                if self.execution_policy.cacheable(method_name):
                    result, cache_status = await self.response_cache.get_or_compute(
                        cache_key,
                        lambda: self.scheduler.run(provider_name, lambda: method(*args, **kwargs)),
                    )
                    if cache_status == "hit":
                        self.runtime_metrics.record_cache_hit()
                    elif cache_status == "coalesced":
                        self.runtime_metrics.record_cache_hit()
                        self.runtime_metrics.record_coalesced_wait()
                        self.runtime_metrics.add_event("Coalesced duplicate AI request.")
                    else:
                        self.runtime_metrics.record_cache_miss()
                else:
                    result = await self.scheduler.run(provider_name, lambda: method(*args, **kwargs))
                    self.runtime_metrics.record_cache_miss()
                await self.scheduler.mark_success(provider_name)
                self.runtime_metrics.record_success(provider_name)
                self.runtime_metrics.record_call_duration(provider_name, method_name, started_at=started_at)
                if provider_index > 0:
                    self.runtime_metrics.add_event("Fallback provider completed the request successfully.")
                return result
            except ExternalAIServiceError as exc:
                self.runtime_metrics.record_call_duration(provider_name, method_name, started_at=started_at)
                last_error = exc
                self.runtime_metrics.record_failure(provider_name, exc.failure_kind)
                if self._should_cooldown(exc):
                    cooldown = await self.scheduler.mark_failure(provider_name)
                    self.runtime_metrics.add_event(
                        f"AI provider failed with {exc.failure_kind}; cooling down for {cooldown:.1f}s."
                    )
                else:
                    self.runtime_metrics.add_event(
                        f"AI provider returned {exc.failure_kind}; keeping provider available for subsequent requests."
                    )
                if provider_index < len(ordered_provider_names) - 1 and self.execution_policy.should_fallback(exc):
                    self.runtime_metrics.record_fallback_activation()
                    self.runtime_metrics.record_retry()
                    self.runtime_metrics.add_event("Fallback activated after a provider failure.")
                    continue
                attempts_left -= 1
                if not self.execution_policy.should_retry(exc) or attempts_left <= 0:
                    break
                continue
        if last_error is not None:
            raise last_error
        if skipped_due_to_cooldown:
            raise ExternalAIServiceError(
                "All configured AI providers are temporarily cooling down after recent failures. Retry shortly.",
                provider="ai_runtime",
                retryable=True,
                failure_kind="cooldown",
            )
        raise ExternalAIServiceError("No AI provider is configured.", provider="none", retryable=False)

    @staticmethod
    def _should_cooldown(exc: ExternalAIServiceError) -> bool:
        return exc.failure_kind not in {"output_format", "request_rejected"}
