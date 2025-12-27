def find_people_people_candidates(chunks, people):
    results = []

    for text in chunks:
        for i, p1 in enumerate(people):
            for p2 in people[i + 1:]:
                if p1["name"] in text and p2["name"] in text:
                    results.append({
                        "person_id": p1["id"],
                        "related_person_id": p2["id"],
                        "name_a": p1["name"],
                        "name_b": p2["name"],
                        "text": text
                    })

    return results
