from __future__ import annotations

from functools import lru_cache

from app.config import get_settings
from app.memory.memory_store import MemoryStore


@lru_cache
def get_memory_store() -> MemoryStore:
    settings = get_settings()
    return MemoryStore(mongo_uri=settings.mongodb_uri, mongo_db=settings.mongodb_db)

