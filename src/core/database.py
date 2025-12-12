import psycopg2
import logging
from psycopg2 import pool
from .config import settings

from ..logging.handlers import logger

class Database:
    _pool = None

    @classmethod
    def initialize(cls):
        try:
            cls._pool = pool.ThreadedConnectionPool(
                minconn=5,
                maxconn=20,
                user=settings.postgres_user,
                password=settings.postgres_password,
                host=settings.postgres_host,
                port=settings.postgres_port,
                dbname=settings.postgres_name
            )
            logger.info("✅ Database pool initialized for: %s", settings.app_name)
        except psycopg2.Error as e:
            logger.exception("Error connection pool")
            raise e

    @classmethod
    def close(cls) -> None:
        if cls._pool:
            cls._pool.closeall()
            logger.info("Database pool closed")

    @classmethod
    def get_connection(cls):
        if not cls._pool:
            raise Exception("Database pool is not initialized")
        return cls._pool.getconn()

    @classmethod
    def return_connection(cls, conn):
        cls._pool.putconn(conn)

# --- The Dependency for FastAPI ---
def get_db_conn():
    """
    Dependency that yields a database connection.
    This handles getting the connection and putting it back in the pool.
    """
    conn = Database.get_connection()
    try:
        yield conn
    finally:
        Database.return_connection(conn)