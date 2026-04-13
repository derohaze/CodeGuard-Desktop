from app.domain.services.ai_client import SecurityAnalysisAIClient


class ValidationAgent:
    def __init__(self, ai_client: SecurityAnalysisAIClient) -> None:
        self.ai_client = ai_client

    async def run(self, remediation_context: dict, remediation_draft: dict, mode: str) -> dict:
        return await self.ai_client.validate_remediation(remediation_context, remediation_draft, mode)
