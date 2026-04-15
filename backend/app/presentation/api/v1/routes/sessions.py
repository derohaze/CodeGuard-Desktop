from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.application.dto.scan_contracts import SessionSummaryResponse
from app.application.dto.scan_contracts import (
    WorkflowRepoHotspotFeedResponse,
    WorkflowRepoIntelligenceSummaryResponse,
    WorkflowServiceExposureFeedResponse,
    WorkflowServiceExposureSummaryResponse,
    WorkflowTeamPostureFeedResponse,
    WorkflowTeamPostureSummaryResponse,
)
from app.application.use_cases.session.delete_all_sessions import DeleteAllSessionsUseCase
from app.application.use_cases.session.delete_session import DeleteSessionUseCase
from app.application.use_cases.workflow.get_workflow_repo_hotspots import GetWorkflowRepoHotspotsUseCase
from app.application.use_cases.workflow.get_workflow_repo_intelligence_summary import GetWorkflowRepoIntelligenceSummaryUseCase
from app.application.use_cases.workflow.get_workflow_service_exposure_feed import GetWorkflowServiceExposureFeedUseCase
from app.application.use_cases.workflow.get_workflow_service_exposure_summary import GetWorkflowServiceExposureSummaryUseCase
from app.application.use_cases.workflow.get_workflow_team_posture_feed import GetWorkflowTeamPostureFeedUseCase
from app.application.use_cases.workflow.get_workflow_team_posture_summary import GetWorkflowTeamPostureSummaryUseCase
from app.application.use_cases.session.list_sessions import ListSessionsUseCase
from app.presentation.api.v1.routes.dependencies import (
    get_delete_all_sessions_use_case,
    get_delete_session_use_case,
    get_list_sessions_use_case,
    get_workflow_repo_hotspots_use_case,
    get_workflow_repo_intelligence_summary_use_case,
    get_workflow_service_exposure_feed_use_case,
    get_workflow_service_exposure_summary_use_case,
    get_workflow_team_posture_feed_use_case,
    get_workflow_team_posture_summary_use_case,
)


router = APIRouter()


@router.get("/sessions", response_model=list[SessionSummaryResponse])
async def list_sessions(use_case: ListSessionsUseCase = Depends(get_list_sessions_use_case)):
    return await use_case.execute()


@router.get("/sessions/repo-intelligence-summary", response_model=WorkflowRepoIntelligenceSummaryResponse)
async def repo_intelligence_summary(
    limit: int = 25,
    use_case: GetWorkflowRepoIntelligenceSummaryUseCase = Depends(get_workflow_repo_intelligence_summary_use_case),
):
    return await use_case.execute(limit=limit)


@router.get("/sessions/repo-hotspots", response_model=WorkflowRepoHotspotFeedResponse)
async def repo_hotspots(
    limit: int = 25,
    use_case: GetWorkflowRepoHotspotsUseCase = Depends(get_workflow_repo_hotspots_use_case),
):
    return await use_case.execute(limit=limit)


@router.get("/sessions/team-posture-summary", response_model=WorkflowTeamPostureSummaryResponse)
async def team_posture_summary(
    limit: int = 25,
    use_case: GetWorkflowTeamPostureSummaryUseCase = Depends(get_workflow_team_posture_summary_use_case),
):
    return await use_case.execute(limit=limit)


@router.get("/sessions/team-posture-feed", response_model=WorkflowTeamPostureFeedResponse)
async def team_posture_feed(
    limit: int = 25,
    use_case: GetWorkflowTeamPostureFeedUseCase = Depends(get_workflow_team_posture_feed_use_case),
):
    return await use_case.execute(limit=limit)


@router.get("/sessions/service-exposure-summary", response_model=WorkflowServiceExposureSummaryResponse)
async def service_exposure_summary(
    limit: int = 25,
    use_case: GetWorkflowServiceExposureSummaryUseCase = Depends(get_workflow_service_exposure_summary_use_case),
):
    return await use_case.execute(limit=limit)


@router.get("/sessions/service-exposure-feed", response_model=WorkflowServiceExposureFeedResponse)
async def service_exposure_feed(
    limit: int = 25,
    use_case: GetWorkflowServiceExposureFeedUseCase = Depends(get_workflow_service_exposure_feed_use_case),
):
    return await use_case.execute(limit=limit)


@router.delete("/sessions", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_sessions(
    use_case: DeleteAllSessionsUseCase = Depends(get_delete_all_sessions_use_case),
):
    await use_case.execute()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    use_case: DeleteSessionUseCase = Depends(get_delete_session_use_case),
):
    deleted = await use_case.execute(session_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan session not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
