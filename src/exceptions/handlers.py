from .exceptions import ApiException
from fastapi.responses import JSONResponse
import psycopg2
from fastapi.requests import Request
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def register_exception_handlers(app):
    
    @app.exception_handler(ApiException)
    async def api_exception_handler(request: Request, exc: ApiException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "error_code": exc.headers["X-Error-Code"],
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
    @app.exception_handler(psycopg2.Error)
    async def postgres_error_handler(request: Request, exc: psycopg2.Error):
        logger.exception("PostgreSQL Error: %s", exc)
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal Server Error",
            }
        )
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )

