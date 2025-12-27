from fastapi import APIRouter, Depends
from ..models.dto import QueryRequest

from ..core import database
from ..services import heritages

router = APIRouter()

@router.get("/heritages")
async def get_heritages(request: QueryRequest, conn = Depends(database.get_db_conn)):
    rows = await heritages.get_heritages(conn=conn)
    return [dict(r) for r in rows]
    