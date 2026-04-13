from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.error_handlers import register_error_handlers
from app.core.logging import configure_logging
from app.infrastructure.database.mongo_manager import ensure_mongo_indexes
from app.presentation.api.v1.routes import health, remediation, scans, sessions


settings = get_settings()
configure_logging()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.app_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(scans.router, prefix="/api/v1", tags=["scans"])
app.include_router(sessions.router, prefix="/api/v1", tags=["sessions"])
app.include_router(remediation.router, prefix="/api/v1", tags=["remediation"])
register_error_handlers(app)


@app.on_event("startup")
async def startup() -> None:
    await ensure_mongo_indexes()
