import asyncio
from ollama import chat
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from .ingestion.indexer import search_similar
from concurrent.futures import ThreadPoolExecutor

app = FastAPI(title="Gemma3 API")

class QueryRequest(BaseModel):
    query: str


def ollama_stream_sync(template: str):
    """
    Blocking synchronous generator from Ollama.
    """
    stream = chat(
        model="gemma3:1b",
        messages=[{"role": "user", "content": template}],
        stream=True,
    )
    for chunk in stream:
        content = chunk.get("message", {}).get("content", "")
        if content:
            yield content


async def get_llm_stream(template: str):
    """
    Async wrapper around the blocking Ollama generator.
    Uses a thread + async queue.
    """
    loop = asyncio.get_event_loop()
    queue = asyncio.Queue()
    executor = ThreadPoolExecutor(max_workers=1)

    def run_blocking():
        for content in ollama_stream_sync(template):
            asyncio.run_coroutine_threadsafe(queue.put(content), loop)
        asyncio.run_coroutine_threadsafe(queue.put(None), loop)  # end signal

    loop.run_in_executor(executor, run_blocking)

    while True:
        item = await queue.get()
        if item is None:
            break
        yield item


@app.post("/rag/stream")
async def rag_stream(request: QueryRequest):

    user_query = request.query
    results = search_similar(user_query, 4)

    formatted = [
        f"Document ID: {r[0]}, Source Metadata: {r[2]}, Content: {r[1]}"
        for r in results
    ]

    contexts = "\n".join(formatted)

    template = f"""You are an expert Q&A system. Only answer from the CONTEXT:
    ### CONTEXT ###
    {contexts}
    ### INSTRUCTIONS ### 
    # 1. **Do not use any external knowledge.** Only use the information present in the documents above. 
    # 2. If the answer is found, answer **precisely** and **completely**. 
    # 3. If the answer is not present in the documents, you **MUST** state: "I cannot find the answer in the provided context." 
    # 4. Provide the answer clearly and concisely.

    QUESTION: {user_query}""".strip()

    async def event_stream():
        async for chunk in get_llm_stream(template):
            yield chunk

    return StreamingResponse(event_stream(), media_type="text/plain")
