import asyncpg
from typing import Any

import logging

from ..core import database

logger = logging.getLogger(__name__)

async def insert_task_log(doc_id: str, initial_state: str = 'INITIALIZED') -> Any:
    async for conn in database.get_db_conn():
        try:
            task_id = conn.fetchval("""
                INSERT INTO task_logs (doc_id, task_state)
                VALUES ($1, $2)
                RETURNING task_id;
                """, doc_id, initial_state)
            return task_id
        except asyncpg.exceptions.UniqueViolationError as e:
                logger.error(f"Duplicate doc_id {doc_id} detected.")
                return None
        except Exception as e:
            logger.exception(f"Failed to insert initial task log for {doc_id}")
            return None
        break

async def update_state(task_id: int, new_state: str, metadata: dict = None):
    """Updates the task_state and updated_at column for an existing task."""
    async for conn in database.get_db_conn():
        try:
            await conn.execute("""
                UPDATE task_logs 
                SET task_state = $1, 
                    task_metadata = COALESCE(task_metadata, '{}'::JSONB) || $2::JSONB,
                    updated_at = NOW()
                WHERE task_id = $3;
            """, new_state, metadata if metadata is not None else {}, task_id)
        except Exception as e:
            logger.exception(f"Failed to update task log {task_id} to state {new_state}")
        break

