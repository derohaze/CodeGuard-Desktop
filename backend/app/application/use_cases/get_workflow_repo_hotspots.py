from app.domain.repositories.scan_repository import ScanSessionRepository
from app.infrastructure.services.session_query_support import list_recent_analysis_sessions
from app.infrastructure.services.workflow_repo_intelligence_projection import build_workflow_repo_hotspots


class GetWorkflowRepoHotspotsUseCase:
    def __init__(self, repository: ScanSessionRepository) -> None:
        self.repository = repository

    async def execute(self, limit: int = 25) -> dict:
        sessions = await list_recent_analysis_sessions(self.repository, limit=limit)
        items = [item for session in sessions for item in build_workflow_repo_hotspots(session)]
        return {"items": items[:limit]}
