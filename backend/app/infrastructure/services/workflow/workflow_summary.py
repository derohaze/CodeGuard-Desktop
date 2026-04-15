from __future__ import annotations

from app.domain.entities.scan import ScanSessionEntity


def build_workflow_summary(session: ScanSessionEntity) -> dict | None:
    if session.status == "queued":
        return _build_summary(
            state="scanning",
            label="Queued analysis",
            summary="The repository analysis is queued and waiting for execution.",
            next_action="Wait for scan execution to start.",
            active_controller="executor",
            planner_stage=None,
            session=session,
        )
    if session.status == "scanning":
        return _build_summary(
            state="scanning",
            label="Scan execution",
            summary=session.progress_message or "The repository analysis is still running.",
            next_action="Wait for analysis to complete before remediation review.",
            active_controller="executor",
            planner_stage="triage",
            session=session,
        )
    if session.status == "failed":
        return _build_summary(
            state="failed",
            label="Workflow failed",
            summary=session.error_message or "The analysis workflow failed before the repository state could be closed.",
            next_action="Inspect the failure and rerun the scan before continuing remediation.",
            active_controller="state-manager",
            planner_stage=None,
            session=session,
        )

    findings = list(session.findings)
    open_findings = [item for item in findings if item.remediation_status != "verified_fixed"]
    patch_generated = [item for item in findings if item.remediation_status == "patch_generated"]
    partial_findings = [item for item in findings if item.remediation_status == "verified_partial"]
    blocked_findings = [item for item in findings if item.remediation_status in {"validation_failed", "rejected", "rolled_back"}]
    pending_approval = [item for item in findings if item.approval_status in {"pending", "escalated"}]

    if partial_findings or blocked_findings:
        return _build_summary(
            state="verification-follow-up",
            label="Verification and recovery follow-up",
            summary="Applied or attempted remediations still require verification review or recovery decisions before closure.",
            next_action="Review verification output or regenerate a stronger patch.",
            active_controller="recovery-controller" if blocked_findings else "verification-controller",
            planner_stage="patch-planning",
            session=session,
        )
    if pending_approval or patch_generated:
        return _build_summary(
            state="approval-control" if pending_approval else "remediation-review",
            label="Review-controlled remediation",
            summary="Validated findings are in patch review or approval control before workspace apply can close the path.",
            next_action="Review queued items and approve or revise the current remediation path.",
            active_controller="approval-controller" if pending_approval else "planner",
            planner_stage="apply-ready",
            session=session,
        )
    if open_findings:
        return _build_summary(
            state="decisioning",
            label="Decision and triage",
            summary="Validated findings remain open and the workflow is still in the decision and remediation planning lane.",
            next_action="Open a finding, generate a remediation plan, and continue review.",
            active_controller="planner",
            planner_stage="patch-planning",
            session=session,
        )
    return _build_summary(
        state="completed",
        label="Workflow closed",
        summary="No validated finding currently remains open in this saved analysis session.",
        next_action="Re-run the scan after future code changes to confirm repository posture remains stable.",
        active_controller="state-manager",
        planner_stage=None,
        session=session,
    )


def _build_summary(
    *,
    state: str,
    label: str,
    summary: str,
    next_action: str,
    active_controller: str,
    planner_stage: str | None,
    session: ScanSessionEntity,
) -> dict:
    recovery_summary = _build_recovery_summary(session)
    operations_summary = _build_operations_summary(state, session)
    return {
        "state": state,
        "label": label,
        "summary": summary,
        "next_action": next_action,
        "active_controller": active_controller,
        "planner_stage": planner_stage,
        "recovery_summary": recovery_summary,
        "recovery_execution": _build_recovery_execution(recovery_summary),
        "memory_summary": _build_memory_summary(session),
        "operations_summary": operations_summary,
        "operations_execution": _build_operations_execution(state, active_controller, operations_summary),
        "workflow_closure": _build_workflow_closure(state, session),
        "blocking_items": (
            len([item for item in session.findings if item.approval_status in {"pending", "escalated"}])
            + len([item for item in session.findings if item.remediation_status == "verified_partial"])
            + len([item for item in session.findings if item.remediation_status in {"validation_failed", "rejected", "rolled_back"}])
        ),
    }


def _build_recovery_summary(session: ScanSessionEntity) -> dict | None:
    retryable = [item for item in session.findings if item.remediation_status in {"verified_partial", "validation_failed", "rejected", "rolled_back"}]
    if not retryable and session.status == "completed":
        return {
            "retry_available": False,
            "retryable_findings": 0,
            "attempted_strategies": sum(len(item.attempted_strategy_ids) for item in session.findings),
            "latest_failure_reason": "",
            "last_verification_status": str((session.last_verification or {}).get("status") or "") or None,
            "recovery_state": "stable",
            "next_transition": "none",
            "controller_status": "closed",
            "planner_reentry_ready": False,
        }
    if not retryable:
        return None
    latest_failure_reason = ""
    for finding in retryable:
        if finding.remediation_notes:
            latest_failure_reason = finding.remediation_notes[-1]
            break
    has_partial = any(item.remediation_status == "verified_partial" for item in retryable)
    has_blocked = any(item.remediation_status in {"validation_failed", "rejected", "rolled_back"} for item in retryable)
    return {
        "retry_available": True,
        "retryable_findings": len(retryable),
        "attempted_strategies": sum(len(item.attempted_strategy_ids) for item in retryable),
        "latest_failure_reason": latest_failure_reason,
        "last_verification_status": str((session.last_verification or {}).get("status") or "") or None,
        "recovery_state": "planner-reentry" if has_partial else "manual-fallback" if has_blocked else "retry-ready",
        "next_transition": "return-to-planner" if has_partial else "retry-remediation" if has_blocked else "review-failure",
        "controller_status": "waiting-for-planner" if has_partial else "manual-review-required" if has_blocked else "waiting-for-retry",
        "planner_reentry_ready": has_partial,
    }


def _build_recovery_execution(recovery_summary: dict | None) -> dict | None:
    if not recovery_summary:
        return None
    if recovery_summary["recovery_state"] == "planner-reentry":
        return {
            "selected_path": "planner-reentry",
            "execution_state": "ready",
            "execution_lane": "planner-lane",
            "reentered_planner": True,
            "path_reason": "A partial verification result still requires a planner-guided next remediation step.",
        }
    if recovery_summary["retry_available"]:
        return {
            "selected_path": "manual-review",
            "execution_state": "held",
            "execution_lane": "manual-lane",
            "reentered_planner": False,
            "path_reason": "Recovery remains on a guarded review path until a stronger remediation is selected.",
        }
    return None


def _build_memory_summary(session: ScanSessionEntity) -> dict | None:
    attempted = sum(len(item.attempted_strategy_ids) for item in session.findings)
    rejected = sum(1 for item in session.findings if item.remediation_status == "rejected")
    escalated = sum(1 for item in session.findings if item.approval_status == "escalated")
    known_ids = sorted({strategy_id for item in session.findings for strategy_id in item.attempted_strategy_ids})
    if attempted == 0 and rejected == 0 and escalated == 0 and not known_ids:
        return None
    return {
        "attempted_strategy_count": attempted,
        "rejected_path_count": rejected,
        "escalated_path_count": escalated,
        "known_strategy_ids": known_ids,
        "suppressed_strategy_count": 0,
        "suppression_state": "clear",
        "next_memory_action": "generate-materially-different-patch" if rejected or escalated else "no-memory-block",
        "recent_constraint": "Previous remediation attempts are tracked at the finding level for safer retries." if attempted else "",
    }


def _build_operations_summary(state: str, session: ScanSessionEntity) -> dict:
    current_lane = {
        "scanning": "scan-lane",
        "decisioning": "decision-lane",
        "remediation-review": "remediation-lane",
        "approval-control": "approval-lane",
        "verification-follow-up": "verification-lane",
        "completed": "closure-lane",
        "failed": "closure-lane",
    }[state]
    next_lane = {
        "scanning": "decision-lane",
        "decisioning": "remediation-lane",
        "remediation-review": "approval-lane",
        "approval-control": "verification-lane",
        "verification-follow-up": "closure-lane",
        "completed": None,
        "failed": None,
    }[state]
    active_items = len(session.findings) if session.status == "completed" else 1
    return {
        "current_lane": current_lane,
        "next_lane": next_lane,
        "pending_handoff": next_lane is not None and state not in {"completed", "failed"},
        "handoff_reason": "The workflow will move to the next controlled lane when the current gate is satisfied." if next_lane else "No further workflow handoff remains for this saved session.",
        "active_item_count": active_items,
    }


def _build_operations_execution(state: str, active_controller: str, operations_summary: dict) -> dict:
    return {
        "current_handoff": f"{operations_summary['current_lane']} -> {operations_summary['next_lane'] or 'closed'}",
        "handoff_status": "active" if state in {"scanning", "decisioning"} else "pending" if operations_summary["pending_handoff"] else "closed",
        "owning_controller": active_controller,
        "pending_execution_step": "Resolve the current workflow gate before the next lane handoff." if operations_summary["pending_handoff"] else "No pending execution step remains.",
        "step_completion_state": "Waiting on the current controller to release the handoff." if operations_summary["pending_handoff"] else "Current workflow lane is closed.",
    }


def _build_workflow_closure(state: str, session: ScanSessionEntity) -> dict:
    requires_human = any(item.approval_status in {"pending", "escalated"} for item in session.findings) or any(
        item.remediation_status in {"verified_partial", "validation_failed", "rejected", "rolled_back"} for item in session.findings
    )
    autonomous_ready = state == "completed" and not requires_human and session.status == "completed"
    return {
        "closure_state": "autonomous-ready" if autonomous_ready else "human-controlled" if requires_human else "manual-closure",
        "closure_label": "Autonomous-ready closure" if autonomous_ready else "Human-controlled closure" if requires_human else "Manual closure",
        "closure_reason": (
            "The saved workflow has no remaining validated finding and no human control blocker."
            if autonomous_ready
            else "Approval or verification pressure still requires human control before the session can be treated as fully closed."
            if requires_human
            else "The saved workflow can be closed manually after the remaining review steps are confirmed."
        ),
        "autonomous_ready": autonomous_ready,
        "requires_human_control": requires_human,
        "next_closure_step": "Re-run the scan after future changes." if autonomous_ready else "Resolve the active review blocker.",
    }
