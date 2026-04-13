from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse


app = FastAPI()
BASE_DIR = Path("exports").resolve()


def safe_join(name: str) -> Path:
    candidate = (BASE_DIR / name).resolve()
    try:
        candidate.relative_to(BASE_DIR)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid path.") from exc
    return candidate


@app.get("/download")
async def download(request: Request):
    requested = request.query_params.get("file", "report.txt")
    return FileResponse(safe_join(requested))
