async def load_entities(conn, document_id):
    people = [dict(r) for r in await conn.fetch(
        "SELECT id,name FROM people WHERE document_id=$1",
        document_id
    )]

    heritages = [dict(r) for r in await conn.fetch(
        "SELECT id,name FROM heritages WHERE document_id=$1",
        document_id
    )]

    festivals = [dict(r) for r in await conn.fetch(
        "SELECT id,name FROM festivals WHERE document_id=$1",
        document_id
    )]

    chunks = [
        r["text"] for r in await conn.fetch(
            "SELECT text FROM embeddings WHERE document_id=$1 LIMIT 30",
            document_id
        )
    ]

    return {
        "people": people,
        "heritages": heritages,
        "festivals": festivals
    }, chunks
