from __future__ import annotations

import threading
from copy import deepcopy
from time import perf_counter


class RuntimeMetrics:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._metrics = self._new_metrics()
        self._events: list[str] = []

    def reset(self) -> None:
        with self._lock:
            self._metrics = self._new_metrics()
            self._events = []

    def record_call(self, provider: str, task_name: str, *, budget_tokens: int) -> None:
        with self._lock:
            self._metrics["provider_calls_total"] += 1
            self._metrics["estimated_prompt_budget_tokens"] += max(0, int(budget_tokens))
            self._metrics["provider_calls_by_provider"][provider] = self._metrics["provider_calls_by_provider"].get(provider, 0) + 1
            self._metrics["tasks_by_name"][task_name] = self._metrics["tasks_by_name"].get(task_name, 0) + 1

    def start_span(self) -> float:
        return perf_counter()

    def record_call_duration(self, provider: str, task_name: str, *, started_at: float) -> None:
        duration_ms = round((perf_counter() - started_at) * 1000, 2)
        with self._lock:
            provider_stats = self._metrics["provider_duration_ms_by_provider"].setdefault(provider, {"total": 0.0, "count": 0, "last": 0.0})
            provider_stats["total"] += duration_ms
            provider_stats["count"] += 1
            provider_stats["last"] = duration_ms
            task_stats = self._metrics["task_duration_ms_by_name"].setdefault(task_name, {"total": 0.0, "count": 0, "last": 0.0})
            task_stats["total"] += duration_ms
            task_stats["count"] += 1
            task_stats["last"] = duration_ms

    def record_success(self, provider: str) -> None:
        with self._lock:
            self._metrics["provider_successes_by_provider"][provider] = self._metrics["provider_successes_by_provider"].get(provider, 0) + 1

    def record_failure(self, provider: str, failure_kind: str) -> None:
        with self._lock:
            self._metrics["provider_failures_total"] += 1
            self._metrics["provider_failures_by_provider"][provider] = self._metrics["provider_failures_by_provider"].get(provider, 0) + 1
            self._metrics["provider_failures_by_kind"][failure_kind] = self._metrics["provider_failures_by_kind"].get(failure_kind, 0) + 1

    def record_retry(self) -> None:
        with self._lock:
            self._metrics["retries_total"] += 1

    def record_fallback_activation(self) -> None:
        with self._lock:
            self._metrics["fallback_activations"] += 1

    def record_cache_hit(self) -> None:
        with self._lock:
            self._metrics["cache_hits"] += 1

    def record_cache_miss(self) -> None:
        with self._lock:
            self._metrics["cache_misses"] += 1

    def record_coalesced_wait(self) -> None:
        with self._lock:
            self._metrics["coalesced_requests"] += 1

    def add_event(self, message: str) -> None:
        if not message:
            return
        with self._lock:
            self._events.append(message)

    def drain_events(self) -> list[str]:
        with self._lock:
            events = list(self._events)
            self._events.clear()
            return events

    def snapshot(self) -> dict:
        with self._lock:
            metrics = deepcopy(self._metrics)
        total_calls = metrics["provider_calls_total"]
        metrics["cache_hit_rate"] = round(metrics["cache_hits"] / max(1, metrics["cache_hits"] + metrics["cache_misses"]), 3)
        metrics["average_provider_calls_per_task"] = round(total_calls / max(1, sum(metrics["tasks_by_name"].values())), 3)
        metrics["provider_duration_ms_by_provider"] = _with_avg(metrics["provider_duration_ms_by_provider"])
        metrics["task_duration_ms_by_name"] = _with_avg(metrics["task_duration_ms_by_name"])
        return metrics

    @staticmethod
    def _new_metrics() -> dict:
        return {
            "provider_calls_total": 0,
            "provider_calls_by_provider": {},
            "provider_successes_by_provider": {},
            "provider_failures_total": 0,
            "provider_failures_by_provider": {},
            "provider_failures_by_kind": {},
            "retries_total": 0,
            "fallback_activations": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "coalesced_requests": 0,
            "estimated_prompt_budget_tokens": 0,
            "tasks_by_name": {},
            "provider_duration_ms_by_provider": {},
            "task_duration_ms_by_name": {},
        }


def _with_avg(values: dict) -> dict:
    enriched: dict = {}
    for key, stats in values.items():
        if not isinstance(stats, dict):
            enriched[key] = stats
            continue
        total = float(stats.get("total", 0.0))
        count = int(stats.get("count", 0))
        enriched[key] = {
            **stats,
            "avg": round(total / max(1, count), 2),
        }
    return enriched
