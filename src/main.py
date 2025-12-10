from fastapi import FastAPI

from contextlib import asynccontextmanager

from .routers import chats, docs
from .core.config import settings
from .core.database import Database
from .exceptions.handlers import register_exception_handlers


# Database connection
@asynccontextmanager
async def lifespan(app: FastAPI):
    Database.initialize()
    yield
    Database.close()

app = FastAPI(title=settings.app_name, lifespan=lifespan)

# Global Exception Handlers
register_exception_handlers(app)


# Routes
app.include_router(chats.router)
app.include_router(docs.router)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/health")
def health_check():
    return {"status": "ok", "app_name": settings.app_name}