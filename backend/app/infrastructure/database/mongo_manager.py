from __future__ import annotations

from pymongo import DESCENDING

from app.infrastructure.database.mongo import get_database


async def ensure_mongo_indexes() -> None:
    database = get_database()
    scan_sessions = database["scan_sessions"]
    await scan_sessions.create_index([("updated_at", DESCENDING)], name="idx_scan_sessions_updated_at_desc")
    await scan_sessions.create_index([("status", 1), ("updated_at", DESCENDING)], name="idx_scan_sessions_status_updated_at_desc")
    await scan_sessions.create_index([("repo", 1), ("updated_at", DESCENDING)], name="idx_scan_sessions_repo_updated_at_desc")
