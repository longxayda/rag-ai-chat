import numpy as np
import sys
import asyncpg
from fastapi import HTTPException
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from fastapi import Depends

from ..core.database import get_db_conn

load_dotenv()

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
model = SentenceTransformer(EMBEDDING_MODEL)


def print_asyncpg_exception(err):
    """
    Simpler handler for asyncpg exceptions. 
    A proper logger is recommended here.
    """
    err_type, err_obj, traceback = sys.exc_info()
    line_num = traceback.tb_lineno
    
    print("\nasyncpg ERROR:", err, "on line number:", line_num)
    print("asyncpg traceback:", traceback, "-- type:", err_type)
    # asyncpg exceptions often have the detail/hint in the main exception object

import json
import numpy as np
from fastapi import HTTPException

async def insert_embeddings(chunks: list[dict], embeddings: np.ndarray, conn) -> None:
    """
    Insert embedding vectors to embeddings table using asyncpg's copy mechanism.
    """
    # 1. Prepare data (list of tuples)
    rows = []
    for chunk, emb in zip(chunks, embeddings):
        rows.append((
            chunk.get("id", "fallback-id"),
            chunk.get("text", ""),
            emb.tolist(), 
            chunk.get("chunk_index", 0),  # Safe access with default value
            json.dumps(chunk.get("metadata", {}))
        ))

    if not rows:
        return

    try:
        # 2. Use copy_records_to_table for high-performance bulk insert
        await conn.copy_records_to_table(
            'embeddings', 
            records=rows, 
            columns=('id', 'text', 'embedding', 'chunk_index', 'metadata')
        )
    except Exception as e:
        # logger.error(f"Database insertion failed: {e}")
        # In a script, you might want to see the real error rather than just a 500
        raise e


async def search_similar(
    text_query: str, 
    top_k: int = 5,
    conn: asyncpg.Connection = Depends(get_db_conn)
) -> list[dict]:
    """
    Search similar chunks using pgvector cosine distance.
    """
    # 1. Encode the query
    query_emb = model.encode([text_query])[0].tolist() # Convert to list for asyncpg

    # 2. Execute the query using conn.fetch (returns list of asyncpg.Record)
    results = await conn.fetch("""
        SELECT 
            id,
            text,
            metadata,
            embedding <=> $1::vector AS distance
        FROM embeddings
        ORDER BY embedding <=> $1::vector ASC
        LIMIT $2;
    """, 
        query_emb,  # $1
        top_k       # $2
    )

    # 3. Convert asyncpg.Record objects to standard Python dicts
    return [dict(record) for record in results]
    
    # NOTE: No explicit conn.close() here! The dependency handles release.