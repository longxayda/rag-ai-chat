def find_people_entity_candidates(text, entities):
    candidates = []

    for p in entities["people"]:
        if p["name"] not in text:
            continue

        for h in entities["heritages"]:
            if h["name"] in text:
                candidates.append({
                    "from_type": "people",
                    "from_id": p["id"],
                    "from_name": p["name"],
                    "to_type": "heritage",
                    "to_id": h["id"],
                    "to_name": h["name"],
                    "text": text
                })

        for f in entities["festivals"]:
            if f["name"] in text:
                candidates.append({
                    "from_type": "people",
                    "from_id": p["id"],
                    "from_name": p["name"],
                    "to_type": "festival",
                    "to_id": f["id"],
                    "to_name": f["name"],
                    "text": text
                })

    return candidates
