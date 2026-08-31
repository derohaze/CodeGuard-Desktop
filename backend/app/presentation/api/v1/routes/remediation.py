from fastapi import APIRouter, Depends, HTTPException, status

from app.application.dto.remediation_contracts import ExplainFindingRequest, ExplanationResponse
from app.application.use_cases.remediation.explain_finding import ExplainFindingUseCase
from app.core.exceptions import ExternalAIServiceError
from app.presentation.api.v1.routes.dependencies import get_explain_finding_use_case
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
