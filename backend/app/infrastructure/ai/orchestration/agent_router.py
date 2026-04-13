from app.infrastructure.ai.agents.explain_agent import ExplainAgent
from app.infrastructure.ai.agents.fix_agent import FixAgent
from app.infrastructure.ai.agents.validation_agent import ValidationAgent


class AgentRouter:
    def __init__(
        self,
        *,
        explain_agent: ExplainAgent,
        fix_agent: FixAgent,
        validation_agent: ValidationAgent,
    ) -> None:
        self.explain_agent = explain_agent
        self.fix_agent = fix_agent
        self.validation_agent = validation_agent

    async def explain(self, remediation_context: dict) -> dict:
        return await self.explain_agent.run(remediation_context)

    async def generate_fix(self, remediation_context: dict, mode: str) -> dict:
        draft = await self.fix_agent.run(remediation_context, mode)
        return await self.validation_agent.run(remediation_context, draft, mode)
