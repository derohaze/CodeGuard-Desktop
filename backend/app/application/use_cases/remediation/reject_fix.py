from app.application.dto.remediation_contracts import RejectFixRequest, RemediationExecutionResponse
from app.application.use_cases.remediation.remediation_mapper import map_remediation_execution
from app.domain.entities.patch_application import PatchApplicationEntity
from app.domain.entities.scan import utc_now
from app.domain.repositories.scan_repository import ScanSessionRepository
from app.infrastructure.services.remediation.decision_summary import append_approval_history, determine_apply_gate
from app.infrastructure.services.remediation.remediation_context import locate_finding
from app.infrastructure.services.workflow.workflow_persistence import WorkflowPersistenceService


class RejectFixUseCase:
    def __init__(self, repository: ScanSessionRepository, workflow_persistence: WorkflowPersistenceService | None = None) -> None:
        self.repository = repository
        self.workflow_persistence = workflow_persistence

    async def execute(self, payload: RejectFixRequest) -> RemediationExecutionResponse | None:
        session = await self.repository.get_by_id(payload.session_id)
        if session is None:
            return None
        finding = locate_finding(session, payload.finding_id)
        if finding is None:
            return None

        finding.remediation_status = "rejected"
        if payload.strategy_id and payload.strategy_id not in finding.attempted_strategy_ids:
            finding.attempted_strategy_ids.append(payload.strategy_id)
        finding.remediation_notes = ["The remediation proposal was rejected. No file changes were applied."]
        append_approval_history(
            finding,
            "rejected",
            "The proposed remediation path was rejected during patch review.",
            timestamp=utc_now().isoformat(),
        )
        updated_session = await self.repository.update(
            session.id,
            {
                "findings": session.findings,
                "updated_at": utc_now(),
            },
        ) or session
        if self.workflow_persistence is not None:
            await self.workflow_persistence.record_audit(
                session_id=session.id,
                entity_type="finding",
                entity_id=finding.id,
                action="remediation.rejected",
                payload={
                    "strategy_id": payload.strategy_id,
                    "status": finding.remediation_status,
                },
            )

        action = PatchApplicationEntity(
            finding_id=finding.id,
            status="rejected",
            file=finding.file,
            applied_strategy_id=payload.strategy_id,
            fix_type="partial_mitigation",
            validation_notes=finding.remediation_notes,
            manual_edit_applied=False,
            approval_gate_outcome=determine_apply_gate(finding)[0],
            approval_gate_reason=determine_apply_gate(finding)[1],
        )
        return map_remediation_execution(action, updated_session)
