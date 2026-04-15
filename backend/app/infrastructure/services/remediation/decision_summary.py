from __future__ import annotations

from typing import Literal

from app.domain.entities.scan import FindingEntity


_IDENTITY_TOKENS = ("auth", "authentication", "authorization", "session", "privilege")


def build_finding_decision_summary(finding: FindingEntity) -> dict:
    category = finding.category.lower()
    touches_identity = any(token in category for token in _IDENTITY_TOKENS)
    risk_score = calculate_finding_risk_score(finding, touches_identity)
    safe_auto_path = is_safe_auto_path(finding, touches_identity, risk_score)
    approval_status = get_approval_status(finding)

    return {
        "validation_label": "Validated finding",
        "validation_note": "This issue is already in the validated findings set, not just a candidate signal.",
        "risk_score": risk_score,
        "risk_label": "Immediate attention" if risk_score >= 85 else "Needs remediation" if risk_score >= 65 else "Review and schedule",
        "triage_band": build_triage_band(finding, risk_score, touches_identity),
        "triage_rank": build_triage_rank(finding, risk_score, touches_identity),
        "execution_disposition": build_execution_disposition(finding, touches_identity),
        "approval_state": build_approval_state(finding, touches_identity),
        "policy_outcome": build_policy_outcome(finding, risk_score, touches_identity, safe_auto_path),
        "policy_reason": build_policy_reason(finding, risk_score, touches_identity, safe_auto_path),
        "stop_state": build_stop_state(finding),
        "apply_readiness": build_apply_readiness(finding, touches_identity, risk_score),
        "escalation_state": build_escalation_state(finding, touches_identity, risk_score),
        "policy_summary": build_policy_summary(finding, touches_identity, risk_score, safe_auto_path),
        "residual_risk_state": build_residual_risk_state(finding),
        "recommended_action": build_recommended_action(finding),
        "fix_recommendation": build_fix_recommendation(category),
        "approval_path": build_approval_path(finding, touches_identity),
        "approval_audit_summary": build_approval_audit_summary(finding, approval_status),
        "risk_factors": build_risk_factors(finding, touches_identity),
    }


def calculate_finding_risk_score(finding: FindingEntity, touches_identity: bool) -> int:
    severity_base = {
        "critical": 92,
        "high": 78,
        "medium": 58,
        "low": 36,
    }[finding.severity]
    confidence_adjustment = round((finding.confidence - 70) / 4)
    lifecycle_adjustment = (
        6
        if finding.remediation_status == "validation_failed"
        else 4
        if finding.remediation_status == "verified_partial"
        else -22
        if finding.remediation_status == "verified_fixed"
        else 0
    )
    identity_adjustment = 8 if touches_identity else 0
    return clamp(severity_base + confidence_adjustment + lifecycle_adjustment + identity_adjustment, 0, 100)


def append_approval_history(finding: FindingEntity, status: str, note: str, *, timestamp: str) -> None:
    if finding.approval_history:
        latest = finding.approval_history[-1]
        if latest.get("status") == status and latest.get("note") == note:
            latest["timestamp"] = timestamp
            finding.approval_status = status
            return
    finding.approval_history.append({"status": status, "note": note, "timestamp": timestamp})
    finding.approval_status = status


def determine_apply_gate(
    finding: FindingEntity,
    *,
    verification_status: Literal["verified", "manual_review_required", "not_run", "rolled_back"] = "not_run",
) -> tuple[str, str]:
    summary = build_finding_decision_summary(finding)
    if verification_status == "manual_review_required":
        return (
            "review-required",
            "The workspace patch was applied, but deterministic verification still requires human review before closure.",
        )
    if summary["policy_outcome"] == "blocked-by-policy":
        return ("blocked-by-policy", str(summary["policy_reason"]))
    if summary["policy_outcome"] == "review-required":
        return ("review-required", str(summary["policy_reason"]))
    return ("auto-approved", "The applied patch remains eligible for the normal low-risk remediation flow.")


def get_approval_status(finding: FindingEntity) -> str:
    return finding.approval_status or "not_required"


def is_safe_auto_path(finding: FindingEntity, touches_identity: bool, risk_score: int) -> bool:
    return (
        not touches_identity
        and finding.severity not in {"critical", "high"}
        and risk_score < 85
        and finding.remediation_status not in {"verified_partial", "patch_generated", "validation_failed", "rejected", "rolled_back"}
    )


def build_policy_outcome(finding: FindingEntity, risk_score: int, touches_identity: bool, safe_auto_path: bool) -> str:
    approval_status = get_approval_status(finding)
    if finding.remediation_status == "validation_failed":
        return "blocked-by-policy"
    if approval_status == "approved" and finding.remediation_status != "verified_partial" and safe_auto_path:
        return "auto-eligible"
    if (
        touches_identity
        or finding.remediation_status in {"verified_partial", "patch_generated", "rejected", "rolled_back"}
        or finding.severity in {"critical", "high"}
        or risk_score >= 85
    ):
        return "review-required"
    return "auto-eligible"


def build_policy_reason(finding: FindingEntity, risk_score: int, touches_identity: bool, safe_auto_path: bool) -> str:
    approval_status = get_approval_status(finding)
    if finding.remediation_status == "validation_failed":
        return "The last remediation attempt was blocked by a safety boundary, so this path cannot proceed without a stronger patch."
    if approval_status == "approved" and finding.remediation_status != "verified_partial" and safe_auto_path:
        return "This remediation path already has an explicit approval record, so workspace apply can proceed within the current review session."
    if approval_status == "approved" and finding.remediation_status != "verified_partial" and not safe_auto_path:
        return "Approval is recorded for this remediation path, but policy still keeps it on a human-controlled review track because the decision pressure remains too high for autonomous progression."
    if touches_identity:
        return "This finding touches identity, session, or authorization logic, so policy requires human review before closure."
    if finding.remediation_status == "verified_partial":
        return "A workspace patch exists, but policy still requires verification review before final closure."
    if finding.remediation_status == "patch_generated":
        return "A patch is ready, but policy still requires explicit review before workspace apply."
    if finding.severity in {"critical", "high"} or risk_score >= 85:
        return "This finding has enough decision pressure that policy requires human review before broader rollout."
    return "This finding is localized enough to stay eligible for the normal remediation flow."


def build_policy_summary(finding: FindingEntity, touches_identity: bool, risk_score: int, safe_auto_path: bool) -> dict:
    approval_status = get_approval_status(finding)
    policy_outcome = build_policy_outcome(finding, risk_score, touches_identity, safe_auto_path)
    if policy_outcome == "blocked-by-policy":
        return {
            "posture": "block",
            "label": "Blocked by policy",
            "summary": "The current remediation path cannot proceed because policy requires a stronger or safer patch.",
            "auto_path_state": "forbidden",
            "human_path_state": "regenerate-required",
            "next_control": "generate-a-stronger-patch",
        }
    if approval_status == "approved" and finding.remediation_status != "verified_partial":
        return {
            "posture": "allow" if safe_auto_path else "review",
            "label": "Approved within policy" if safe_auto_path else "Approved but still human-controlled",
            "summary": (
                "Policy allows this remediation path to proceed because the required approval is already recorded."
                if safe_auto_path
                else "Approval is recorded, but policy still keeps this remediation path on a human-controlled track because the remaining decision pressure is too high for autonomous progression."
            ),
            "auto_path_state": "eligible" if safe_auto_path else "gated",
            "human_path_state": "approved-review-cycle",
            "next_control": "proceed-with-local-apply",
        }
    if approval_status == "escalated":
        return {
            "posture": "review",
            "label": "Escalated policy review",
            "summary": "Policy keeps this remediation path in escalated review until the higher-risk decision is resolved.",
            "auto_path_state": "gated",
            "human_path_state": "escalated-review",
            "next_control": "resolve-escalation",
        }
    if policy_outcome == "review-required":
        return {
            "posture": "review",
            "label": "Review-controlled path",
            "summary": "Policy allows remediation to continue only through an explicit human-controlled review path.",
            "auto_path_state": "gated",
            "human_path_state": "approval-required",
            "next_control": "collect-approval",
        }
    return {
        "posture": "allow",
        "label": "Standard policy flow",
        "summary": "Policy allows this remediation path to stay on the standard low-risk flow after patch review.",
        "auto_path_state": "eligible",
        "human_path_state": "standard-review",
        "next_control": "continue-standard-review",
    }


def build_triage_band(finding: FindingEntity, risk_score: int, touches_identity: bool) -> str:
    if finding.remediation_status == "verified_fixed":
        return "Resolved locally"
    if finding.remediation_status == "verified_partial":
        return "Review before closure" if touches_identity else "Verification follow-up"
    if finding.remediation_status == "validation_failed":
        return "Blocked remediation"
    if touches_identity or finding.severity == "critical" or risk_score >= 85:
        return "Priority 1"
    if finding.severity == "high" or risk_score >= 65:
        return "Priority 2"
    return "Priority 3"


def build_triage_rank(finding: FindingEntity, risk_score: int, touches_identity: bool) -> int:
    if finding.remediation_status == "validation_failed":
        return 1
    if finding.remediation_status == "verified_partial":
        return 2 if touches_identity else 3
    if touches_identity and finding.remediation_status in {"open", "patch_generated"}:
        return 2
    if finding.remediation_status == "patch_generated":
        return 3
    if finding.severity == "critical" or risk_score >= 85:
        return 4
    if finding.severity == "high" or risk_score >= 65:
        return 5
    if finding.remediation_status == "verified_fixed":
        return 7
    return 6


def build_execution_disposition(finding: FindingEntity, touches_identity: bool) -> str:
    if finding.remediation_status == "verified_fixed":
        return "Re-scan before repository closure"
    if finding.remediation_status == "verified_partial":
        return "Do not auto-close; verification follow-up required"
    if finding.remediation_status == "validation_failed":
        return "Blocked pending stronger patch"
    if finding.remediation_status == "patch_generated":
        return "Review patch before any apply" if touches_identity else "Patch review in progress"
    if touches_identity:
        return "Do not auto-apply without approval"
    return "Eligible for remediation planning"


def build_approval_state(finding: FindingEntity, touches_identity: bool) -> str:
    approval_status = get_approval_status(finding)
    if approval_status == "approved" and finding.remediation_status == "patch_generated":
        return "Approved for workspace apply"
    if approval_status == "rejected":
        return "Rejected during approval review"
    if approval_status == "escalated":
        return "Escalated review"
    if finding.remediation_status == "verified_fixed":
        return "Not required for local closure"
    if touches_identity:
        return "Approval required"
    if finding.remediation_status == "verified_partial":
        return "Verification review required"
    if finding.severity in {"critical", "high"}:
        return "Human review required"
    return "Standard review"


def build_residual_risk_state(finding: FindingEntity) -> str:
    return {
        "verified_fixed": "Reduced in patched file; repository confirmation still pending",
        "verified_partial": "Residual risk remains until follow-up verification closes the path",
        "validation_failed": "Risk unchanged because no patch was applied",
        "rejected": "Risk unchanged because the proposed remediation was rejected",
        "rolled_back": "Risk restored to the pre-patch state",
    }.get(finding.remediation_status, "Risk remains active until a verified remediation is applied")


def build_stop_state(finding: FindingEntity) -> str:
    approval_status = get_approval_status(finding)
    if finding.remediation_status == "verified_fixed":
        return "ready-for-closure-review"
    if finding.remediation_status in {"validation_failed", "rejected", "rolled_back"}:
        return "stop-and-regenerate"
    if finding.remediation_status == "verified_partial" or approval_status == "escalated":
        return "hold-for-review"
    return "continue-remediation"


def build_apply_readiness(finding: FindingEntity, touches_identity: bool, risk_score: int) -> str:
    approval_status = get_approval_status(finding)
    if finding.remediation_status == "validation_failed":
        return "blocked-before-apply"
    if approval_status == "approved":
        return "local-apply-eligible"
    if (
        touches_identity
        or finding.remediation_status in {"patch_generated", "verified_partial"}
        or finding.severity in {"critical", "high"}
        or risk_score >= 85
    ):
        return "approval-required-before-apply"
    return "local-apply-eligible"


def build_escalation_state(finding: FindingEntity, touches_identity: bool, risk_score: int) -> str:
    approval_status = get_approval_status(finding)
    if approval_status == "escalated":
        return "already-escalated"
    if touches_identity or finding.remediation_status == "verified_partial" or risk_score >= 85:
        return "required"
    return "none"


def build_recommended_action(finding: FindingEntity) -> str:
    return {
        "patch_generated": "Review the proposed patch and approve it only if it matches the traced sink and the required security strategy.",
        "verified_fixed": "Treat the patched file as fixed, then re-run the broader analysis before closing repository-level risk.",
        "verified_partial": "Keep the finding open until follow-up verification or a stronger patch confirms the vulnerable path is fully closed.",
        "validation_failed": "Generate another remediation or edit the patch manually; the previous apply attempt was blocked safely.",
        "rejected": "The issue is still open. Generate a different remediation path or handle the fix manually.",
        "rolled_back": "A previous patch was rolled back. Review another remediation path before applying changes again.",
    }.get(
        finding.remediation_status,
        "Generate a remediation plan, review the patch, and apply it only after confirming the path and sink match the real finding.",
    )


def build_fix_recommendation(category: str) -> str:
    if "sql injection" in category:
        return "Prefer sink-level parameterization over input screening."
    if "nosql" in category:
        return "Prefer typed filter construction or operator allowlisting over generic sanitization."
    if "command injection" in category:
        return "Prefer structured argv execution with shell disabled."
    if "ssrf" in category or "server-side request forgery" in category:
        return "Prefer trusted destination validation and outbound client controls at the request boundary."
    if "path traversal" in category:
        return "Prefer canonical path containment checks against a trusted base directory."
    if "open redirect" in category:
        return "Prefer relative-only redirects or an explicit destination allowlist."
    if "session" in category:
        return "Prefer session rotation and invalidation in the auth transition itself, not only cookie hardening."
    if "auth" in category or "authorization" in category or "privilege" in category:
        return "Prefer a structural fix in the central auth or authorization path, not a local workaround."
    return "Prefer a code-level fix at the real trust boundary or sink instead of an early-path workaround."


def build_approval_path(finding: FindingEntity, touches_identity: bool) -> str:
    if touches_identity:
        return "Human approval is required for rollout because this finding touches identity or access-control behavior."
    if finding.severity in {"critical", "high"}:
        return "Human review is required before broader rollout. Workspace apply can proceed after patch review, but export or PR should still be reviewed."
    return "Workspace apply is eligible after patch review. Broader rollout should still be reviewed before merging."


def build_approval_audit_summary(finding: FindingEntity, approval_status: str) -> dict:
    latest_entry = finding.approval_history[-1] if finding.approval_history else None
    return {
        "status": approval_status,
        "label": (
            "No approval gate"
            if approval_status == "not_required"
            else "Approval pending"
            if approval_status == "pending"
            else "Approval resolved"
            if approval_status == "approved"
            else "Approval rejected"
            if approval_status == "rejected"
            else "Escalated review"
        ),
        "summary": (
            "This remediation path does not currently require a stored approval decision."
            if approval_status == "not_required"
            else "This remediation path is waiting for an approval decision before workspace apply can proceed."
            if approval_status == "pending"
            else "This remediation path has a stored approval decision and can proceed within the current review cycle."
            if approval_status == "approved"
            else "The last approval decision rejected this remediation path, so a different patch or a renewed review is required."
            if approval_status == "rejected"
            else "This remediation path is held in escalated review and cannot proceed until that review is resolved."
        ),
        "note": latest_entry.get("note") if latest_entry else (
            "No approval note is required for the current remediation path."
            if approval_status == "not_required"
            else "Waiting for an explicit approval decision."
            if approval_status == "pending"
            else "The remediation path was approved for the current review cycle."
            if approval_status == "approved"
            else "The remediation path was rejected during approval review."
            if approval_status == "rejected"
            else "The remediation path remains under escalated review."
        ),
        "timestamp": latest_entry.get("timestamp") if latest_entry else None,
        "resolution_category": (
            "not-required"
            if approval_status == "not_required"
            else "awaiting-review"
            if approval_status == "pending"
            else "resolved"
            if approval_status == "approved"
            else "rejected"
            if approval_status == "rejected"
            else "held"
        ),
        "source": (
            "policy-default"
            if approval_status == "not_required"
            else "approval-controller"
            if approval_status in {"approved", "rejected", "escalated"}
            else "approval-queue"
        ),
    }


def build_risk_factors(finding: FindingEntity, touches_identity: bool) -> list[str]:
    factors = [f"{capitalize(finding.severity)} severity with {finding.confidence}% model confidence.", finding.impact]
    if touches_identity:
        factors.append("The issue touches identity, session, or authorization logic, which raises rollout risk.")
    elif finding.remediation_status in {"verified_partial", "validation_failed"}:
        factors.append("The current remediation state is incomplete, so the issue should stay open until a stronger result is confirmed.")
    else:
        factors.append("The finding is still tied to a concrete source-to-sink path in the validated analysis result.")
    return factors


def clamp(value: int, minimum: int, maximum: int) -> int:
    return min(maximum, max(minimum, value))


def capitalize(value: str) -> str:
    return value[:1].upper() + value[1:]
