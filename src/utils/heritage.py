from ..services.rag import search_heritage_chunks
from ..ingestion import embedder

HERITAGE_QUERIES = [
    "di sản văn hóa",
    "di tích lịch sử",
    "địa danh lịch sử",
    "lễ hội truyền thống",
    "nhân vật lịch sử",
    "văn hóa dân gian",
    "di sản phi vật thể",
    "di sản vật thể",
    "văn hóa địa phương Cà Mau"
]

async def collect_relevant_chunks(conn, document_id):
    collected = set()

    for query in HERITAGE_QUERIES:
        query_embedding = await embedder.embed_query(query)

        rows = await conn.fetch("""
            SELECT text
            FROM embeddings
            WHERE document_id = $1
            ORDER BY embedding <=> $2::vector
            LIMIT 5
        """, document_id, query_embedding)

        for r in rows:
            collected.add(r["text"])

    return list(collected)


def build_context(chunks) -> str:
    context_blocks = []

    for i, row in enumerate(chunks, 1):
        source = row["metadata"].get("file_name", "unknown")
        text = row["text"].strip()

        context_blocks.append(
            f"[Source {i} | {source}]\n{text}"
        )

    return "\n\n".join(context_blocks)


def build_prompt(question: str, context: str) -> list[dict]:
    return [
        {
            "role": "system",
            "content": (
                "Bạn là trợ lý AI chuyên về di sản văn hóa tỉnh Cà Mau. "
                "Chỉ sử dụng thông tin trong ngữ cảnh được cung cấp. "
                "Nếu không có thông tin phù hợp, hãy nói rõ rằng không tìm thấy dữ liệu."
            )
        },
        {
            "role": "user",
            "content": f"""
                Ngữ cảnh:
                {context}

                Câu hỏi:
                {question}

                Yêu cầu:
                - Trả lời bằng tiếng Việt
                - Phù hợp với học sinh
                - Không suy đoán ngoài dữ liệu
            """
        }
    ]
