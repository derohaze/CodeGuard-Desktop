from pathlib import Path

from app.application.dto.remediation_contracts import RemediationExecutionResponse, RollbackFixRequest
from app.application.use_cases.remediation_mapper import map_remediation_execution
from app.domain.entities.patch_application import PatchApplicationEntity
from app.domain.entities.scan import utc_now
from app.domain.repositories.scan_repository import ScanSessionRepository
from app.infrastructure.services.patch_applier import restore_patch_checkpoint
from app.infrastructure.services.patch_checkpointing import build_rollback_updates, find_checkpoint
from app.infrastructure.services.runtime_safety_policy import (
    build_network_policy_note,
    build_write_scope_note,
    ensure_safe_patch_target,
)
from app.infrastructure.services.workflow_persistence import WorkflowPersistenceService


class RollbackFixUseCase:
    def __init__(self, repository: ScanSessionRepository, workflow_persistence: WorkflowPersistenceService | None = None) -> None:
        self.repository = repository
        self.workflow_persistence = workflow_persistence

    async def execute(self, payload: RollbackFixRequest) -> RemediationExecutionResponse | None:
        session = await self.repository.get_by_id(payload.session_id)
        if session is None:
            return None

        checkpoint = find_checkpoint(session, payload.checkpoint_id, payload.finding_id)
        if checkpoint is None:
            action = PatchApplicationEntity(
                finding_id=payload.finding_id,
                status="validation_failed",
                file="",
                validation_notes=["No saved local patch checkpoint was available for rollback."],
                verification_status="not_run",
            )
            return map_remediation_execution(action, session)

        source_root = _resolve_source_root(session.source_path)
        target_file = str(checkpoint.get("target_file", "")).strip()
        target_path = ensure_safe_patch_target(source_root=source_root, target_file=target_file)
        restore_patch_checkpoint(target_path=target_path, original_content=str(checkpoint.get("original_content", "")))

        rollback_notes = [
            "Restored the original file content from the saved local checkpoint.",
            build_write_scope_note(target_file),
            build_network_policy_note(),
        ]
        session_updates = build_rollback_updates(session=session, checkpoint=checkpoint, rollback_notes=rollback_notes)
        updated_session = await self.repository.update(
            session.id,
            {
                **session_updates,
                "updated_at": utc_now(),
            },
        ) or session
        if self.workflow_persistence is not None:
            await self.workflow_persistence.record_verification(
                session_id=session.id,
                finding_id=payload.finding_id,
                fix_id=str(checkpoint.get("strategy_id", "")) or payload.finding_id,
                status="rolled_back",
                checks=rollback_notes,
                payload={
                    "checkpoint_id": str(checkpoint.get("id", "")),
                    "target_file": target_file,
                },
            )
            await self.workflow_persistence.record_audit(
                session_id=session.id,
                entity_type="finding",
                entity_id=payload.finding_id,
                action="remediation.rolled_back",
                payload={
                    "checkpoint_id": str(checkpoint.get("id", "")),
                    "file": target_file,
                },
            )
        action = PatchApplicationEntity(
            finding_id=payload.finding_id,
            status="rolled_back",
            file=target_file,
            applied_strategy_id=str(checkpoint.get("strategy_id", "")) or None,
            validation_notes=rollback_notes,
            checkpoint_id=str(checkpoint.get("id", "")),
            rollback_available=False,
            verification_status="rolled_back",
            verification_notes=rollback_notes,
            approval_gate_outcome="review-required",
            approval_gate_reason="The workspace patch was rolled back, so the finding returned to a human-controlled remediation path.",
            write_scope=build_write_scope_note(target_file),
            network_policy=build_network_policy_note(),
        )
        return map_remediation_execution(action, updated_session)


def _resolve_source_root(source_path: str) -> Path:
    path = Path(source_path).expanduser().resolve()
    return path if path.is_dir() else path.parent
