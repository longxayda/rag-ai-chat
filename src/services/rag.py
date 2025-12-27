import numpy as np
from sentence_transformers import SentenceTransformer
from uuid import UUID
import uuid
import json

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
model = SentenceTransformer(EMBEDDING_MODEL)

async def insert_embeddings(conn, chunks: list[dict], embeddings: np.ndarray):
    query = """
        INSERT INTO embeddings (
            id, document_id, text, embedding, chunk_index, metadata
        )
        VALUES ($1, $2, $3, $4::vector, $5, $6::jsonb)
        ON CONFLICT (id) DO NOTHING
    """

    records = []
    for chunk, emb in zip(chunks, embeddings):
        records.append((
            chunk.get("id", "fallback-id"),
            chunk["document_id"],
            chunk.get("text", ""),
            emb.tolist(),           # list → text cast by SQL
            chunk.get("chunk_index", 0),
            json.dumps(chunk.get("metadata", {}))
        ))

    async with conn.transaction():
        await conn.executemany(query, records)


async def insert_document(conn, document_id, filename, source_path, file_hash):
    await conn.execute("""
        INSERT INTO documents (id, filename, source_path, file_hash, status)
        VALUES ($1, $2, $3, $4, 'PROCESSING')
        ON CONFLICT (id) DO NOTHING
    """, document_id, filename, source_path, file_hash)


async def search_similar(text_query: str, top_k: int, conn) -> list[dict]:
    """
    Search similar chunks using pgvector cosine distance.
    """
    # 1. Encode the query
    query_emb = model.encode([text_query])[0].tolist() # Convert to list for asyncpg

    # 2. Execute the query using conn.fetch (returns list of asyncpg.Record)
    results = await conn.fetch("""
        SELECT id, text, metadata, embedding <=> $1::vector AS distance
        FROM embeddings
        ORDER BY embedding <=> $1::vector ASC
        LIMIT $2;
    """, 
        query_emb,  # $1
        top_k       # $2
    )

    # 3. Convert asyncpg.Record objects to standard Python dicts
    return [dict(record) for record in results]

async def search_heritage_chunks(
    conn,
    document_id: UUID,
    query_embedding: list[float],
    top_k: int = 5
):
    return await conn.fetch("""
        SELECT text
        FROM embeddings
        WHERE document_id = $1
        ORDER BY embedding <=> $2::vector
        LIMIT $3
    """, document_id, query_embedding, top_k)
    
async def insert_heritages(conn, document_id, heritages: list[dict]):
    query = """
    INSERT INTO heritages
    (id, name, location, type, year, description, image, category, document_id)
    VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
    ON CONFLICT DO NOTHING
    """

    for h in heritages:
        if not h.get("name"):
            continue  # 🚨 chặn lỗi NULL name

        await conn.execute(
            query,
            uuid.uuid4(),
            h["name"].strip(),
            h.get("location"),
            h.get("type"),
            h.get("year"),
            h.get("description"),
            None,
            h.get("category"),
            document_id
        )
        
async def insert_people(conn, document_id, people: list[dict]):
    query = """
    INSERT INTO people
    (id, name, birth_year, death_year, role, associated_place, description, document_id)
    VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
    ON CONFLICT DO NOTHING
    """

    for p in people:
        if not p.get("name"):
            continue

        await conn.execute(
            query,
            uuid.uuid4(),
            p["name"].strip(),
            p.get("birth_year"),
            p.get("death_year"),
            p.get("role"),
            p.get("associated_place"),
            p.get("description"),
            document_id
        )