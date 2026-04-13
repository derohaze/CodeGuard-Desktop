from app.domain.services.ai_client import SecurityAnalysisAIClient


class ExplainAgent:
    def __init__(self, ai_client: SecurityAnalysisAIClient) -> None:
        self.ai_client = ai_client

    async def run(self, remediation_context: dict) -> dict:
        return await self.ai_client.explain_finding(remediation_context)
