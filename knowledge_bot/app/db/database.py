from pathlib import Path

import asyncpg

from app.config import settings

_pool: asyncpg.Pool | None = None

async def connect() -> asyncpg.Pool:
    global _pool
    _pool = await asyncpg.create_pool(settings.database_url, min_size=1, max_size=4)
    migration = Path(__file__).parents[2] / "migrations" / "001_init.sql"
    await _pool.execute(migration.read_text())
    return _pool

async def close() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None

def pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Database is not connected")
    return _pool
