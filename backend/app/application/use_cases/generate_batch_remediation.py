from app.application.dto.remediation_contracts import GenerateBatchRemediationRequest, RemediationPlanResponse
from app.application.use_cases.generate_fix import _build_plan_entity, remediation_plan_is_usable
from app.application.use_cases.remediation_mapper import map_remediation_plan
from app.domain.entities.scan import FindingEntity
from app.domain.entities.scan import utc_now
from app.domain.repositories.scan_repository import ScanSessionRepository
from app.infrastructure.ai.orchestration.remediation_router import RemediationRouter
from app.infrastructure.services.decision_summary import append_approval_history, build_finding_decision_summary
from app.infrastructure.services.remediation_context import build_batch_remediation_context, build_remediation_context


class GenerateBatchRemediationUseCase:
    def __init__(self, repository: ScanSessionRepository, agent_router: RemediationRouter) -> None:
        self.repository = repository
        self.agent_router = agent_router

    async def execute(self, payload: GenerateBatchRemediationRequest) -> RemediationPlanResponse | None:
        session = await self.repository.get_by_id(payload.session_id)
        if session is None:
            return None
        if not session.findings:
            return None

        batch_context = build_batch_remediation_context(session, session.findings)
        ranked_findings = sorted(session.findings, key=_batch_primary_sort_key, reverse=True)
        entity = None

        for finding in ranked_findings:
            primary_context = build_remediation_context(session, finding)
            combined_context = {**primary_context, "batch": batch_context}
            await self.agent_router.start_run(combined_context, "batch")
            explanation = await self.agent_router.explain(primary_context, mode="batch")
            remediation = await self.agent_router.generate_fix(combined_context, mode="batch")
            candidate = _build_plan_entity(
                finding.id,
                explanation,
                remediation,
                combined_context,
                await self.agent_router.build_trace(combined_context, "batch"),
                mode="batch",
            )
            candidate.finding_ids = [item.id for item in session.findings]
            if remediation_plan_is_usable(map_remediation_plan(candidate)):
                entity = candidate
                break
            if entity is None:
                entity = candidate

        if entity is None:
            return None

        entity.finding_ids = [item.id for item in session.findings]
        entity.review_summary = _build_batch_review_summary(session.findings, entity.patch.file, entity.strategies[0].label if entity.strategies else "")
        for finding in session.findings:
            finding.remediation_status = "patch_generated"
            finding.decision_summary = build_finding_decision_summary(finding)
            if finding.decision_summary["policy_outcome"] == "review-required" and finding.approval_status not in {"approved", "escalated", "rejected"}:
                append_approval_history(
                    finding,
                    "pending",
                    "Batch remediation review is pending before workspace apply can proceed.",
                    timestamp=utc_now().isoformat(),
                )
        await self.repository.update(
            session.id,
            {
                "findings": session.findings,
                "updated_at": utc_now(),
            },
        )
        return map_remediation_plan(entity)


def _batch_primary_sort_key(finding: FindingEntity) -> tuple[int, int, int]:
    severity_rank = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    span = max(1, int(finding.line_end) - int(finding.line) + 1)
    return (severity_rank.get(finding.severity, 0), int(finding.confidence), span)


def _build_batch_review_summary(findings: list[FindingEntity], patch_file: str, strategy_label: str) -> str:
    categories = sorted({finding.category for finding in findings if finding.category})
    category_summary = ", ".join(categories[:3]) if categories else "security issues"
    strategy_text = strategy_label or "the selected strategy"
    return (
        f"Prepared a batch remediation plan for {len(findings)} validated findings. "
        f"The current patch focuses on {patch_file} using {strategy_text}, while the remaining findings stay visible for follow-up review. "
        f"Covered categories: {category_summary}."
    )
