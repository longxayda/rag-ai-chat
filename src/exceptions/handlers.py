from .exceptions import ApiException
from fastapi.responses import JSONResponse
import psycopg2
from fastapi.requests import Request
from datetime import datetime
import logging
from fastapi import FastAPI

logger = logging.getLogger(__name__)


async def api_exception_handler(request: Request, exc: ApiException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error_code": exc.headers["X-Error-Code"],
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    
async def postgres_error_handler(request: Request, exc: psycopg2.Error):
    logger.exception("PostgreSQL Error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Server Error",
        }
    )
    
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
        

def register_exception_handlers(app: FastAPI):
    app.exception_handler(ApiException)(api_exception_handler)
    app.exception_handler(psycopg2.Error)(postgres_error_handler)
    app.exception_handler(Exception)(global_exception_handler)

    

