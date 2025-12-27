from sentence_transformers import SentenceTransformer
import numpy as np
from typing import Any
import asyncio

model_name = "all-MiniLM-L6-v2"
model = SentenceTransformer(model_name)
async def get_embeddings(chunks_from_doc: list[dict]) -> Any:
    """
    Loads text chunks from a list of dictionary, computes their embeddings, and returns
    the chunks and the embeddings.

    Args:
        processed_file_path: The path to the JSON file containing the chunks.

    Returns:
        A tuple (chunks, embeddings) where:
            - chunks (list): The list of loaded text chunks (dictionaries).
            - embeddings (numpy.ndarray): The computed sentence embeddings.
    """
    # 1. Configuration

    # 3. Load Data
    if not chunks_from_doc:
        return [], np.array([])

    sentences = [chunk["text"] for chunk in chunks_from_doc]

    print("--- Embedding Process ---")
    print("Number of chunks loaded:", len(sentences))

    # 4. Compute Embeddings
    # The output is a numpy array
    embeddings = await asyncio.to_thread(
        model.encode,
        sentences,
        show_progress_bar=True,
        batch_size=32
    )

    print("Embedding computation done.")
    print("Embeddings shape:", embeddings.shape)
    print("--- ------------------- ---")

    return chunks_from_doc, embeddings

async def embed_query(text: str) -> list[float]:
    embedding = await asyncio.to_thread(
        model.encode,
        [text]
    )
    return embedding[0].tolist()