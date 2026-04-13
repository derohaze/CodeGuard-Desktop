from dataclasses import dataclass, field
from typing import Literal


PatchApplyStatus = Literal["applied", "rejected", "validation_failed", "rolled_back"]
FixType = Literal["full_fix", "partial_mitigation", "temporary_guard", "risky_workaround"]
VerificationStatus = Literal["verified", "manual_review_required", "not_run", "rolled_back"]
ApprovalGateOutcome = Literal["auto-approved", "review-required", "blocked-by-policy"]


@dataclass(slots=True)
class PatchApplicationEntity:
    finding_id: str
    status: PatchApplyStatus
    file: str
    applied_strategy_id: str | None = None
    fix_type: FixType = "full_fix"
    validation_notes: list[str] = field(default_factory=list)
    manual_edit_applied: bool = False
    checkpoint_id: str | None = None
    rollback_available: bool = False
    verification_status: VerificationStatus = "not_run"
    verification_notes: list[str] = field(default_factory=list)
    verification_confidence: int | None = None
    verification_confidence_valid: bool = False
    approval_gate_outcome: ApprovalGateOutcome = "auto-approved"
    approval_gate_reason: str = ""
    write_scope: str = ""
    network_policy: str = ""
