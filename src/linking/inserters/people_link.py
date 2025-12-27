# linking/inserters/people_link.py

async def insert_people_people_link(
    conn,
    cand: dict,
    relation: str,
    document_id
):
    """
    cand = {
        person_id,
        related_person_id,
        name_a,
        name_b,
        text
    }
    """

    await conn.execute(
        """
        INSERT INTO people_links (
            id,
            person_id,
            related_person_id,
            relation,
            document_id
        )
        VALUES (
            gen_random_uuid(),
            $1, $2, $3, $4
        )
        ON CONFLICT DO NOTHING
        """,
        cand["person_id"],
        cand["related_person_id"],
        relation,
        document_id
    )
