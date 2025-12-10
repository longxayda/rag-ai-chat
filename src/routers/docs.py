from fastapi import APIRouter
from ..exceptions.exceptions import DocumentNotFound

router = APIRouter()

@router.get("/documents/{doc_id}")
async def submit_docs(doc_id: str):
    raise DocumentNotFound(doc_id=doc_id)