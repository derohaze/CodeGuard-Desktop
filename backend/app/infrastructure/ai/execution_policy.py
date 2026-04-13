from __future__ import annotations


TASK_PROVIDER_PREFERENCES = {
    "map_repository": ["modal", "groq"],
    "review_paths": ["modal", "groq"],
    "validate_findings": ["modal", "groq"],
    "summarize_verdict": ["modal", "groq"],
    "explain_finding": ["modal", "groq"],
    "draft_fix_strategies": ["modal", "groq"],
    "validate_remediation": ["modal", "groq"],
}


class AIExecutionPolicy:
    def task_token_budget(self, task_name: str) -> int:
        budgets = {
            "map_repository": 4500,
            "review_paths": 5200,
            "validate_findings": 4200,
            "summarize_verdict": 2800,
            "explain_finding": 3200,
            "draft_fix_strategies": 4200,
            "validate_remediation": 3800,
        }
        return budgets.get(task_name, 3000)

    def provider_order_for(self, task_name: str, available_providers: list[str]) -> list[str]:
        preferred = TASK_PROVIDER_PREFERENCES.get(task_name, available_providers)
        ordered = [provider for provider in preferred if provider in available_providers]
        ordered.extend(provider for provider in available_providers if provider not in ordered)
        return ordered

    def cacheable(self, task_name: str) -> bool:
        return task_name in {
            "map_repository",
            "review_paths",
            "validate_findings",
            "summarize_verdict",
            "explain_finding",
            "draft_fix_strategies",
            "validate_remediation",
        }

    def max_attempts(self, task_name: str) -> int:
        if task_name in {"review_paths", "validate_findings"}:
            return 2
        return 1

    def should_fallback(self, error) -> bool:
        failure_kind = getattr(error, "failure_kind", "runtime")
        if failure_kind in {"output_format", "parse"}:
            return False
        return True

    def should_retry(self, error) -> bool:
        failure_kind = getattr(error, "failure_kind", "runtime")
        return getattr(error, "retryable", False) and failure_kind in {
            "gateway",
            "timeout",
            "connection",
            "rate_limit",
            "runtime",
            "upstream",
        }
