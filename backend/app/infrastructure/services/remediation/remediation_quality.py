from __future__ import annotations

from dataclasses import replace

from app.domain.entities.remediation import FixStrategyEntity, PatchCandidateEntity
from app.infrastructure.services.remediation.remediation_policy import (
    category_requires_full_fix,
    evaluate_strategy_policy,
    normalize_category,
)


def assess_remediation_quality(
    *,
    finding: dict,
    strategies: list[FixStrategyEntity],
    patch: PatchCandidateEntity,
) -> tuple[list[FixStrategyEntity], PatchCandidateEntity, str | None]:
    if not strategies:
        return strategies, patch, None

    category = normalize_category(str(finding.get("category", "")))
    finding_file = str(finding.get("file", ""))
    enriched: list[FixStrategyEntity] = []

    for strategy in strategies:
        assessed = _assess_strategy(
            strategy=strategy,
            category=category,
            patch_file=patch.file,
            finding_file=finding_file,
        )
        enriched.append(assessed)

    compliant = [item for item in enriched if item.policy_compliant]
    non_compliant = [item for item in enriched if not item.policy_compliant]
    compliant.sort(key=_strategy_sort_key, reverse=True)
    non_compliant.sort(key=_strategy_sort_key, reverse=True)
    enriched = [*compliant, *non_compliant]
    recommended_id = enriched[0].id
    final_strategies: list[FixStrategyEntity] = []
    for item in enriched:
        if item.id == recommended_id:
            final_strategies.append(
                replace(
                    item,
                    recommended=True,
                    selection_reason=item.selection_reason or _selection_reason(item),
                    non_selection_reason="",
                )
            )
            continue
        final_strategies.append(
            replace(
                item,
                recommended=False,
                non_selection_reason=item.non_selection_reason or _non_selection_reason(item, enriched[0]),
            )
        )

    chosen = final_strategies[0]
    patch_entity = replace(
        patch,
        fix_type=chosen.fix_type,
        rationale=chosen.selection_reason or chosen.rationale,
        residual_risks=_merge_unique(chosen.residual_risks, patch.validation_notes),
        manual_review_required=(
            chosen.fix_type != "full_fix"
            or chosen.regression_risk == "high"
            or not chosen.policy_compliant
            or (category_requires_full_fix(category) and chosen.fix_type != "full_fix")
        ),
        validation_notes=_build_patch_validation_notes(category=category, strategy=chosen, patch=patch),
    )
    return final_strategies, patch_entity, recommended_id


def _assess_strategy(*, strategy: FixStrategyEntity, category: str, patch_file: str, finding_file: str) -> FixStrategyEntity:
    base_fix_type = _infer_fix_type(category, strategy)
    policy = evaluate_strategy_policy(category=category, strategy=strategy, fix_type=base_fix_type, patch_file=patch_file)
    fix_type = _enforce_fix_type(strategy=strategy, fix_type=base_fix_type, policy_compliant=policy.compliant)
    strength = _infer_security_strength(category, strategy, fix_type, policy.compliant)
    regression_risk = _infer_regression_risk(strategy, fix_type)
    sink_alignment_notes = _sink_alignment_notes(category=category, patch_file=patch_file, finding_file=finding_file)
    residual_risks = _infer_residual_risks(category, strategy, fix_type, patch_file, list(policy.violations) + sink_alignment_notes)
    return replace(
        strategy,
        fix_type=fix_type,
        security_strength=strength,
        regression_risk=regression_risk,
        selection_reason=_selection_reason_text(category, strategy, fix_type, strength, policy.compliant, list(policy.violations)),
        residual_risks=residual_risks,
        policy_compliant=policy.compliant,
        policy_violations=list(policy.violations),
    )


def _infer_fix_type(category: str, strategy: FixStrategyEntity) -> str:
    diff = strategy.diff.lower()
    if strategy.kind == "guard":
        return "temporary_guard"
    if strategy.kind == "sanitization":
        if any(token in diff for token in ("allowlist", "safe_redirect", "validated_host")) and "redirect" in category:
            return "full_fix"
        return "partial_mitigation"
    if any(token in diff for token in ("%s", "preparedstatement", "cursor.execute(query,", "bind", "shell=false", "subprocess.run(", "urllib.parse", "urlparse", "session.regenerate", "session_regenerate_id", "$eq", "bson")):
        return "full_fix"
    return "partial_mitigation"


def _enforce_fix_type(*, strategy: FixStrategyEntity, fix_type: str, policy_compliant: bool) -> str:
    if policy_compliant:
        return fix_type
    if strategy.kind == "guard":
        return "risky_workaround"
    if fix_type == "full_fix":
        return "partial_mitigation"
    return fix_type


def _infer_security_strength(category: str, strategy: FixStrategyEntity, fix_type: str, policy_compliant: bool) -> str:
    if not policy_compliant:
        return "low"
    if fix_type == "full_fix" and strategy.kind == _preferred_kind(category):
        return "high"
    if fix_type == "temporary_guard":
        return "low"
    if fix_type == "partial_mitigation":
        return "medium"
    return "medium"


def _infer_regression_risk(strategy: FixStrategyEntity, fix_type: str) -> str:
    if fix_type == "temporary_guard":
        return "low"
    if strategy.kind == "refactor" and strategy.effort == "high":
        return "high"
    if strategy.kind == "refactor":
        return "medium"
    return "low"


def _infer_residual_risks(
    category: str,
    strategy: FixStrategyEntity,
    fix_type: str,
    patch_file: str,
    policy_violations: list[str],
) -> list[str]:
    residuals: list[str] = []
    if fix_type != "full_fix":
        residuals.append("This patch reduces exposure, but may not fully eliminate the vulnerable path.")
    if "sql injection" in category and strategy.kind != "refactor":
        residuals.append("The sink still deserves parameterization at the query execution layer.")
    if "command injection" in category and strategy.kind != "refactor":
        residuals.append("Shell or command construction may remain risky if untrusted input reaches execution.")
    if "ssrf" in category and strategy.kind == "guard":
        residuals.append("Network egress rules or host allowlisting may still be needed deeper in the client layer.")
    if ("auth" in category or "session" in category) and "router" in patch_file.replace("\\", "/"):
        residuals.append("Service or session management logic may still need hardening beyond the router boundary.")
    if "redirect" in category and strategy.kind != "refactor":
        residuals.append("Redirect handling should still be restricted to trusted relative targets or allowlisted hosts.")
    if "nosql" in category and strategy.kind != "refactor":
        residuals.append("The query layer should still enforce typed filters and operator allowlisting.")
    residuals.extend(policy_violations)
    return residuals


def _selection_reason_text(
    category: str,
    strategy: FixStrategyEntity,
    fix_type: str,
    strength: str,
    policy_compliant: bool,
    policy_violations: list[str],
) -> str:
    if not policy_compliant:
        return (
            "This strategy remains below the security policy bar for this vulnerability category: "
            + "; ".join(policy_violations)
        )
    preferred = _preferred_kind(category)
    if strategy.kind == preferred and fix_type == "full_fix":
        return "Selected because it fixes the vulnerability at the sink with the strongest available control for this category."
    if strength == "high":
        return "Selected because it materially changes the risky execution path rather than only screening inputs."
    if fix_type == "temporary_guard":
        return "Selected as a fast fail-safe mitigation, not as the strongest long-term fix."
    return "Selected because it reduces the reachable risk while staying compatible with the current code path."


def _selection_reason(strategy: FixStrategyEntity) -> str:
    return strategy.selection_reason or "Selected because it offers the strongest security improvement with acceptable code impact."


def _non_selection_reason(strategy: FixStrategyEntity, recommended: FixStrategyEntity) -> str:
    if not strategy.policy_compliant:
        return "Not selected because it violates the enforced remediation policy for this vulnerability."
    if strategy.fix_type != "full_fix":
        return "Not selected because it acts as a mitigation rather than a complete sink-level fix."
    if strategy.regression_risk == "high" and recommended.regression_risk != "high":
        return "Not selected because it increases regression risk compared with the recommended strategy."
    return "Not selected because another strategy offered a stronger security improvement for this path."


def _preferred_kind(category: str) -> str:
    if "sql injection" in category or "nosql" in category or "command injection" in category:
        return "refactor"
    if "ssrf" in category:
        return "refactor"
    if "redirect" in category:
        return "sanitization"
    if "auth" in category or "session" in category:
        return "refactor"
    return "refactor"


def _strategy_score(strategy: FixStrategyEntity) -> int:
    compliance_score = 120 if strategy.policy_compliant else -220
    strength_score = {"high": 300, "medium": 200, "low": 100}[strategy.security_strength]
    fix_score = {
        "full_fix": 80,
        "partial_mitigation": 40,
        "temporary_guard": 15,
        "risky_workaround": 0,
    }[strategy.fix_type]
    regression_penalty = {"low": 30, "medium": 10, "high": -20}[strategy.regression_risk]
    impact_score = {"high": 30, "medium": 20, "low": 10}.get(strategy.impact, 10)
    effort_score = {"low": 20, "medium": 10, "high": 0}.get(strategy.effort, 0)
    return compliance_score + strength_score + fix_score + regression_penalty + impact_score + effort_score + strategy.confidence


def _sink_alignment_notes(*, category: str, patch_file: str, finding_file: str) -> list[str]:
    normalized_patch = patch_file.replace("\\", "/").lower()
    normalized_finding = finding_file.replace("\\", "/").lower()
    if not normalized_patch or not normalized_finding or normalized_patch == normalized_finding:
        return []
    if any(token in normalized_patch for token in ("service", "dao", "repo", "query", "db", "auth", "session", "security")):
        return []
    if "sql injection" in category or "command injection" in category or "nosql" in category:
        return ["The recommended patch location is outside the direct sink file and does not clearly move into a trusted execution layer."]
    if "auth" in category or "session" in category:
        return ["The recommended patch location is outside both the traced file and central auth/session modules."]
    return []


def _strategy_sort_key(strategy: FixStrategyEntity) -> tuple[int, int, int, int, int]:
    return (
        1 if strategy.policy_compliant else 0,
        _strategy_score(strategy),
        1 if strategy.fix_type == "full_fix" else 0,
        1 if strategy.security_strength == "high" else 0,
        strategy.confidence,
    )


def _build_patch_validation_notes(*, category: str, strategy: FixStrategyEntity, patch: PatchCandidateEntity) -> list[str]:
    notes = list(patch.validation_notes)
    notes.insert(0, f"Patch classified as {strategy.fix_type.replace('_', ' ')}.")
    if not strategy.policy_compliant:
        notes.append("Security policy enforcement rejected this strategy as a final recommendation for the vulnerability category.")
        notes.extend(strategy.policy_violations)
    notes.append(f"Security strength assessed as {strategy.security_strength}.")
    if strategy.regression_risk == "high":
        notes.append("Regression risk is elevated; careful application-level review is advised.")
    elif strategy.regression_risk == "medium":
        notes.append("Regression risk appears moderate and should be checked in the affected flow.")
    else:
        notes.append("Patch shape appears low-risk for surrounding logic.")

    if "sql injection" in category and strategy.kind != "refactor":
        notes.append("This does not fully replace dynamic query construction with parameterization.")
    if "sql injection" in category and strategy.kind == "refactor":
        notes.append("The patch moves the query path toward parameterization at the sink.")
    if "nosql" in category and strategy.kind == "refactor":
        notes.append("The patch moves the query path toward typed filter construction and operator allowlisting.")
    if "command injection" in category and strategy.kind == "refactor":
        notes.append("The patch moves command execution toward structured argument-based execution instead of shell interpretation.")
    if "command injection" in category and strategy.kind != "refactor":
        notes.append("This does not fully eliminate dangerous command execution semantics at the sink.")
    if "ssrf" in category and strategy.kind == "refactor":
        notes.append("The patch validates destinations with parsed URL and host controls before the outbound client executes.")
    if "ssrf" in category and strategy.kind != "refactor":
        notes.append("This does not fully move SSRF protection into trusted URL validation and outbound client controls.")
    if ("auth" in category or "session" in category) and "router" in patch.file.replace("\\", "/"):
        notes.append("Router-level protection may still leave deeper session or service logic exposed.")
    if ("auth" in category or "session" in category) and strategy.kind == "refactor":
        notes.append("The patch hardens authentication or session state in central logic rather than only at the request boundary.")
    return _merge_unique([], notes)


def _merge_unique(base: list[str], extra: list[str]) -> list[str]:
    merged: list[str] = []
    for item in [*base, *extra]:
        normalized = item.strip()
        if normalized and normalized not in merged:
            merged.append(normalized)
    return merged
