from ..exceptions.exceptions import DocumentNotFound

async def get_document(doc_id: str, conn):
    doc = await conn.fetchrow(
        "SELECT * FROM documents WHERE doc_id = $1", doc_id
    )
    if not doc:
        raise DocumentNotFound(doc_id=doc_id)
    
    return dict(doc)