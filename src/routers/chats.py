from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from ..models.dto import QueryRequest
from ..utils import chat
from ..core import database
from ..services import rag

router = APIRouter()

OLLAMA_MODEL = "gemma3:1b"
TOP_RELEVANT_CONTEXT = 4

# --- API Routes ---

# @router.get("/chat/{chat_id}")
# async def get_chat(chat_id: str):
#     raise ChatNotFoundException(chat_id=chat_id)

@router.post("/chat/stream")
async def rag_stream(
    request: QueryRequest,
    conn = Depends(database.get_db_conn)
):
    ctx = await rag.search_similar(request.query, 5, conn)
    ctx_str = chat.format_context(ctx) if ctx else "No relevant documents found."
    full_prompt = chat.build_rag_prompt(request.query, ctx_str)

    return StreamingResponse(
        chat.stream_generator(full_prompt, model=OLLAMA_MODEL),
        media_type="text/plain"
    )
    