# semantic_chunker.py
import semchunk
import tiktoken
from typing import List, Tuple


def semantic_chunk_text(
    text: str,
    chunk_size: int = 512,
    overlap: float | int = 0.15,
    return_offsets: bool = False,
) -> List[str] | Tuple[List[str], List[tuple]]:
    """
    Semantic chunking using semchunk.

    Args:
        text (str): Full document text
        chunk_size (int): Max tokens per chunk
        overlap (float|int): Token overlap (ratio <1 or absolute >=1)
        return_offsets (bool): Whether to return (chunks, offsets)

    Returns:
        list[str] OR (list[str], list[offsets])
    """

    if not text or not text.strip():
        return [] if not return_offsets else ([], [])

    # --- Tokenizer (recommended for RAG) ---
    tokenizer = tiktoken.encoding_for_model("gpt-4")

    # --- Build chunker ---
    chunker = semchunk.chunkerify(
        tokenizer,
        chunk_size=chunk_size,
    )

    # --- Chunk ---
    if return_offsets:
        chunks, offsets = chunker(
            text,
            offsets=True,
            overlap=overlap,
        )
        return chunks, offsets

    chunks = chunker(
        text,
        overlap=overlap,
    )

    return chunks
