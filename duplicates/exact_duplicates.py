from collections import defaultdict


def find_exact_duplicates(tracks):
    occurrences = defaultdict(list)

    for i, t in enumerate(tracks):
        occurrences[t["id"]].append(i)

    duplicates = []

    for track_id, indexes in occurrences.items():
        if len(indexes) > 1:
            duplicates.append({
                "track_id": track_id,
                "count": len(indexes),
                "positions": indexes,
                "track": tracks[indexes[0]]  
            })

    return duplicates