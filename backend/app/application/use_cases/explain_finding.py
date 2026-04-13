from app.application.dto.remediation_contracts import ExplainFindingRequest, ExplanationResponse
from app.application.use_cases.remediation_mapper import map_explanation
from app.domain.entities.remediation import ExplanationEntity
from app.domain.repositories.scan_repository import ScanSessionRepository
from app.infrastructure.ai.orchestration.remediation_router import RemediationRouter
from app.infrastructure.services.remediation_context import build_remediation_context, locate_finding
from app.infrastructure.services.workflow_persistence import WorkflowPersistenceService


class ExplainFindingUseCase:
    def __init__(
        self,
        repository: ScanSessionRepository,
        agent_router: RemediationRouter,
        workflow_persistence: WorkflowPersistenceService | None = None,
    ) -> None:
        self.repository = repository
        self.agent_router = agent_router
        self.workflow_persistence = workflow_persistence

    async def execute(self, payload: ExplainFindingRequest) -> ExplanationResponse | None:
        session = await self.repository.get_by_id(payload.session_id)
        if session is None:
            return None

        finding = locate_finding(session, payload.finding_id)
        if finding is None:
            return None

        context = build_remediation_context(session, finding)
        await self.agent_router.start_run(context, "single")
        explanation = await self.agent_router.explain(context, mode="single")
        entity = ExplanationEntity(
            finding_id=finding.id,
            summary=str(explanation.get("summary") or finding.summary),
            exploit_scenario=str(explanation.get("exploit_scenario") or finding.explanation),
            request_example=str(explanation.get("request_example") or ""),
            payload_example=str(explanation.get("payload_example") or ""),
            attack_steps=[str(item) for item in explanation.get("attack_steps", []) if str(item).strip()] or [
                f"Reach the entry point: {finding.attack_input}",
                f"Follow the execution path: {finding.attack_execution}",
                f"Exploit the sink impact: {finding.attack_result}",
            ],
            entry_point=str(explanation.get("entry_point") or finding.attack_input),
            execution_path=str(explanation.get("execution_path") or finding.attack_execution),
            sink=str(explanation.get("sink") or f"{finding.file}:{finding.line}"),
            impact=str(explanation.get("impact") or finding.impact),
        )
        if self.workflow_persistence is not None:
            await self.workflow_persistence.record_audit(
                session_id=session.id,
                entity_type="finding",
                entity_id=finding.id,
                action="remediation.explained",
                payload={
                    "file": finding.file,
                    "category": finding.category,
                    "summary": entity.summary,
                },
            )
        return map_explanation(entity)
