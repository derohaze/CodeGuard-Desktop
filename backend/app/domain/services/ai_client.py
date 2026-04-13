from abc import ABC, abstractmethod


class SecurityAnalysisAIClient(ABC):
    def reset_runtime_state(self) -> None:
        return None

    def drain_runtime_events(self) -> list[str]:
        return []

    def snapshot_runtime_metrics(self, *, reset: bool = False) -> dict | None:
        return None

    @abstractmethod
    async def map_repository(
        self,
        project_name: str,
        source_path: str,
        repository_profile: dict,
        repository_artifacts: dict,
        preset: str,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    async def review_paths(
        self,
        project_name: str,
        source_path: str,
        repository_profile: dict,
        repository_map: dict,
        work_items: list[dict[str, str]],
        batch_index: int,
        total_batches: int,
        preset: str,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    async def validate_findings(
        self,
        project_name: str,
        source_path: str,
        repository_profile: dict,
        repository_map: dict,
        findings: list[dict],
        preset: str,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    async def summarize_verdict(
        self,
        project_name: str,
        source_path: str,
        repository_profile: dict,
        repository_map: dict,
        findings: list[dict],
        security_score: int | None,
        preset: str,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    async def explain_finding(
        self,
        remediation_context: dict,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    async def draft_fix_strategies(
        self,
        remediation_context: dict,
        mode: str,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    async def validate_remediation(
        self,
        remediation_context: dict,
        remediation_draft: dict,
        mode: str,
    ) -> dict:
        raise NotImplementedError
