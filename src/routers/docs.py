from fastapi import BackgroundTasks, Depends, APIRouter, UploadFile, Request
from pathlib import Path
import shutil
import uuid

from ..core import database
from ..services import doc
from ..ingestion import pipeline

import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/documents/{doc_id}")
async def check_doc_status(doc_id: str, conn = Depends(database.get_db_conn)):
    return await doc.get_document(doc_id, conn)

@router.post("/documents")
async def upload_and_ingest(request: Request):
    # raw_dir = Path("/data/raw")
    print("WTF")
    print(request)
    # raw_dir.mkdir(parents=True, exist_ok=True)
    
    # doc_id = uuid.uuid4().hex
    # file_path = raw_dir / f"{doc_id}_{file.filename}"
    
    # with file_path.open("wb") as f:
    #     shutil.copyfileobj(file.file, f)
        
    # background_tasks.add_task(pipeline.run_ingestion_pipeline, file_path, doc_id)
    
    return {
        "doc_id": "bruh",
        "status": "processing",
    }
    