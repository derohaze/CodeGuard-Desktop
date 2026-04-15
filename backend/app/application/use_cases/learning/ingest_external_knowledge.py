from app.infrastructure.learning.ingestion.ingestion import ExternalKnowledgeIngestionService, IngestionSummary
from app.infrastructure.learning.common.schemas import ExternalKnowledgeSourceSpec


class IngestExternalKnowledgeUseCase:
    def __init__(self, service: ExternalKnowledgeIngestionService) -> None:
        self.service = service

    async def execute(self, sources: list[ExternalKnowledgeSourceSpec]) -> IngestionSummary:
        return await self.service.ingest(sources)
