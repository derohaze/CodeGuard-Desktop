from dataclasses import dataclass, field
from typing import Literal


RemediationMode = Literal["single", "batch"]
FixStrategyKind = Literal["refactor", "guard", "sanitization"]


@dataclass(slots=True)
class ExplanationEntity:
    finding_id: str
    summary: str
    exploit_scenario: str
    request_example: str
    payload_example: str
    attack_steps: list[str] = field(default_factory=list)
    entry_point: str = ""
    execution_path: str = ""
    sink: str = ""
    impact: str = ""


@dataclass(slots=True)
class FixStrategyEntity:
    id: str
    label: str
    kind: FixStrategyKind
    confidence: int
    impact: str
    effort: str
    summary: str
    rationale: str
    diff: str = ""
    recommended: bool = False
    fix_type: Literal["full_fix", "partial_mitigation", "temporary_guard", "risky_workaround"] = "partial_mitigation"
    security_strength: Literal["high", "medium", "low"] = "medium"
    regression_risk: Literal["low", "medium", "high"] = "medium"
    selection_reason: str = ""
    non_selection_reason: str = ""
    residual_risks: list[str] = field(default_factory=list)
    policy_compliant: bool = True
    policy_violations: list[str] = field(default_factory=list)


@dataclass(slots=True)
class PatchCandidateEntity:
    file: str
    language: str
    summary: str
    diff: str
    validation_notes: list[str] = field(default_factory=list)
    before_snippet: str = ""
    after_snippet: str = ""
    fix_type: Literal["full_fix", "partial_mitigation", "temporary_guard", "risky_workaround"] = "partial_mitigation"
    rationale: str = ""
    residual_risks: list[str] = field(default_factory=list)
    manual_review_required: bool = False


@dataclass(slots=True)
class RemediationStepEntity:
    id: str
    title: str
    status: Literal["done", "running", "pending"]
    agent: str
    model: str
    details: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RemediationMetricsEntity:
    file: str
    vulnerability_type: str
    remediation_mode: RemediationMode
    analyzed_lines: int
    path_steps: int
    evidence_location: str


@dataclass(slots=True)
class RemediationScoreEntity:
    total: int
    strategy_quality: int
    fix_completeness: int
    sink_alignment: int
    residual_risk: int
    confidence: int
    rationale: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RemediationPlanEntity:
    mode: RemediationMode
    finding_ids: list[str]
    review_summary: str
    explanation: ExplanationEntity | None = None
    strategies: list[FixStrategyEntity] = field(default_factory=list)
    recommended_strategy_id: str | None = None
    patch: PatchCandidateEntity | None = None
    steps: list[RemediationStepEntity] = field(default_factory=list)
    metrics: RemediationMetricsEntity | None = None
    score: RemediationScoreEntity | None = None
