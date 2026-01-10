import numpy as np
from sentence_transformers import SentenceTransformer
from uuid import UUID
import uuid
import json
import re
from typing import List, Dict

# EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_MODEL = "keepitreal/vietnamese-sbert"
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
            emb.tolist(),                 # pgvector OK
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
        ORDER BY distance ASC
        LIMIT $2;
    """, 
        query_emb,  # $1
        top_k       # $2
    )

    # 3. Convert asyncpg.Record objects to standard Python dicts
    return [dict(record) for record in results]


async def hybrid_search(
    text_query: str, 
    top_k: int, 
    conn,
    boost_exact_match: bool = True
) -> List[Dict]:
    """
    Hybrid search combining vector similarity with keyword boosting.
    
    Args:
        text_query: Search query
        top_k: Number of results
        conn: Database connection
        boost_exact_match: Whether to boost exact name matches
    
    Returns:
        List of results sorted by relevance
    """
    # 1. Encode the query
    query_emb = model.encode([text_query])[0].tolist()
    
    # 2. Extract potential names (Vietnamese proper nouns in CAPS)
    # This captures patterns like "Hồ Thị Kỷ", "Cao Triều Phát", etc.
    name_pattern = r'[A-ZĐÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴ][a-zàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵ]*(?:\s+[A-ZĐÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴ][a-zàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵ]*){1,3}'
    potential_names = re.findall(name_pattern, text_query)
    
    # 3. Execute vector search
    results = await conn.fetch("""
        SELECT 
            id, 
            text, 
            metadata, 
            embedding <=> $1::vector AS distance
        FROM embeddings
        ORDER BY distance ASC
        LIMIT $2;
    """, 
        query_emb,
        top_k * 2  # Get more results for re-ranking
    )
    
    # 4. Convert to dicts and apply hybrid scoring
    processed_results = []
    for record in results:
        result = dict(record)
        
        distance = result['distance']
        text_lower = result['text'].lower()
        
        # Boost score if exact name match found
        if boost_exact_match and potential_names:
            for name in potential_names:
                if name.lower() in text_lower:
                    # Reduce distance significantly for exact matches
                    # This makes exact name matches rank higher
                    distance = distance * 0.5
                    result['boosted'] = True
                    break
        
        result['final_score'] = distance
        processed_results.append(result)
    
    # 5. Re-sort by final score and return top_k
    processed_results.sort(key=lambda x: x['final_score'])
    return processed_results[:top_k]


async def search_with_context_expansion(
    text_query: str,
    top_k: int,
    conn,
    expand_neighbors: int = 1
) -> list[dict]:
    """
    Search similar chunks and automatically include adjacent chunks
    to provide complete context.
    
    Args:
        text_query: Search query
        top_k: Number of initial results
        conn: Database connection
        expand_neighbors: Number of adjacent chunks to include (before/after)
    
    Returns:
        List of expanded results with complete context
    """
    # 1. Get initial results
    query_emb = model.encode([text_query])[0].tolist()
    
    initial_results = await conn.fetch("""
        SELECT id, text, metadata, embedding <=> $1::vector AS distance
        FROM embeddings
        ORDER BY distance ASC
        LIMIT $2;
    """, query_emb, top_k)
    
    if not initial_results:
        return []
    
    # 2. Extract chunk IDs and get adjacent chunks
    # Assumes your chunks have sequential IDs or document_id + chunk_index in metadata
    expanded_ids = set()
    for result in initial_results:
        chunk_id = result['id']
        expanded_ids.add(chunk_id)
        
        # Add adjacent chunks (requires sequential IDs or metadata tracking)
        for offset in range(-expand_neighbors, expand_neighbors + 1):
            if offset != 0:
                adjacent_id = chunk_id + offset
                expanded_ids.add(adjacent_id)
    
    # 3. Fetch all expanded chunks
    expanded_results = await conn.fetch("""
        SELECT id, text, metadata, 0 AS distance
        FROM embeddings
        WHERE id = ANY($1::int[])
        ORDER BY id ASC;
    """, list(expanded_ids))
    
    return [dict(r) for r in expanded_results]




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