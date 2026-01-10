from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
import json

from ..models.dto import QueryRequest
from ..utils import chat
from ..core import database
from ..services import rag

router = APIRouter()

OLLAMA_MODEL = "gemma3:1b"
TOP_RELEVANT_CONTEXT = 3

# --- API Routes ---

@router.post("/chat/stream")
async def rag_stream(
    request: QueryRequest,
    conn = Depends(database.get_db_conn)
):
    ctxs = await rag.hybrid_search(request.query, TOP_RELEVANT_CONTEXT, conn)
    print("CTXS---------", ctxs)
    ctx_str = chat.format_context(ctxs) if ctxs else "Không tìm được tài liệu liên quan."
    print("CTX STRING---------", ctx_str)
    full_prompt = chat.build_rag_prompt_v3(request.query, ctx_str)
    print("FULL -------------", full_prompt)
    # Extract sources
    sources = []
    if ctxs:
        seen_files = set()
        for ctx in ctxs:
            metadata = json.loads(ctx['metadata']) if isinstance(ctx['metadata'], str) else ctx['metadata']
            file_name = metadata.get('file_name', 'Unknown')
            if file_name not in seen_files:
                sources.append({
                    'file_name': file_name,
                    'file_path': metadata.get('file_path', ''),
                })
                seen_files.add(file_name)
    
    async def sse_generator():
        # Send sources first (space is fine here for JSON)
        yield f"event: sources\ndata: {json.dumps(sources, ensure_ascii=False)}\n\n"
        
        # Stream the response - NO space after 'data:'
        async for chunk in chat.stream_generator(full_prompt, model=OLLAMA_MODEL):
            yield f"event: message\ndata:{chunk}\n\n"  # ← Remove space after 'data:'
        
        # Signal completion
        yield "event: done\ndata: {}\n\n"
    
    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream"
    )