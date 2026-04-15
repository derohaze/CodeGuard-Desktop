from app.application.dto.remediation_contracts import (
    ExplanationResponse,
    FixStrategyResponse,
    PatchApplicationResponse,
    RemediationScoreResponse,
    RemediationMetricsResponse,
    RemediationStepResponse,
    PatchCandidateResponse,
    RemediationExecutionResponse,
    RemediationPlanResponse,
)
from app.application.use_cases.scan.scan_mapper import map_finding, map_session_summary
from app.domain.entities.remediation import (
    ExplanationEntity,
    FixStrategyEntity,
    PatchCandidateEntity,
    RemediationMetricsEntity,
    RemediationPlanEntity,
    RemediationScoreEntity,
    RemediationStepEntity,
)
from app.domain.entities.patch_application import PatchApplicationEntity
from app.domain.entities.scan import ScanSessionEntity


def map_explanation(entity: ExplanationEntity) -> ExplanationResponse:
    return ExplanationResponse(
        finding_id=entity.finding_id,
        summary=entity.summary,
        exploit_scenario=entity.exploit_scenario,
        request_example=entity.request_example,
        payload_example=entity.payload_example,
        attack_steps=entity.attack_steps,
        entry_point=entity.entry_point,
        execution_path=entity.execution_path,
        sink=entity.sink,
        impact=entity.impact,
    )


def map_fix_strategy(entity: FixStrategyEntity) -> FixStrategyResponse:
    return FixStrategyResponse(
        id=entity.id,
        label=entity.label,
        kind=entity.kind,
        confidence=entity.confidence,
        impact=entity.impact,
        effort=entity.effort,
        summary=entity.summary,
        rationale=entity.rationale,
        diff=entity.diff,
        recommended=entity.recommended,
        fix_type=entity.fix_type,
        security_strength=entity.security_strength,
        regression_risk=entity.regression_risk,
        selection_reason=entity.selection_reason,
        non_selection_reason=entity.non_selection_reason,
        residual_risks=entity.residual_risks,
        policy_compliant=entity.policy_compliant,
        policy_violations=entity.policy_violations,
    )


def map_patch_candidate(entity: PatchCandidateEntity) -> PatchCandidateResponse:
    return PatchCandidateResponse(
        file=entity.file,
        language=entity.language,
        summary=entity.summary,
        diff=entity.diff,
        validation_notes=entity.validation_notes,
        before_snippet=entity.before_snippet,
        after_snippet=entity.after_snippet,
        fix_type=entity.fix_type,
        rationale=entity.rationale,
        residual_risks=entity.residual_risks,
        manual_review_required=entity.manual_review_required,
    )


def map_remediation_step(entity: RemediationStepEntity) -> RemediationStepResponse:
    return RemediationStepResponse(
        id=entity.id,
        title=entity.title,
        status=entity.status,
        agent=entity.agent,
        details=entity.details,
    )


def map_remediation_metrics(entity: RemediationMetricsEntity) -> RemediationMetricsResponse:
    return RemediationMetricsResponse(
        file=entity.file,
        vulnerability_type=entity.vulnerability_type,
        remediation_mode=entity.remediation_mode,
        analyzed_lines=entity.analyzed_lines,
        path_steps=entity.path_steps,
        evidence_location=entity.evidence_location,
    )


def map_remediation_score(entity: RemediationScoreEntity) -> RemediationScoreResponse:
    return RemediationScoreResponse(
        total=entity.total,
        strategy_quality=entity.strategy_quality,
        fix_completeness=entity.fix_completeness,
        sink_alignment=entity.sink_alignment,
        residual_risk=entity.residual_risk,
        confidence=entity.confidence,
        rationale=entity.rationale,
    )


def map_patch_application(entity: PatchApplicationEntity) -> PatchApplicationResponse:
    return PatchApplicationResponse(
        finding_id=entity.finding_id,
        status=entity.status,
        file=entity.file,
        applied_strategy_id=entity.applied_strategy_id,
        fix_type=entity.fix_type,
        validation_notes=entity.validation_notes,
        manual_edit_applied=entity.manual_edit_applied,
        checkpoint_id=entity.checkpoint_id,
        rollback_available=entity.rollback_available,
        verification_status=entity.verification_status,
        verification_notes=entity.verification_notes,
        verification_confidence=entity.verification_confidence,
        verification_confidence_valid=entity.verification_confidence_valid,
        approval_gate_outcome=entity.approval_gate_outcome,
        approval_gate_reason=entity.approval_gate_reason,
        write_scope=entity.write_scope,
        network_policy=entity.network_policy,
    )


def map_remediation_plan(entity: RemediationPlanEntity) -> RemediationPlanResponse:
    return RemediationPlanResponse(
        mode=entity.mode,
        finding_ids=entity.finding_ids,
        review_summary=entity.review_summary,
        explanation=map_explanation(entity.explanation) if entity.explanation else None,
        strategies=[map_fix_strategy(item) for item in entity.strategies],
        recommended_strategy_id=entity.recommended_strategy_id,
        patch=map_patch_candidate(entity.patch) if entity.patch else None,
        steps=[map_remediation_step(item) for item in entity.steps],
        metrics=map_remediation_metrics(entity.metrics) if entity.metrics else None,
        score=map_remediation_score(entity.score) if entity.score else None,
    )


def map_remediation_execution(action: PatchApplicationEntity, session: ScanSessionEntity) -> RemediationExecutionResponse:
    return RemediationExecutionResponse(
        action=map_patch_application(action),
        session=map_session_summary(session),
        findings=[map_finding(item) for item in session.findings],
        candidate_findings=[map_finding(item) for item in session.candidate_findings],
    )
