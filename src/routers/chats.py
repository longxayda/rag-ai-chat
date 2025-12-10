from typing import AsyncGenerator, List, Tuple

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from ollama import AsyncClient

from ..ingestion.indexer import search_similar
from ..models.dto import QueryRequest
from ..exceptions.exceptions import ChatNotFoundException

router = APIRouter()

OLLAMA_MODEL = "gemma3:1b"
TOP_RELEVANT_CONTEXT = 4

llm_client = AsyncClient()

def format_context(results: List[Tuple]) -> str:
    """
    Formats the raw tuples from the search engine into a readable string.
    Assumption: Tuple structure is (id, content, metadata).
    """
    formatted_docs = []
    for doc_id, content, metadata in results:
        formatted_docs.append(
            f"Document ID: {doc_id}\n"
            f"Source Metadata: {metadata}\n"
            f"Content: {content}"
        )
    return "\n---\n".join(formatted_docs)


def build_rag_prompt(user_query: str, context_str: str) -> str:
    """
    Constructs the system prompt for RAG.
    """
    return f"""You are an expert Q&A system. Only answer from the CONTEXT provided below.

### CONTEXT ###
{context_str}

### INSTRUCTIONS ### 
1. **Do not use any external knowledge.** Only use the information present in the documents above. 
2. If the answer is found, answer **precisely** and **completely**. 
3. If the answer is not present in the documents, you **MUST** state: "I cannot find the answer in the provided context." 
4. Provide the answer clearly and concisely.

QUESTION: {user_query}""".strip()


async def stream_generator(prompt: str) -> AsyncGenerator[str, None]:
    """
    Streams the response from Ollama asynchronously.
    """
    try:
        # Native async support from Ollama library
        stream = await llm_client.chat(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
        )

        async for chunk in stream:
            # Type hint: chunk is a ChatResponse object
            content = chunk.get("message", {}).get("content", "")
            if content:
                yield content

    except Exception as e:
        yield f"\n[Error generating response: {str(e)}]"


# --- API Routes ---

@router.get("/chat/{chat_id}")
async def get_chat(chat_id: str):
    raise ChatNotFoundException(chat_id=chat_id)

@router.post("/chat/stream")
async def rag_stream(request: QueryRequest) -> StreamingResponse:
    """
    Endpoint to retrieve context and stream LLM response.
    """
    # context_tuples = await asyncio.to_thread(search_similar, request.query, top_k=TOP_RELEVANT_CONTEXT)
    context_tuples = search_similar(request.query, top_k=TOP_RELEVANT_CONTEXT)
    
    if not context_tuples:
        context_str = "No relevant documents found."
    else:
        context_str = format_context(context_tuples)

    full_prompt = build_rag_prompt(request.query, context_str)
    
    return StreamingResponse(
        stream_generator(full_prompt),
        media_type="text/plain"
    )
    