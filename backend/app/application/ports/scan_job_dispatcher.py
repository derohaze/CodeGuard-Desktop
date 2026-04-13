from typing import Protocol


class ScanJobDispatcher(Protocol):
    async def enqueue_scan(self, session_id: str, job_id: str) -> None: ...
