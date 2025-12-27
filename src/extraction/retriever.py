from .queries import HERITAGE_QUERIES, PEOPLE_QUERIES
from ..ingestion.embedder import embed_query

MAX_CHUNKS = 20  # 🚨 cực kỳ quan trọng cho Gemma 1B

async def collect_heritage_chunks(conn, document_id, top_k_per_query=3):
    collected = {}

    for query in HERITAGE_QUERIES:
        q_emb = await embed_query(query)

        rows = await conn.fetch(
            """
            SELECT text
            FROM embeddings
            WHERE document_id = $1
            ORDER BY embedding <=> $2::vector
            LIMIT $3
            """,
            document_id,
            q_emb,
            top_k_per_query
        )

        for r in rows:
            collected[r["text"]] = True

        if len(collected) >= MAX_CHUNKS:
            break

    return list(collected.keys())[:MAX_CHUNKS]

async def collect_people_chunks(conn, document_id, top_k_per_query=4):
    collected = {}

    for query in PEOPLE_QUERIES:
        q_emb = await embed_query(query)

        rows = await conn.fetch(
            """
            SELECT text
            FROM embeddings
            WHERE document_id = $1
            ORDER BY embedding <=> $2::vector
            LIMIT $3
            """,
            document_id,
            q_emb,
            top_k_per_query
        )

        for r in rows:
            collected[r["text"]] = True

        if len(collected) >= MAX_CHUNKS:
            break

    return list(collected.keys())[:MAX_CHUNKS]

