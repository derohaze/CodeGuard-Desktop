class CodeGuardError(Exception):
    pass


class InvalidSourcePathError(CodeGuardError):
    pass


class ExternalAIServiceError(CodeGuardError):
    def __init__(
        self,
        message: str,
        *,
        provider: str = "ai_provider",
        retryable: bool = True,
        status_code: int | None = None,
        failure_kind: str = "runtime",
    ) -> None:
        super().__init__(message)
        self.provider = provider
        self.retryable = retryable
        self.status_code = status_code
        self.failure_kind = failure_kind


class WorkflowConflictError(CodeGuardError):
    pass
