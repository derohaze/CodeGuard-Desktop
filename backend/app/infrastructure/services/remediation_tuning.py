from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.entities.remediation import RemediationPlanEntity
from app.infrastructure.services.remediation_policy import category_requires_full_fix, normalize_category


MIN_REMEDIATION_SCORE = 70


@dataclass(slots=True)
class TuningDecision:
    should_retry: bool
    reason: str
    excluded_strategy_ids: list[str]
    constraints: list[str]


def build_tuning_context(
    *,
    base_context: dict[str, Any],
    category: str,
    previous_failures: list[dict[str, Any]],
    excluded_strategy_ids: list[str],
    attempt: int,
) -> dict[str, Any]:
    tuning = dict(base_context.get("tuning", {})) if isinstance(base_context.get("tuning"), dict) else {}
    tuning.update(
        {
            "attempt": attempt,
            "known_bad_strategies": _known_bad_strategies(category),
            "preferred_strategy_shape": _preferred_strategy_shape(category),
            "excluded_strategy_ids": sorted(set(excluded_strategy_ids)),
            "previous_failures": previous_failures,
            "constraints": _constraints_for_category(category),
        }
    )
    next_context = dict(base_context)
    next_context["tuning"] = tuning
    retry = dict(next_context.get("retry", {})) if isinstance(next_context.get("retry"), dict) else {}
    retry["excluded_strategy_ids"] = tuning["excluded_strategy_ids"]
    retry["attempted_strategy_ids"] = retry.get("attempted_strategy_ids", [])
    next_context["retry"] = retry
    return next_context


def evaluate_tuning_need(plan: RemediationPlanEntity) -> TuningDecision:
    if plan.score is None or not plan.strategies:
        return TuningDecision(True, "No scored remediation plan was produced.", [], ["Return a scored, code-grounded remediation plan."])
    if plan.patch is None or not plan.patch.diff.strip() or not plan.patch.after_snippet.strip():
        return TuningDecision(
            True,
            "No concrete patch diff or updated snippet was produced.",
            [plan.strategies[0].id] if plan.strategies else [],
            ["Return a concrete, code-grounded patch diff with before/after snippets."],
        )
    strategy = plan.strategies[0]
    category = normalize_category(plan.metrics.vulnerability_type if plan.metrics else "")
    constraints = _constraints_for_category(category)
    if not strategy.policy_compliant:
        return TuningDecision(
            True,
            "Recommended strategy violates hard remediation policy requirements.",
            [strategy.id],
            constraints,
        )
    if category_requires_full_fix(category) and strategy.fix_type != "full_fix":
        return TuningDecision(
            True,
            f"{category} requires a full fix, but the current recommendation is {strategy.fix_type.replace('_', ' ')}.",
            [strategy.id],
            constraints,
        )
    if plan.score.total >= MIN_REMEDIATION_SCORE and strategy.fix_type == "full_fix":
        return TuningDecision(False, "", [], constraints)
    if strategy.fix_type != "full_fix":
        return TuningDecision(
            True,
            f"Recommended strategy is only {strategy.fix_type.replace('_', ' ')} with score {plan.score.total}.",
            [strategy.id],
            constraints,
        )
    if plan.score.strategy_quality < 70:
        return TuningDecision(
            True,
            f"Strategy quality is too low ({plan.score.strategy_quality}).",
            [strategy.id],
            constraints,
        )
    return TuningDecision(False, "", [], constraints)


def extract_failure_case(*, plan: RemediationPlanEntity, context: dict[str, Any]) -> dict[str, Any]:
    strategy = plan.strategies[0] if plan.strategies else None
    return {
        "category": str(context.get("finding", {}).get("category", "")),
        "file": str(context.get("finding", {}).get("file", "")),
        "title": str(context.get("finding", {}).get("title", "")),
        "chosen_strategy": strategy.id if strategy else "",
        "chosen_kind": strategy.kind if strategy else "",
        "chosen_fix_type": strategy.fix_type if strategy else "",
        "score_total": plan.score.total if plan.score else 0,
        "score_breakdown": {
            "strategy_quality": plan.score.strategy_quality if plan.score else 0,
            "fix_completeness": plan.score.fix_completeness if plan.score else 0,
            "sink_alignment": plan.score.sink_alignment if plan.score else 0,
            "residual_risk": plan.score.residual_risk if plan.score else 0,
            "confidence": plan.score.confidence if plan.score else 0,
        },
        "path_hint": str(context.get("path", {}).get("path_hint", "")),
        "evidence_location": f"{context.get('finding', {}).get('file', '')}:{context.get('finding', {}).get('line', 0)}",
        "expected_strategy": _preferred_strategy_shape(str(context.get("finding", {}).get("category", ""))),
    }


def choose_better_plan(left: RemediationPlanEntity, right: RemediationPlanEntity) -> RemediationPlanEntity:
    if left.score is None:
        return right
    if right.score is None:
        return left
    left_strategy = left.strategies[0] if left.strategies else None
    right_strategy = right.strategies[0] if right.strategies else None
    if left_strategy and right_strategy and left_strategy.policy_compliant != right_strategy.policy_compliant:
        return right if right_strategy.policy_compliant else left
    if right.score.total > left.score.total:
        return right
    if right.score.total == left.score.total and right.score.fix_completeness > left.score.fix_completeness:
        return right
    return left


def _known_bad_strategies(category: str) -> list[str]:
    lowered = category.lower()
    patterns: list[str] = []
    if "sql injection" in lowered:
        patterns.extend(["sanitization-only", "router input filtering", "escape quotes only"])
    if "command injection" in lowered:
        patterns.extend(["strip dangerous chars", "regex filtering only"])
    if "auth" in lowered or "session" in lowered:
        patterns.extend(["route-only guard", "conditional bypass check without central verification"])
    if "redirect" in lowered:
        patterns.extend(["encoding-only redirect", "temporary redirect guard"])
    if "nosql" in lowered:
        patterns.extend(["string sanitization around $where", "regex strip only"])
    return patterns


def _preferred_strategy_shape(category: str) -> str:
    lowered = category.lower()
    if "sql injection" in lowered:
        return "sink-level parameterization or prepared query execution"
    if "command injection" in lowered:
        return "safe execution API with argv separation and no shell semantics"
    if "ssrf" in lowered:
        return "allowlisted outbound request handling with URL validation at the client boundary"
    if "auth" in lowered or "session" in lowered:
        return "auth/session verification in the central helper, middleware, or service layer"
    if "nosql" in lowered:
        return "typed query builder or allowlisted operator usage at the query layer"
    if "redirect" in lowered:
        return "trusted relative redirect or strict host allowlist validation"
    return "sink-level structural remediation"


def _constraints_for_category(category: str) -> list[str]:
    lowered = normalize_category(category)
    constraints = ["Prefer materially different strategies on retry."]
    if "sql injection" in lowered:
        constraints.append("Must fix at the sink with parameterized or prepared execution.")
        constraints.append("Do not recommend sanitization-only or guard-only SQL injection fixes.")
    if "command injection" in lowered:
        constraints.append("Must eliminate shell-like execution semantics with safe argv-based process APIs.")
        constraints.append("Do not recommend input-filtering-only command injection fixes.")
    if "auth" in lowered or "session" in lowered:
        constraints.append("Must fix in auth/session verification logic, not only at the route boundary.")
        constraints.append("Do not recommend route-only guards as the final auth/session remediation.")
    if "redirect" in lowered:
        constraints.append("Must restrict redirects to trusted relative targets or allowlisted hosts.")
    if "nosql" in lowered:
        constraints.append("Must use typed query construction or allowlisted operators at the query layer.")
    if "ssrf" in lowered:
        constraints.append("Must validate outbound hosts and protocols using allowlisting at the request client boundary.")
    return constraints
