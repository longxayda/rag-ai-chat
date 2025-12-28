# recursive_chunker.py
import tiktoken
from typing import List, Tuple
from langchain_text_splitters import RecursiveCharacterTextSplitter


def recursive_chunk_text(
    text: str,
    chunk_size: int = 800,
    overlap: float | int = 0.15,
    return_offsets: bool = False,
) -> List[str] | Tuple[List[str], List[tuple]]:
    """
    Recursive chunking using LangChain RecursiveCharacterTextSplitter.

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

    # --- Calculate overlap in tokens ---
    if isinstance(overlap, float) and overlap < 1:
        chunk_overlap = int(chunk_size * overlap)
    else:
        chunk_overlap = int(overlap)

    # --- Tokenizer (for accurate token counting) ---
    tokenizer = tiktoken.encoding_for_model("gpt-4")

    # --- Build recursive text splitter ---
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=200,
        length_function=lambda t: len(tokenizer.encode(t)),
        # separators=["\n\n", "\n", ". ", " ", ""],
        separators=[
            "\n\n\n",
            "\n\n",
            "\n",
            ". ",
            ".",
            "! ",      # Exclamation
            "? ",      # Question
            "; ",      # Semicolon
            " ",
            ",",
            "\u200b",  # Zero-width space
            "\uff0c",  # Fullwidth comma
            "\u3001",  # Ideographic comma
            "\uff0e",  # Fullwidth full stop
            "\u3002",  # Ideographic full stop
            "",
        ],
        keep_separator=True,
    )

    # --- Chunk ---
    if return_offsets:
        chunks = text_splitter.split_text(text)
        offsets = _calculate_offsets(text, chunks)
        return chunks, offsets

    chunks = text_splitter.split_text(text)
    return chunks


def _calculate_offsets(text: str, chunks: List[str]) -> List[tuple]:
    """
    Calculate character offsets for each chunk in the original text.

    Args:
        text (str): Original text
        chunks (list[str]): List of text chunks

    Returns:
        list[tuple]: List of (start, end) offset tuples
    """
    offsets = []
    search_start = 0

    for chunk in chunks:
        start_idx = text.find(chunk, search_start)
        if start_idx == -1:
            # If exact match not found, approximate based on last position
            start_idx = search_start
        end_idx = start_idx + len(chunk)
        offsets.append((start_idx, end_idx))
        search_start = start_idx + 1

    return offsets