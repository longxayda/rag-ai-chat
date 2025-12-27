async def insert_entity_link(conn, cand, relation, document_id):
    if cand["to_type"] == "heritage":
        await conn.execute(
            """
            INSERT INTO people_heritage_links
            (people_id, heritage_id, relation, document_id)
            VALUES ($1,$2,$3,$4)
            ON CONFLICT DO NOTHING
            """,
            cand["from_id"],
            cand["to_id"],
            relation,
            document_id
        )

    elif cand["to_type"] == "festival":
        await conn.execute(
            """
            INSERT INTO people_festival_links
            (people_id, festival_id, relation, document_id)
            VALUES ($1,$2,$3,$4)
            ON CONFLICT DO NOTHING
            """,
            cand["from_id"],
            cand["to_id"],
            relation,
            document_id
        )
