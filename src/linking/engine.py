from .loaders.load_entities import load_entities
from .candidates.people_entity import find_people_entity_candidates
from .candidates.people_people import find_people_people_candidates
from .confirm.entity_link import confirm_entity_link
from .confirm.people_link import confirm_people_link
from .inserters.entity_link import insert_entity_link
from .inserters.people_link import insert_people_people_link


async def run_linking_engine(conn, document_id):
    entities, chunks = await load_entities(conn, document_id)

    # 1️⃣ People ↔ Heritage / Festival
    for chunk in chunks:
        candidates = find_people_entity_candidates(chunk, entities)

        for cand in candidates:
            result = await confirm_entity_link(
                chunk,
                cand["from_name"],
                cand["to_name"]
            )

            if result.get("related"):
                await insert_entity_link(
                    conn,
                    cand,
                    result["relation"],
                    document_id
                )

    # 2️⃣ People ↔ People
    people_candidates = find_people_people_candidates(chunks, entities["people"])

    for cand in people_candidates:
        result = await confirm_people_link(
            cand["text"],
            cand["name_a"],
            cand["name_b"]
        )

        if result.get("related"):
            await insert_people_people_link(
                conn,
                cand,
                result["relation"],
                document_id
            )
