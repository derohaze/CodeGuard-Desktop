from pathlib import Path

from app.core.exceptions import WorkflowConflictError
from app.application.dto.remediation_contracts import ApplyFixRequest, RemediationExecutionResponse
from app.application.use_cases.remediation_mapper import map_remediation_execution
from app.domain.entities.patch_application import PatchApplicationEntity
from app.domain.entities.scan import utc_now
from app.domain.repositories.scan_repository import ScanSessionRepository
from app.infrastructure.services.patch_applier import apply_patch_locally
from app.infrastructure.services.patch_checkpointing import append_checkpoint, create_patch_checkpoint
from app.infrastructure.services.patch_validator import validate_patch_application
from app.infrastructure.services.post_fix_verifier import verify_applied_patch
from app.infrastructure.services.decision_summary import (
    append_approval_history,
    build_finding_decision_summary,
    determine_apply_gate,
)
from app.infrastructure.services.remediation_context import locate_finding
from app.infrastructure.services.remediation_session_state import build_post_remediation_updates
from app.infrastructure.services.runtime_safety_policy import (
    build_network_policy_note,
    build_write_scope_note,
    ensure_safe_patch_target,
)
from app.infrastructure.services.workflow_persistence import WorkflowPersistenceService


class ApplyFixUseCase:
    def __init__(self, repository: ScanSessionRepository, workflow_persistence: WorkflowPersistenceService | None = None) -> None:
        self.repository = repository
        self.workflow_persistence = workflow_persistence

    async def execute(self, payload: ApplyFixRequest) -> RemediationExecutionResponse | None:
        session = await self.repository.get_by_id(payload.session_id)
        if session is None:
            return None
        finding = locate_finding(session, payload.finding_id)
        if finding is None:
            return None
        finding.decision_summary = build_finding_decision_summary(finding)
        apply_readiness = str((finding.decision_summary or {}).get("apply_readiness") or "local-apply-eligible")
        if apply_readiness == "approval-required-before-apply" and finding.approval_status != "approved" and not payload.approval_acknowledged:
            raise WorkflowConflictError("This remediation path still requires approval acknowledgement before workspace apply can proceed.")
        if payload.approval_acknowledged and finding.approval_status != "approved":
            append_approval_history(
                finding,
                "approved",
                "Workspace apply was approved for the current remediation review cycle.",
                timestamp=utc_now().isoformat(),
            )

        source_root = _resolve_source_root(session.source_path)
        valid, notes, fix_type = validate_patch_application(
            source_root=source_root,
            target_file=payload.file,
            before_snippet=payload.before_snippet,
            after_snippet=payload.after_snippet,
            evidence_file=finding.file,
            evidence_line=finding.line,
            manual_edit=payload.manual_edit,
        )
        if not valid:
            finding.remediation_status = "validation_failed"
            finding.remediation_notes = notes
            finding.decision_summary = build_finding_decision_summary(finding)
            gate_outcome, gate_reason = determine_apply_gate(finding)
            updated_session = await self.repository.update(
                session.id,
                {"findings": session.findings, "updated_at": utc_now()},
            ) or session
            action = PatchApplicationEntity(
                finding_id=finding.id,
                status="validation_failed",
                file=payload.file,
                applied_strategy_id=payload.strategy_id,
                fix_type=fix_type,
                validation_notes=notes,
                manual_edit_applied=payload.manual_edit,
                approval_gate_outcome=gate_outcome,
                approval_gate_reason=gate_reason,
            )
            return map_remediation_execution(action, updated_session)

        try:
            target_path = ensure_safe_patch_target(source_root=source_root, target_file=payload.file)
        except ValueError as exc:
            finding.remediation_status = "validation_failed"
            finding.remediation_notes = [str(exc)]
            finding.decision_summary = build_finding_decision_summary(finding)
            gate_outcome, gate_reason = determine_apply_gate(finding)
            updated_session = await self.repository.update(
                session.id,
                {"findings": session.findings, "updated_at": utc_now()},
            ) or session
            action = PatchApplicationEntity(
                finding_id=finding.id,
                status="validation_failed",
                file=payload.file,
                applied_strategy_id=payload.strategy_id,
                fix_type=fix_type,
                validation_notes=[str(exc)],
                manual_edit_applied=payload.manual_edit,
                approval_gate_outcome=gate_outcome,
                approval_gate_reason=gate_reason,
            )
            return map_remediation_execution(action, updated_session)
        original_content = target_path.read_text(encoding="utf-8", errors="ignore")
        checkpoint = create_patch_checkpoint(
            session=session,
            finding=finding,
            target_file=payload.file,
            original_content=original_content,
            strategy_id=payload.strategy_id,
        )
        apply_patch_locally(
            source_root=source_root,
            target_file=payload.file,
            before_snippet=payload.before_snippet,
            after_snippet=payload.after_snippet,
            evidence_line=finding.line,
        )
        verification = verify_applied_patch(
            source_root=source_root,
            target_file=payload.file,
            finding_category=finding.category,
            finding_line=finding.line,
        )
        write_scope = build_write_scope_note(payload.file)
        network_policy = build_network_policy_note()
        verification_notes = [*verification["notes"], write_scope, network_policy]
        if verification["status"] == "verified":
            finding.remediation_status = "verified_fixed"
            finding.applied_strategy_id = payload.strategy_id
            finding.remediation_notes = [*notes, *verification_notes]
        else:
            finding.remediation_status = "verified_partial"
            finding.applied_strategy_id = payload.strategy_id
            finding.remediation_notes = [
                *notes,
                "Local patch applied, but deterministic verification still requires follow-up review.",
                *verification_notes,
            ]
        if payload.strategy_id and payload.strategy_id not in finding.attempted_strategy_ids:
            finding.attempted_strategy_ids.append(payload.strategy_id)
        finding.decision_summary = build_finding_decision_summary(finding)
        gate_outcome, gate_reason = determine_apply_gate(finding, verification_status=verification["status"])

        session_updates = build_post_remediation_updates(
            session=session,
            applied_finding=finding,
            validation_notes=notes,
            verification=verification,
        )

        updated_session = await self.repository.update(
            session.id,
            {
                **session_updates,
                "remediation_checkpoints": append_checkpoint(session.remediation_checkpoints, checkpoint),
                "last_verification": {
                    "status": verification["status"],
                    "notes": verification_notes,
                    "timestamp": utc_now().isoformat(),
                    "confidence": verification.get("confidence"),
                    "confidence_valid": bool(verification.get("confidence_valid")),
                },
                "updated_at": utc_now(),
            },
        ) or session
        if self.workflow_persistence is not None:
            await self.workflow_persistence.record_verification(
                session_id=session.id,
                finding_id=finding.id,
                fix_id=payload.strategy_id or finding.id,
                status=verification["status"],
                checks=verification_notes,
                payload={
                    "file": payload.file,
                    "manual_edit": payload.manual_edit,
                    "checkpoint_id": checkpoint["id"],
                    "approval_gate_outcome": gate_outcome,
                },
            )
            await self.workflow_persistence.record_audit(
                session_id=session.id,
                entity_type="finding",
                entity_id=finding.id,
                action="remediation.applied",
                payload={
                    "strategy_id": payload.strategy_id,
                    "file": payload.file,
                    "verification_status": verification["status"],
                    "approval_gate_outcome": gate_outcome,
                },
            )
        action = PatchApplicationEntity(
            finding_id=finding.id,
            status="applied",
            file=payload.file,
            applied_strategy_id=payload.strategy_id,
            fix_type=fix_type,
            validation_notes=notes,
            manual_edit_applied=payload.manual_edit,
            checkpoint_id=checkpoint["id"],
            rollback_available=True,
            verification_status=verification["status"],
            verification_notes=verification_notes,
            verification_confidence=verification.get("confidence"),
            verification_confidence_valid=bool(verification.get("confidence_valid")),
            approval_gate_outcome=gate_outcome,
            approval_gate_reason=gate_reason,
            write_scope=write_scope,
            network_policy=network_policy,
        )
        return map_remediation_execution(action, updated_session)


def _resolve_source_root(source_path: str) -> Path:
    path = Path(source_path).expanduser().resolve()
    return path if path.is_dir() else path.parent
