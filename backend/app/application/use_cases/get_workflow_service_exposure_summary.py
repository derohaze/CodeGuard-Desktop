from app.domain.repositories.scan_repository import ScanSessionRepository
from app.infrastructure.services.session_query_support import list_recent_analysis_sessions
from app.infrastructure.services.workflow_service_exposure_projection import (
    build_workflow_service_exposure_hotspots,
    summarize_workflow_service_exposure_hotspots,
)


class GetWorkflowServiceExposureSummaryUseCase:
    def __init__(self, repository: ScanSessionRepository) -> None:
        self.repository = repository

    async def execute(self, limit: int = 25) -> dict:
        sessions = await list_recent_analysis_sessions(self.repository, limit=limit)
        hotspots = [item for session in sessions for item in build_workflow_service_exposure_hotspots(session)]
        return summarize_workflow_service_exposure_hotspots(sessions, hotspots)
