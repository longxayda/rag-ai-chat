import uuid

async def insert_people_people_link(
    conn,
    person_id,
    related_person_id,
    relation,
    document_id
):
    await conn.execute("""
        INSERT INTO people_links
        (id, person_id, related_person_id, relation, document_id)
        VALUES ($1,$2,$3,$4,$5)
        ON CONFLICT DO NOTHING
    """,
        uuid.uuid4(),
        person_id,
        related_person_id,
        relation,
        document_id
    )
