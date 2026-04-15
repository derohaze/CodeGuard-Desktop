from app.domain.repositories.scan_repository import ScanSessionRepository
from app.infrastructure.services.workflow.session_query_support import list_recent_analysis_sessions
from app.infrastructure.services.workflow.workflow_team_posture_projection import (
    build_workflow_team_posture_hotspots,
    summarize_workflow_team_posture_hotspots,
)


class GetWorkflowTeamPostureSummaryUseCase:
    def __init__(self, repository: ScanSessionRepository) -> None:
        self.repository = repository

    async def execute(self, limit: int = 25) -> dict:
        sessions = await list_recent_analysis_sessions(self.repository, limit=limit)
        hotspots = build_workflow_team_posture_hotspots(sessions)
        return summarize_workflow_team_posture_hotspots(sessions, hotspots)
