import asyncpg
from fastapi import HTTPException
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from .config import settings

import logging

logger = logging.getLogger(__name__)

# In src/core/database.py

async def register_vector_type(conn):
    """Registers the pgvector type with asyncpg."""
    await conn.set_type_codec(
        'vector',
        encoder=lambda v: str(v), # Encodes list [0.1, 0.2] as string '[0.1, 0.2]'
        decoder=lambda v: [float(x) for x in v[1:-1].split(',')],
        schema='public',
        format='text'
    )

class AsyncDatabase:
    _pool: asyncpg.Pool = None
    
    @classmethod
    async def initialize(cls):
        """Initializes the asyncpg connection pool."""
        if cls._pool is not None:
            return

        try:
            # Use asyncpg.create_pool, which is an asynchronous function
            cls._pool = await asyncpg.create_pool(
                user=settings.postgres_user,
                password=settings.postgres_password,
                host=settings.postgres_host,
                port=settings.postgres_port,
                database=settings.postgres_name,
                min_size=5,  # Same as minconn
                max_size=20, # Same as maxconn
            )
            print("✅ Async Database pool initialized...")
        except Exception as e:
            print("Error initializing async connection pool")
            raise e

    @classmethod
    async def close(cls) -> None:
        """Closes the asyncpg connection pool."""
        if cls._pool:
            await cls._pool.close()
            cls._pool = None
            print("Async Database pool closed")

    @classmethod
    @asynccontextmanager
    async def get_connection(cls) -> AsyncGenerator[asyncpg.Connection, None]:
        """Async context manager to acquire and release a connection."""
        if not cls._pool:
            raise Exception("Database pool is not initialized")
        
        conn: asyncpg.Connection = None
        conn = await cls._pool.acquire() 
        try:
            # Acquires a connection asynchronously
            await register_vector_type(conn)
            yield conn
        finally:
            # Releases the connection back to the pool
            if conn is not None:
                await cls._pool.release(conn)

async def get_db_conn():
    """Provides an acquired connection to the router and ensures release."""
    try:
        # Calls the context manager from the AsyncDatabase class
        async with AsyncDatabase.get_connection() as conn:
            yield conn
    except Exception as e:
        # Handle case where pool is not initialized or database is down
        logger.exception("Database exception", e)
        raise HTTPException(status_code=503, detail="Database Service Unavailable")