async def get_heritages(conn):
    query = """
        SELECT
            id,
            name,
            location,
            type,
            year,
            description,
            document_id,
            created_at
        FROM heritages
        ORDER BY created_at DESC
    """
    return await conn.fetch(query)