from app.application.ports.scan_job_dispatcher import ScanJobDispatcher
from app.infrastructure.queue.redis import get_arq_pool
from app.infrastructure.services.scan_execution_service import ScanExecutionService


class InProcessScanJobDispatcher(ScanJobDispatcher):
    def __init__(self, scan_execution_service: ScanExecutionService) -> None:
        self.scan_execution_service = scan_execution_service

    async def enqueue_scan(self, session_id: str, job_id: str) -> None:
        await self.scan_execution_service.submit(session_id, job_id=job_id)


class ArqScanJobDispatcher(ScanJobDispatcher):
    def __init__(self, queue_name: str) -> None:
        self.queue_name = queue_name

    async def enqueue_scan(self, session_id: str, job_id: str) -> None:
        pool = await get_arq_pool()
        await pool.enqueue_job(
            "run_scan_job",
            session_id,
            job_id,
            _queue_name=self.queue_name,
            _job_id=f"scan:{job_id}",
        )
