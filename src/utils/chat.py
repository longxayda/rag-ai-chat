from typing import AsyncGenerator, List, Tuple
from ollama import AsyncClient

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

async def stream_generator(prompt: str, model: str) -> AsyncGenerator[str, None]:
    """
    Streams the response from Ollama asynchronously.
    """
    try:
        stream = await llm_client.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
        )

        async for chunk in stream:
            content = chunk.get("message", {}).get("content", "")
            if content:
                yield content

    except Exception as e:
        yield f"\n[Error generating response: {str(e)}]"