from fastapi import FastAPI

from contextlib import asynccontextmanager

from .routers import chats, docs, heritages
from .core.config import settings
from .core.database import AsyncDatabase
from .exceptions.handlers import register_exception_handlers

from fastapi.middleware.cors import CORSMiddleware



# Database connection
@asynccontextmanager
async def lifespan(app: FastAPI):
    await AsyncDatabase.initialize()
    yield
    await AsyncDatabase.close()

app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or specific origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handlers
register_exception_handlers(app)

# Routes
app.include_router(chats.router)
app.include_router(docs.router)
app.include_router(heritages.router)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/health")
def health_check():
    return {"status": "ok", "app_name": settings.app_name}