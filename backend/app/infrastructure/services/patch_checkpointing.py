from __future__ import annotations

from copy import deepcopy
from uuid import uuid4

from app.domain.entities.scan import FindingEntity, ScanSessionEntity, utc_now


_SESSION_SNAPSHOT_FIELDS = (
    "preview",
    "repository_summary",
    "review_queue_summary",
    "annotations",
    "annotation_summary",
    "findings",
    "candidate_findings",
    "is_safe",
    "security_score",
    "score_rationale",
    "progress_logs",
    "unread",
    "path_summary",
    "traced_paths_count",
    "total_paths_count",
)


def create_patch_checkpoint(
    *,
    session: ScanSessionEntity,
    finding: FindingEntity,
    target_file: str,
    original_content: str,
    strategy_id: str | None,
) -> dict:
    return {
        "id": uuid4().hex,
        "finding_id": finding.id,
        "target_file": target_file,
        "strategy_id": strategy_id,
        "created_at": utc_now().isoformat(),
        "original_content": original_content,
        "session_snapshot": {
            key: deepcopy(_snapshot_value(getattr(session, key)))
            for key in _SESSION_SNAPSHOT_FIELDS
        },
    }


def append_checkpoint(existing: list[dict], checkpoint: dict, *, keep_last: int = 10) -> list[dict]:
    next_items = [*existing, checkpoint]
    if len(next_items) <= keep_last:
        return next_items
    return next_items[-keep_last:]


def build_rollback_updates(
    *,
    session: ScanSessionEntity,
    checkpoint: dict,
    rollback_notes: list[str],
) -> dict:
    snapshot = dict(checkpoint.get("session_snapshot", {}))
    logs = list(snapshot.get("progress_logs", session.progress_logs[-11:]))
    logs.append(
        f"Rolled back the locally applied remediation for {checkpoint.get('target_file', 'the selected file')}."
    )
    remaining_checkpoints = [
        item for item in session.remediation_checkpoints
        if str(item.get("id", "")) != str(checkpoint.get("id", ""))
    ]
    return {
        **snapshot,
        "progress_logs": logs[-12:],
        "unread": True,
        "last_verification": {
            "status": "rolled_back",
            "notes": rollback_notes,
            "timestamp": utc_now().isoformat(),
            "confidence": None,
            "confidence_valid": False,
        },
        "remediation_checkpoints": remaining_checkpoints,
    }


def find_checkpoint(session: ScanSessionEntity, checkpoint_id: str | None, finding_id: str) -> dict | None:
    checkpoints = list(session.remediation_checkpoints)
    if checkpoint_id:
        for item in reversed(checkpoints):
            if str(item.get("id", "")) == checkpoint_id:
                return item
        return None
    for item in reversed(checkpoints):
        if str(item.get("finding_id", "")) == finding_id:
            return item
    return None


def _snapshot_value(value):
    if isinstance(value, FindingEntity):
        return _finding_snapshot(value)
    if isinstance(value, list):
        return [_snapshot_value(item) for item in value]
    return value


def _finding_snapshot(finding: FindingEntity) -> dict:
    return {
        "id": finding.id,
        "severity": finding.severity,
        "title": finding.title,
        "file": finding.file,
        "line": finding.line,
        "line_end": finding.line_end,
        "category": finding.category,
        "confidence": finding.confidence,
        "summary": finding.summary,
        "impact": finding.impact,
        "attack_input": finding.attack_input,
        "attack_execution": finding.attack_execution,
        "attack_result": finding.attack_result,
        "audit_log": list(finding.audit_log),
        "explanation": finding.explanation,
        "fix_suggestions": list(finding.fix_suggestions),
        "evidence": finding.evidence,
        "remediation_status": finding.remediation_status,
        "approval_status": finding.approval_status,
        "approval_history": list(finding.approval_history),
        "applied_strategy_id": finding.applied_strategy_id,
        "remediation_notes": list(finding.remediation_notes),
        "attempted_strategy_ids": list(finding.attempted_strategy_ids),
        "decision_summary": finding.decision_summary,
    }
