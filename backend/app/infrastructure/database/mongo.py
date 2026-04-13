import asyncio

from pymongo import AsyncMongoClient

from app.core.config import get_settings


_mongo_client: AsyncMongoClient | None = None
_mongo_database = None
_mongo_lock = asyncio.Lock()


def _build_client() -> AsyncMongoClient:
    settings = get_settings()
    return AsyncMongoClient(
        settings.mongodb_uri,
        maxPoolSize=settings.mongodb_max_pool_size,
        minPoolSize=settings.mongodb_min_pool_size,
        serverSelectionTimeoutMS=settings.mongodb_server_selection_timeout_ms,
        uuidRepresentation="standard",
    )


async def initialize_mongo():
    global _mongo_client, _mongo_database
    if _mongo_database is not None:
        return _mongo_database

    async with _mongo_lock:
        if _mongo_database is not None:
            return _mongo_database
        settings = get_settings()
        client = _build_client()
        database = client[settings.mongodb_database]
        await database.command("ping")
        _mongo_client = client
        _mongo_database = database
        return _mongo_database


def get_database():
    global _mongo_client, _mongo_database
    if _mongo_database is None:
        settings = get_settings()
        _mongo_client = _build_client()
        _mongo_database = _mongo_client[settings.mongodb_database]
    return _mongo_database


async def ping_mongo() -> bool:
    try:
        database = await initialize_mongo()
        await database.command("ping")
        return True
    except Exception:
        return False


async def close_mongo() -> None:
    global _mongo_client, _mongo_database
    if _mongo_client is not None:
        await _mongo_client.close()
    _mongo_client = None
    _mongo_database = None
