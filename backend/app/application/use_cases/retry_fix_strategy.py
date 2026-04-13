from app.application.dto.remediation_contracts import RetryFixStrategyRequest, RemediationPlanResponse
from app.application.use_cases.generate_fix import _build_plan_entity
from app.application.use_cases.remediation_mapper import map_remediation_plan
from app.domain.entities.retry_state import RetryStateEntity
from app.domain.entities.scan import utc_now
from app.domain.repositories.scan_repository import ScanSessionRepository
from app.infrastructure.ai.orchestration.remediation_router import RemediationRouter
from app.infrastructure.services.decision_summary import append_approval_history, build_finding_decision_summary
from app.infrastructure.services.remediation_context import build_batch_remediation_context, build_remediation_context, locate_finding
from app.infrastructure.services.workflow_persistence import WorkflowPersistenceService


class RetryFixStrategyUseCase:
    def __init__(
        self,
        repository: ScanSessionRepository,
        router: RemediationRouter,
        workflow_persistence: WorkflowPersistenceService | None = None,
    ) -> None:
        self.repository = repository
        self.router = router
        self.workflow_persistence = workflow_persistence

    async def execute(self, payload: RetryFixStrategyRequest) -> RemediationPlanResponse | None:
        session = await self.repository.get_by_id(payload.session_id)
        if session is None:
            return None
        finding = locate_finding(session, payload.finding_id)
        if finding is None:
            return None

        retry_state = RetryStateEntity(
            excluded_strategy_ids=sorted(set(payload.excluded_strategy_ids or [])),
            attempted_strategy_ids=sorted(set((payload.attempted_strategy_ids or []) + finding.attempted_strategy_ids)),
            previous_rationales=[],
        )
        context = build_remediation_context(session, finding)
        context["retry"] = {
            "attempt": max(2, len(retry_state.attempted_strategy_ids) + 1),
            "excluded_strategy_ids": retry_state.excluded_strategy_ids,
            "attempted_strategy_ids": retry_state.attempted_strategy_ids,
        }

        if payload.mode == "batch":
            context["batch"] = build_batch_remediation_context(session, session.findings)

        await self.router.start_run(context, payload.mode)
        explanation = await self.router.explain(context, mode=payload.mode)
        remediation = await self.router.generate_fix(context, mode=payload.mode)
        remediation["strategies"] = [
            item
            for item in remediation.get("strategies", [])
            if str(item.get("id", "")) not in set(retry_state.excluded_strategy_ids)
        ]

        if not remediation["strategies"]:
            return None

        entity = _build_plan_entity(
            finding.id,
            explanation,
            remediation,
            context,
            await self.router.build_trace(context, payload.mode),
            mode=payload.mode,
        )
        finding.remediation_status = "patch_generated"
        finding.decision_summary = build_finding_decision_summary(finding)
        if finding.decision_summary["policy_outcome"] == "review-required" and finding.approval_status not in {"approved", "escalated", "rejected"}:
            append_approval_history(
                finding,
                "pending",
                "A replacement remediation path is pending review before workspace apply can proceed.",
                timestamp=utc_now().isoformat(),
            )
        new_attempts = sorted(set(finding.attempted_strategy_ids + [item.id for item in entity.strategies]))
        finding.attempted_strategy_ids = new_attempts
        await self.repository.update(
            session.id,
            {
                "findings": session.findings,
                "updated_at": utc_now(),
            },
        )
        if self.workflow_persistence is not None:
            await self.workflow_persistence.record_audit(
                session_id=session.id,
                entity_type="finding",
                entity_id=finding.id,
                action="remediation.plan_retried",
                payload={
                    "excluded_strategy_ids": retry_state.excluded_strategy_ids,
                    "attempted_strategy_ids": finding.attempted_strategy_ids,
                    "recommended_strategy_id": entity.recommended_strategy_id,
                },
            )
        return map_remediation_plan(entity)
