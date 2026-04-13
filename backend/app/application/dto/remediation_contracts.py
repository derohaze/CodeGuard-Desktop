from typing import Literal

from pydantic import BaseModel, Field
from app.application.dto.scan_contracts import FindingResponse, SessionSummaryResponse


class ExplainFindingRequest(BaseModel):
    session_id: str = Field(min_length=1)
    finding_id: str = Field(min_length=1)


class GenerateFixRequest(BaseModel):
    session_id: str = Field(min_length=1)
    finding_id: str = Field(min_length=1)


class GenerateBatchRemediationRequest(BaseModel):
    session_id: str = Field(min_length=1)


class ApplyFixRequest(BaseModel):
    session_id: str = Field(min_length=1)
    finding_id: str = Field(min_length=1)
    strategy_id: str | None = None
    file: str = Field(min_length=1)
    before_snippet: str = ""
    after_snippet: str = ""
    diff: str = ""
    manual_edit: bool = False
    approval_acknowledged: bool = False
    mode: Literal["single", "batch"] = "single"


class RollbackFixRequest(BaseModel):
    session_id: str = Field(min_length=1)
    finding_id: str = Field(min_length=1)
    checkpoint_id: str | None = None


class RejectFixRequest(BaseModel):
    session_id: str = Field(min_length=1)
    finding_id: str = Field(min_length=1)
    strategy_id: str | None = None


class RetryFixStrategyRequest(BaseModel):
    session_id: str = Field(min_length=1)
    finding_id: str = Field(min_length=1)
    mode: Literal["single", "batch"] = "single"
    excluded_strategy_ids: list[str] = Field(default_factory=list)
    attempted_strategy_ids: list[str] = Field(default_factory=list)


class ExplanationResponse(BaseModel):
    finding_id: str
    summary: str
    exploit_scenario: str
    request_example: str
    payload_example: str
    attack_steps: list[str]
    entry_point: str
    execution_path: str
    sink: str
    impact: str


class FixStrategyResponse(BaseModel):
    id: str
    label: str
    kind: Literal["refactor", "guard", "sanitization"]
    confidence: int
    impact: str
    effort: str
    summary: str
    rationale: str
    diff: str
    recommended: bool = False
    fix_type: Literal["full_fix", "partial_mitigation", "temporary_guard", "risky_workaround"] = "partial_mitigation"
    security_strength: Literal["high", "medium", "low"] = "medium"
    regression_risk: Literal["low", "medium", "high"] = "medium"
    selection_reason: str = ""
    non_selection_reason: str = ""
    residual_risks: list[str] = Field(default_factory=list)
    policy_compliant: bool = True
    policy_violations: list[str] = Field(default_factory=list)


class PatchCandidateResponse(BaseModel):
    file: str
    language: str
    summary: str
    diff: str
    validation_notes: list[str]
    before_snippet: str
    after_snippet: str
    fix_type: Literal["full_fix", "partial_mitigation", "temporary_guard", "risky_workaround"] = "partial_mitigation"
    rationale: str = ""
    residual_risks: list[str] = Field(default_factory=list)
    manual_review_required: bool = False


class RemediationStepResponse(BaseModel):
    id: str
    title: str
    status: Literal["done", "running", "pending"]
    agent: str
    details: list[str] = Field(default_factory=list)


class RemediationMetricsResponse(BaseModel):
    file: str
    vulnerability_type: str
    remediation_mode: Literal["single", "batch"]
    analyzed_lines: int
    path_steps: int
    evidence_location: str


class RemediationScoreResponse(BaseModel):
    total: int
    strategy_quality: int
    fix_completeness: int
    sink_alignment: int
    residual_risk: int
    confidence: int
    rationale: list[str] = Field(default_factory=list)


class PatchApplicationResponse(BaseModel):
    finding_id: str
    status: Literal["applied", "rejected", "validation_failed", "rolled_back"]
    file: str
    applied_strategy_id: str | None = None
    fix_type: Literal["full_fix", "partial_mitigation", "temporary_guard", "risky_workaround"] = "full_fix"
    validation_notes: list[str] = Field(default_factory=list)
    manual_edit_applied: bool = False
    checkpoint_id: str | None = None
    rollback_available: bool = False
    verification_status: Literal["verified", "manual_review_required", "not_run", "rolled_back"] = "not_run"
    verification_notes: list[str] = Field(default_factory=list)
    verification_confidence: int | None = None
    verification_confidence_valid: bool = False
    approval_gate_outcome: Literal["auto-approved", "review-required", "blocked-by-policy"] = "auto-approved"
    approval_gate_reason: str = ""
    write_scope: str = ""
    network_policy: str = ""


class RemediationPlanResponse(BaseModel):
    mode: Literal["single", "batch"]
    finding_ids: list[str]
    review_summary: str
    explanation: ExplanationResponse | None = None
    strategies: list[FixStrategyResponse] = Field(default_factory=list)
    recommended_strategy_id: str | None = None
    patch: PatchCandidateResponse | None = None
    steps: list[RemediationStepResponse] = Field(default_factory=list)
    metrics: RemediationMetricsResponse | None = None
    score: RemediationScoreResponse | None = None


class RemediationExecutionResponse(BaseModel):
    action: PatchApplicationResponse
    session: SessionSummaryResponse
    findings: list[FindingResponse] = Field(default_factory=list)
    candidate_findings: list[FindingResponse] = Field(default_factory=list)
