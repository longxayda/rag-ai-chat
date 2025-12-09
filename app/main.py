from fastapi import FastAPI

from .routers import chats, docs

app = FastAPI()

app.include_router(chats.router)
app.include_router(docs.router)

@app.get("/")
async def root():
    return {"message": "RAG AI Application"}