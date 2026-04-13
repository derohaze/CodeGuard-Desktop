from functools import lru_cache

from app.application.use_cases.delete_all_sessions import DeleteAllSessionsUseCase
from app.application.use_cases.delete_session import DeleteSessionUseCase
from app.application.use_cases.apply_fix import ApplyFixUseCase
from app.application.use_cases.rollback_fix import RollbackFixUseCase
from app.application.use_cases.explain_finding import ExplainFindingUseCase
from app.application.use_cases.generate_batch_remediation import GenerateBatchRemediationUseCase
from app.application.use_cases.generate_fix import GenerateFixUseCase
from app.application.use_cases.get_session import GetSessionUseCase
from app.application.use_cases.get_workflow_repo_hotspots import GetWorkflowRepoHotspotsUseCase
from app.application.use_cases.get_workflow_repo_intelligence_summary import GetWorkflowRepoIntelligenceSummaryUseCase
from app.application.use_cases.get_workflow_service_exposure_feed import GetWorkflowServiceExposureFeedUseCase
from app.application.use_cases.get_workflow_service_exposure_summary import GetWorkflowServiceExposureSummaryUseCase
from app.application.use_cases.get_workflow_team_posture_feed import GetWorkflowTeamPostureFeedUseCase
from app.application.use_cases.get_workflow_team_posture_summary import GetWorkflowTeamPostureSummaryUseCase
from app.application.use_cases.list_sessions import ListSessionsUseCase
from app.application.use_cases.reject_fix import RejectFixUseCase
from app.application.use_cases.retry_fix_strategy import RetryFixStrategyUseCase
from app.application.use_cases.start_scan import StartScanUseCase
from app.infrastructure.ai.agents.explain_agent import ExplainAgent
from app.infrastructure.ai.agents.fix_agent import FixAgent
from app.infrastructure.ai.agents.validation_agent import ValidationAgent
from app.domain.services.ai_client import SecurityAnalysisAIClient
from app.infrastructure.ai.provider_factory import build_ai_client
from app.infrastructure.ai.orchestration.remediation_router import RemediationRouter
from app.infrastructure.repositories.mongo_scan_repository import MongoScanSessionRepository
from app.infrastructure.services.runtime_safety_policy import validate_provider_endpoints
from app.infrastructure.services.scan_execution_service import ScanExecutionService


@lru_cache
def get_repository() -> MongoScanSessionRepository:
    return MongoScanSessionRepository()


@lru_cache
def get_ai_client() -> SecurityAnalysisAIClient:
    validate_provider_endpoints()
    return build_ai_client()


@lru_cache
def get_scan_execution_service() -> ScanExecutionService:
    return ScanExecutionService(get_repository(), get_ai_client())


@lru_cache
def get_remediation_router() -> RemediationRouter:
    ai_client = get_ai_client()
    return RemediationRouter(
        explain_agent=ExplainAgent(ai_client),
        fix_agent=FixAgent(ai_client),
        validation_agent=ValidationAgent(ai_client),
        model_router=ai_client.model_router,
    )


def get_start_scan_use_case() -> StartScanUseCase:
    return StartScanUseCase(get_repository())


def get_list_sessions_use_case() -> ListSessionsUseCase:
    return ListSessionsUseCase(get_repository())


def get_workflow_repo_intelligence_summary_use_case() -> GetWorkflowRepoIntelligenceSummaryUseCase:
    return GetWorkflowRepoIntelligenceSummaryUseCase(get_repository())


def get_workflow_repo_hotspots_use_case() -> GetWorkflowRepoHotspotsUseCase:
    return GetWorkflowRepoHotspotsUseCase(get_repository())


def get_workflow_team_posture_summary_use_case() -> GetWorkflowTeamPostureSummaryUseCase:
    return GetWorkflowTeamPostureSummaryUseCase(get_repository())


def get_workflow_team_posture_feed_use_case() -> GetWorkflowTeamPostureFeedUseCase:
    return GetWorkflowTeamPostureFeedUseCase(get_repository())


def get_workflow_service_exposure_summary_use_case() -> GetWorkflowServiceExposureSummaryUseCase:
    return GetWorkflowServiceExposureSummaryUseCase(get_repository())


def get_workflow_service_exposure_feed_use_case() -> GetWorkflowServiceExposureFeedUseCase:
    return GetWorkflowServiceExposureFeedUseCase(get_repository())


def get_session_use_case() -> GetSessionUseCase:
    return GetSessionUseCase(get_repository())


def get_delete_session_use_case() -> DeleteSessionUseCase:
    return DeleteSessionUseCase(get_repository())


def get_delete_all_sessions_use_case() -> DeleteAllSessionsUseCase:
    return DeleteAllSessionsUseCase(get_repository())


def get_explain_finding_use_case() -> ExplainFindingUseCase:
    return ExplainFindingUseCase(get_repository(), get_remediation_router())


def get_generate_fix_use_case() -> GenerateFixUseCase:
    return GenerateFixUseCase(get_repository(), get_remediation_router())


def get_generate_batch_remediation_use_case() -> GenerateBatchRemediationUseCase:
    return GenerateBatchRemediationUseCase(get_repository(), get_remediation_router())


def get_apply_fix_use_case() -> ApplyFixUseCase:
    return ApplyFixUseCase(get_repository())


def get_reject_fix_use_case() -> RejectFixUseCase:
    return RejectFixUseCase(get_repository())


def get_retry_fix_strategy_use_case() -> RetryFixStrategyUseCase:
    return RetryFixStrategyUseCase(get_repository(), get_remediation_router())


def get_rollback_fix_use_case() -> RollbackFixUseCase:
    return RollbackFixUseCase(get_repository())
