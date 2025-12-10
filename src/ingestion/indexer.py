import os
import json
import sys
import psycopg2
from psycopg2.extras import execute_values
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from psycopg2 import pool, OperationalError, errorcodes, errors

load_dotenv()

EMBEDDING_MODEL = "all-MiniLM-L6-v2"

model = SentenceTransformer(EMBEDDING_MODEL)


config = {
    "host": os.getenv("POSTGRES_HOST"),
    "port": int(os.getenv("POSTGRES_PORT")) or 5432,
    "dbname": os.getenv("POSTGRES_NAME"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD")
}


connection_pool = pool.ThreadedConnectionPool(1, 20, **config)




def print_psycopg2_exception(err):
    err_type, err_obj, traceback = sys.exc_info()
    line_num = traceback.tb_lineno
    
    print ("\npsycopg2 ERROR:", err, "on line number:", line_num)
    print ("psycopg2 traceback:", traceback, "-- type:", err_type)

    # psycopg2 extensions.Diagnostics object attribute
    print ("\nextensions.Diagnostics:", err.diag)

    # print the pgcode and pgerror exceptions
    print ("pgerror:", err.pgerror)
    print ("pgcode:", err.pgcode, "\n")

def init_db() -> None:
    """
    Connect to Postgres and create table if exists
    """
    if conn != None:
        cur = conn.cursor()

        try:
            cur.execute("""
                CREATE EXTENSION IF NOT EXISTS vector;
                
                CREATE TABLE IF NOT EXISTS embeddings (
                    id TEXT PRIMARY KEY,               -- chunk id
                    text TEXT NOT NULL,                -- chunk text
                    embedding VECTOR(384) NOT NULL,    -- pgvector column
                    chunk_index INT NOT NULL,          -- chunk index for ordering
                    metadata JSONB,                    -- any metadata from your chunker
                    created_at TIMESTAMP DEFAULT NOW() -- optional timestamp
                );
            """)
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print_psycopg2_exception(e)
            conn.rollback()
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()
    


def insert_embeddings(chunks: list[dict], embeddings) -> None:
    """
    Insert embedding vectors to embeddings table
    """
    conn = get_connection()
    cur = conn.cursor()

    rows = []
    for chunk, emb in zip(chunks, embeddings):
        rows.append((
            chunk["id"],                     
            chunk["text"],
            emb.tolist(),              
            chunk["chunk_index"],
            json.dumps(chunk.get("metadata", {}))
        ))

    execute_values(cur,
        """
        INSERT INTO embeddings (id, text, embedding, chunk_index, metadata)
        VALUES %s
        ON CONFLICT (id) DO UPDATE SET
            embedding = EXCLUDED.embedding,
            metadata  = EXCLUDED.metadata
        """,
        rows,
        template="(%s, %s, %s::vector, %s, %s)"
    )

    conn.commit()
    cur.close()
    conn.close()


def search_similar(text_query: str, top_k: int = 5) -> list[tuple]:
    """
    Search similar chunks using pgvector cosine distance.
    """
    query_emb = model.encode([text_query])[0]

    conn = get_connection()
    if not conn:
        raise 
    cur = conn.cursor()

    results: list[tuple]
    
    cur.execute("""
        SELECT 
            id,
            text,
            metadata,
            embedding <=> %s::vector AS distance
        FROM embeddings
        ORDER BY embedding <=> %s::vector ASC
        LIMIT %s;
    """, (
        query_emb.tolist(),
        query_emb.tolist(),
        top_k
    ))

    results = cur.fetchall()

    cur.close()
    conn.close()

    return results

# test DB connection
if __name__ == "__main__":
    conn = get_connection()
    if conn:
        print("Connect DB success")
    conn.close()