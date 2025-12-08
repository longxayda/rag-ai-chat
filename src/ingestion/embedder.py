from sentence_transformers import SentenceTransformer
from pathlib import Path
import json
import numpy as np

def get_embeddings(processed_file_path: Path = Path.cwd() / "data" / "processed" / "chunks.json"):
    """
    Loads text chunks from a JSON file, computes their embeddings, and returns
    the chunks and the embeddings.

    Args:
        processed_file_path: The path to the JSON file containing the chunks.

    Returns:
        A tuple (chunks, embeddings) where:
            - chunks (list): The list of loaded text chunks (dictionaries).
            - embeddings (numpy.ndarray): The computed sentence embeddings.
    """
    # 1. Configuration
    model_name = "all-MiniLM-L6-v2"

    # 2. Load Model
    try:
        model = SentenceTransformer(model_name)
    except Exception as e:
        print(f"Error loading model {model_name}: {e}")
        return [], np.array([])

    # 3. Load Data
    if not processed_file_path.exists():
        raise FileNotFoundError(f"{processed_file_path} not found")

    with processed_file_path.open("r", encoding="utf-8") as file:
        chunks = json.load(file)

    sentences = [chunk["text"] for chunk in chunks]

    print("--- Embedding Process ---")
    print("Number of chunks loaded:", len(sentences))

    # 4. Compute Embeddings
    # The output is a numpy array
    embeddings = model.encode(sentences, show_progress_bar=True, batch_size=32)

    print("Embedding computation done.")
    print("Embeddings shape:", embeddings.shape)
    print("--- ------------------- ---")

    return chunks, embeddings

if __name__ == "__main__":
    chunks, embeddings = get_embeddings()

    # If you want to save the embeddings for long-term use (recommended for large datasets):
    embeddings_file = Path.cwd() / "data" / "processed" / "embeddings.npy"
    np.save(embeddings_file, embeddings)
    print(f"Embeddings saved to {embeddings_file}")