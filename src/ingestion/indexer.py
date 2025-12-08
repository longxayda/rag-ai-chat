import psycopg2
from psycopg2.extras import execute_values
import json
from sentence_transformers import SentenceTransformer
import os
from dotenv import load_dotenv

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

def get_connection():
    """
    Connect to Postgres
    """
    return psycopg2.connect(**config)

def init_db():
    """
    Connect to Postgres and create table if exists
    """
    conn = get_connection()
    cur = conn.cursor()

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


def insert_documents(chunks):
    """
    Insert parent documents to documents table only once.
    """
    conn = get_connection()
    cur = conn.cursor()

    # group chunks by parent doc ID
    docs = {}
    for c in chunks:
        doc_id = c["id"].split("_chunk_")[0]
        if doc_id not in docs:
            docs[doc_id] = {
                "content": "",
                "metadata": c.get("metadata", {})
            }
        docs[doc_id]["content"] += c["text"] + "\n"

    data = [(doc_id, d["content"], json.dumps(d["metadata"]))
            for doc_id, d in docs.items()]

    execute_values(cur,
        """
        INSERT INTO documents (id, content, metadata)
        VALUES %s
        ON CONFLICT (id) DO NOTHING
        """,
        data
    )

    conn.commit()
    cur.close()
    conn.close()


def insert_embeddings(chunks, embeddings):
    """
    Insert embedding vectors to embeddings table
    """
    conn = get_connection()
    cur = conn.cursor()

    rows = []
    for chunk, emb in zip(chunks, embeddings):
        rows.append((
            chunk["id"],                       # id
            chunk["text"], 
            emb.tolist(),                      # embedding as python list
            chunk["chunk_index"],              # chunk number
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


def search_similar(text_query: str, top_k=5):
    """
    Search similar chunks using pgvector cosine distance.
    """
    query_emb = model.encode([text_query])[0]

    conn = get_connection()
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