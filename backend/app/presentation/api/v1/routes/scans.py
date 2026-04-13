import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app.application.dto.scan_contracts import ScanSessionDetailResponse, StartScanRequest
from app.application.use_cases.scan_mapper import map_session_detail
from app.application.use_cases.get_session import GetSessionUseCase
from app.application.use_cases.start_scan import StartScanUseCase
from app.core.exceptions import InvalidSourcePathError
from app.presentation.api.v1.routes.dependencies import (
    get_scan_execution_service,
    get_session_use_case,
    get_start_scan_use_case,
)


router = APIRouter()


@router.post("/scans", response_model=ScanSessionDetailResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_scan(
    payload: StartScanRequest,
    start_scan_use_case: StartScanUseCase = Depends(get_start_scan_use_case),
):
    try:
        created = await start_scan_use_case.execute(payload)
    except InvalidSourcePathError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    await get_scan_execution_service().submit(created.id)
    return map_session_detail(created)


@router.get("/scans/{session_id}", response_model=ScanSessionDetailResponse)
async def get_scan(session_id: str, use_case: GetSessionUseCase = Depends(get_session_use_case)):
    detail = await use_case.execute(session_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan session not found.")
    return detail


@router.get("/scans/{session_id}/events")
async def stream_scan_events(session_id: str, use_case: GetSessionUseCase = Depends(get_session_use_case)):
    detail = await use_case.execute(session_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan session not found.")

    async def event_generator():
        last_signature = None
        while True:
            current = await use_case.execute(session_id)
            if current is None:
                yield "event: scan_failed\ndata: " + json.dumps({"error": "Scan session not found."}) + "\n\n"
                return

            payload = current.model_dump(mode="json")
            session = payload["session"]
            signature = (
                session["updated_at"],
                session["status"],
                session["progress"],
                session.get("phase_progress", 0),
                session["current_phase"],
                session["findings_count"],
                session["candidate_findings_count"],
            )
            if signature != last_signature:
                event_name = "scan_progress"
                if session["status"] == "completed":
                    event_name = "scan_completed"
                elif session["status"] == "failed":
                    event_name = "scan_failed"
                yield f"event: {event_name}\ndata: {json.dumps(payload, separators=(',', ':'))}\n\n"
                last_signature = signature

            if session["status"] in {"completed", "failed"}:
                return
            await asyncio.sleep(1.0)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
