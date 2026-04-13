from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse


app = FastAPI()
EXPORTS_DIR = Path("exports").resolve()
ALLOWED_HOSTS = {"example.com", "api.example.com"}


def ensure_allowed_host(url: str) -> str:
    host = httpx.URL(url).host or ""
    if host not in ALLOWED_HOSTS:
        raise HTTPException(status_code=400, detail="Host is not allowed.")
    return url


def safe_export_path(name: str) -> Path:
    candidate = (EXPORTS_DIR / name).resolve()
    candidate.relative_to(EXPORTS_DIR)
    return candidate


@app.get("/fetch")
async def fetch_remote(request: Request):
    target_url = ensure_allowed_host(request.query_params.get("url", "https://example.com"))
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(target_url)
    return {"status": response.status_code}


@app.get("/download")
async def download_file(request: Request):
    export_name = request.query_params.get("file", "report.txt")
    return FileResponse(safe_export_path(export_name))
