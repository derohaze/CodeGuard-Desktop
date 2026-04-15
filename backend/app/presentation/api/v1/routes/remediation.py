from fastapi import APIRouter, Depends, HTTPException, status

from app.application.dto.remediation_contracts import (
    ApplyFixRequest,
    ExplainFindingRequest,
    ExplanationResponse,
    GenerateBatchRemediationRequest,
    GenerateFixRequest,
    RejectFixRequest,
    RemediationExecutionResponse,
    RemediationPlanResponse,
    RollbackFixRequest,
    RetryFixStrategyRequest,
)
from app.application.use_cases.remediation.apply_fix import ApplyFixUseCase
from app.application.use_cases.remediation.explain_finding import ExplainFindingUseCase
from app.application.use_cases.remediation.generate_batch_remediation import GenerateBatchRemediationUseCase
from app.application.use_cases.remediation.generate_fix import (
    GenerateFixUseCase,
    remediation_plan_failure_reason,
    remediation_plan_is_usable,
)
from app.application.use_cases.remediation.reject_fix import RejectFixUseCase
from app.application.use_cases.remediation.rollback_fix import RollbackFixUseCase
from app.application.use_cases.remediation.retry_fix_strategy import RetryFixStrategyUseCase
from app.core.exceptions import ExternalAIServiceError
from app.core.exceptions import WorkflowConflictError
from app.presentation.api.v1.routes.dependencies import (
    get_apply_fix_use_case,
    get_explain_finding_use_case,
    get_generate_batch_remediation_use_case,
    get_generate_fix_use_case,
    get_reject_fix_use_case,
    get_rollback_fix_use_case,
    get_retry_fix_strategy_use_case,
)
from app.infrastructure.services.runtime_safety_policy import sanitize_runtime_error


router = APIRouter()


@router.post("/remediation/explain", response_model=ExplanationResponse)
async def explain_finding(
    payload: ExplainFindingRequest,
    use_case: ExplainFindingUseCase = Depends(get_explain_finding_use_case),
):
    try:
        detail = await use_case.execute(payload)
    except ExternalAIServiceError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=sanitize_runtime_error(exc, operation="remediation")) from exc
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding or session not found.")
    return detail


@router.post("/remediation/fix", response_model=RemediationPlanResponse)
async def generate_fix(
    payload: GenerateFixRequest,
    use_case: GenerateFixUseCase = Depends(get_generate_fix_use_case),
):
    try:
        detail = await use_case.execute(payload)
    except ExternalAIServiceError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=sanitize_runtime_error(exc, operation="remediation")) from exc
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding or session not found.")
    if not remediation_plan_is_usable(detail):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=remediation_plan_failure_reason(detail),
        )
    return detail


@router.post("/remediation/fix/batch", response_model=RemediationPlanResponse)
async def generate_batch_remediation(
    payload: GenerateBatchRemediationRequest,
    use_case: GenerateBatchRemediationUseCase = Depends(get_generate_batch_remediation_use_case),
):
    try:
        detail = await use_case.execute(payload)
    except ExternalAIServiceError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=sanitize_runtime_error(exc, operation="remediation")) from exc
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No validated findings were available for batch remediation.")
    if not remediation_plan_is_usable(detail):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=remediation_plan_failure_reason(detail),
        )
    return detail


@router.post("/remediation/fix/apply", response_model=RemediationExecutionResponse)
async def apply_fix(
    payload: ApplyFixRequest,
    use_case: ApplyFixUseCase = Depends(get_apply_fix_use_case),
):
    try:
        detail = await use_case.execute(payload)
    except WorkflowConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding or session not found.")
    return detail


@router.post("/remediation/fix/reject", response_model=RemediationExecutionResponse)
async def reject_fix(
    payload: RejectFixRequest,
    use_case: RejectFixUseCase = Depends(get_reject_fix_use_case),
):
    detail = await use_case.execute(payload)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding or session not found.")
    return detail


@router.post("/remediation/fix/rollback", response_model=RemediationExecutionResponse)
async def rollback_fix(
    payload: RollbackFixRequest,
    use_case: RollbackFixUseCase = Depends(get_rollback_fix_use_case),
):
    detail = await use_case.execute(payload)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding or session not found.")
    return detail


@router.post("/remediation/fix/retry", response_model=RemediationPlanResponse)
async def retry_fix_strategy(
    payload: RetryFixStrategyRequest,
    use_case: RetryFixStrategyUseCase = Depends(get_retry_fix_strategy_use_case),
):
    try:
        detail = await use_case.execute(payload)
    except ExternalAIServiceError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=sanitize_runtime_error(exc, operation="remediation")) from exc
    if detail is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No materially different remediation strategy remained.")
    if not remediation_plan_is_usable(detail):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=remediation_plan_failure_reason(detail),
        )
    return detail
