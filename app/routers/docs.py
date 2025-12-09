from fastapi import APIRouter

router = APIRouter()

@router.get("/documents")
async def submit_docs():
    return {"message": "Router submit docs"}