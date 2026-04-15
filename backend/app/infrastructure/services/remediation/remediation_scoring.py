from __future__ import annotations

from app.domain.entities.remediation import FixStrategyEntity, PatchCandidateEntity, RemediationScoreEntity
from app.infrastructure.services.remediation.remediation_policy import category_requires_full_fix, normalize_category


def score_remediation(
    *,
    finding: dict,
    strategy: FixStrategyEntity | None,
    patch: PatchCandidateEntity | None,
) -> RemediationScoreEntity:
    if strategy is None or patch is None:
        return RemediationScoreEntity(
            total=0,
            strategy_quality=0,
            fix_completeness=0,
            sink_alignment=0,
            residual_risk=0,
            confidence=0,
            rationale=["No remediation strategy or patch candidate was available for scoring."],
        )

    category = normalize_category(str(finding.get("category", "")))
    patch_file = patch.file.replace("\\", "/").lower()
    finding_file = str(finding.get("file", "")).replace("\\", "/").lower()

    strategy_quality = _score_strategy_quality(category, strategy)
    fix_completeness = _score_fix_completeness(category, strategy)
    sink_alignment = _score_sink_alignment(category, patch_file, finding_file)
    residual_risk = _score_residual_risk(strategy, patch)
    confidence = max(0, min(100, strategy.confidence))

    total = round(
        (strategy_quality * 0.3)
        + (fix_completeness * 0.28)
        + (sink_alignment * 0.18)
        + (residual_risk * 0.12)
        + (confidence * 0.12)
    )
    total, strategy_quality, fix_completeness = _apply_hard_enforcement_caps(
        category=category,
        strategy=strategy,
        total=total,
        strategy_quality=strategy_quality,
        fix_completeness=fix_completeness,
    )
    rationale = _build_rationale(
        category=category,
        strategy=strategy,
        patch=patch,
        strategy_quality=strategy_quality,
        fix_completeness=fix_completeness,
        sink_alignment=sink_alignment,
        residual_risk=residual_risk,
    )
    return RemediationScoreEntity(
        total=max(0, min(100, total)),
        strategy_quality=strategy_quality,
        fix_completeness=fix_completeness,
        sink_alignment=sink_alignment,
        residual_risk=residual_risk,
        confidence=confidence,
        rationale=rationale,
    )


def _score_strategy_quality(category: str, strategy: FixStrategyEntity) -> int:
    base = {"high": 88, "medium": 64, "low": 34}[strategy.security_strength]
    if not strategy.policy_compliant:
        base -= 40
    preferred_kind = _preferred_kind(category)
    if strategy.kind == preferred_kind:
        base += 8
    else:
        base -= 18

    if "sql injection" in category and strategy.kind != "refactor":
        base -= 32
    if "command injection" in category and strategy.kind != "refactor":
        base -= 30
    if ("auth" in category or "session" in category) and strategy.kind == "guard":
        base -= 28
    if "open redirect" in category and strategy.kind != "sanitization":
        base -= 16
    return _clamp(base)


def _score_fix_completeness(category: str, strategy: FixStrategyEntity) -> int:
    score = {
        "full_fix": 95,
        "partial_mitigation": 58,
        "temporary_guard": 26,
        "risky_workaround": 8,
    }[strategy.fix_type]
    if not strategy.policy_compliant:
        score -= 28
    if "sql injection" in category and strategy.kind != "refactor":
        score -= 26
    if "command injection" in category and strategy.kind != "refactor":
        score -= 24
    if ("auth" in category or "session" in category) and "router" in " ".join(strategy.residual_risks).lower():
        score -= 18
    if "open redirect" in category and strategy.fix_type == "partial_mitigation":
        score -= 12
    return _clamp(score)


def _score_sink_alignment(category: str, patch_file: str, finding_file: str) -> int:
    if patch_file == finding_file:
        return 100
    if any(token in patch_file for token in ("service", "dao", "repo", "query", "db", "helper")):
        return 90
    if ("auth" in category or "session" in category) and any(token in patch_file for token in ("auth", "security", "session")):
        return 92
    return 56


def _score_residual_risk(strategy: FixStrategyEntity, patch: PatchCandidateEntity) -> int:
    notes = " ".join(patch.validation_notes).lower()
    residuals = patch.residual_risks or strategy.residual_risks
    if strategy.fix_type == "full_fix" and any("no residual" in item.lower() or "fully mitigates" in item.lower() for item in residuals):
        return 94
    if residuals and patch.manual_review_required:
        return 86
    if residuals:
        return 78
    if "manual review" in notes:
        return 68
    return 40


def _build_rationale(
    *,
    category: str,
    strategy: FixStrategyEntity,
    patch: PatchCandidateEntity,
    strategy_quality: int,
    fix_completeness: int,
    sink_alignment: int,
    residual_risk: int,
) -> list[str]:
    rationale = [
        f"Strategy quality scored {strategy_quality}/100 based on vulnerability-specific best-practice fit.",
        f"Fix completeness scored {fix_completeness}/100 from the classified remediation type ({strategy.fix_type.replace('_', ' ')}).",
        f"Sink alignment scored {sink_alignment}/100 based on where the patch is applied relative to the traced finding.",
        f"Residual-risk handling scored {residual_risk}/100 from the clarity of remaining-risk notes.",
    ]
    if not strategy.policy_compliant:
        rationale.append("Hard enforcement downgraded this remediation because it violates the required security strategy for the vulnerability category.")
        rationale.extend(strategy.policy_violations)
    if "sql injection" in category and strategy.kind != "refactor":
        rationale.append("Penalty applied because SQL injection remediation should prefer sink-level parameterization over screening-only fixes.")
    if "command injection" in category and strategy.kind != "refactor":
        rationale.append("Penalty applied because command injection remediation should replace unsafe execution semantics, not only filter input.")
    if ("auth" in category or "session" in category) and strategy.kind == "guard":
        rationale.append("Penalty applied because route-level guards are weaker than fixing auth/session verification logic directly.")
    if strategy.fix_type == "full_fix":
        rationale.append("Boost applied because the strategy is classified as a full fix rather than a mitigation.")
    return rationale


def _preferred_kind(category: str) -> str:
    if "sql injection" in category or "command injection" in category or "nosql" in category:
        return "refactor"
    if "open redirect" in category or "ssrf" in category:
        return "sanitization"
    if "auth" in category or "session" in category:
        return "refactor"
    return "refactor"


def _clamp(value: int) -> int:
    return max(0, min(100, value))


def _apply_hard_enforcement_caps(
    *,
    category: str,
    strategy: FixStrategyEntity,
    total: int,
    strategy_quality: int,
    fix_completeness: int,
) -> tuple[int, int, int]:
    if not strategy.policy_compliant:
        total = min(total, 54)
        strategy_quality = min(strategy_quality, 44)
        fix_completeness = min(fix_completeness, 34)
    if category_requires_full_fix(category) and strategy.fix_type != "full_fix":
        total = min(total, 59)
        fix_completeness = min(fix_completeness, 39)
    return total, strategy_quality, fix_completeness
