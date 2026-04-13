from functools import lru_cache

from pymongo import AsyncMongoClient

from app.core.config import get_settings


@lru_cache
def get_database():
    settings = get_settings()
    client = AsyncMongoClient(settings.mongodb_uri)
    return client[settings.mongodb_database]
