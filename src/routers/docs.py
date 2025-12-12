from fastapi import APIRouter
from ..exceptions.exceptions import DocumentNotFound
from ..logging.handlers import logger
router = APIRouter()

@router.get("/documents/{doc_id}")
async def submit_docs(doc_id: str):
    logger.error("Doc not found")
    raise DocumentNotFound(doc_id=doc_id)