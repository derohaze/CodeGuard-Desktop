from app.domain.services.ai_client import SecurityAnalysisAIClient


class FixAgent:
    def __init__(self, ai_client: SecurityAnalysisAIClient) -> None:
        self.ai_client = ai_client

    async def run(self, remediation_context: dict, mode: str) -> dict:
        return await self.ai_client.draft_fix_strategies(remediation_context, mode)
