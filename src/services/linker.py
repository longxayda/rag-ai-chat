import uuid

async def insert_people_heritage_link(conn, person_id, heritage_id, relation, document_id):
    await conn.execute("""
        INSERT INTO heritage_links
        (id, heritage_id, person_id, relation, document_id)
        VALUES ($1,$2,$3,$4,$5)
        """,
        uuid.uuid4(),
        heritage_id,
        person_id,
        relation,
        document_id
    )
