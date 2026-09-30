from difflib import SequenceMatcher
from datetime import datetime
from core.similarity import score_candidate


def is_valid_candidate(track):
    name = track["name"].lower()

    blacklist = ["live", "remix", "karaoke", "instrumental"]

    return not any(word in name for word in blacklist)


def build_search_query(track, max_artists=3):
    artists = track.get("artists", []) or []
    if max_artists is not None and len(artists) > max_artists:
        artists = artists[:max_artists]

    query = track.get("name", "")
    if artists:
        query = f"{query} {' '.join(artists)}"
    return query.strip()


def build_search_queries(track):
    # Try progressively simpler search queries for tracks with many artists.
    yield build_search_query(track, max_artists=3)
    yield build_search_query(track, max_artists=1)
    yield build_search_query(track, max_artists=0)


def find_best_match(search_engine, track, threshold=0.0, limit=10):
    best = None
    best_score = 0
    seen_queries = set()

    for query in build_search_queries(track):
        if not query or query in seen_queries:
            continue

        seen_queries.add(query)
        results = search_engine.search(query, limit=limit)["items"]

        for candidate in results:
            if candidate.get("id") == track.get("id"):
                continue

            if not is_valid_candidate(candidate):
                continue

            score = score_candidate(track, candidate)

            if score > best_score:
                best = candidate
                best_score = score

        if threshold > 0 and best_score >= threshold:
            break

    if best_score >= threshold:
        return best, best_score

    return None, best_score


def find_replacement(search_engine, track, replace_threshold=0.75, ask_threshold=0.65):
    best = None
    best_score = 0

    for limit in (10, 20, 30):
        candidate, score = find_best_match(search_engine, track, threshold=0.0, limit=limit)
        if score > best_score:
            best = candidate
            best_score = score

        if best_score >= replace_threshold:
            break

    if not best:
        return {
            "original": track,
            "replacement": None,
            "action": "KEEP",
            "reason": "No better match found",
            "score": best_score
        }

    if best["id"] == track["id"]:
        return {
            "original": track,
            "replacement": None,
            "action": "KEEP",
            "reason": "Same track",
            "score": best_score
        }

    if best_score >= replace_threshold:
        return {
            "original": track,
            "replacement": best,
            "action": "REPLACE",
            "score": best_score,
            "reason": "High confidence replacement"
        }

    if best_score >= ask_threshold:
        return {
            "original": track,
            "replacement": best,
            "action": "ASK",
            "score": best_score,
            "reason": "Borderline replacement, manual review recommended"
        }

    return {
        "original": track,
        "replacement": None,
        "action": "KEEP",
        "reason": "No replacement above threshold",
        "score": best_score
    }


def build_replacement_report(search_engine, dead_tracks, ask_threshold=0.95):
    report = {
        "generated_at": datetime.now().isoformat(),
        "total_dead": len(dead_tracks),
        "items": []
    }

    for track in dead_tracks:
        best, score = find_best_match(search_engine, track, threshold=0.0)

        if not best:
            report["items"].append({
                "original": track,
                "replacement": None,
                "score": score,
                "action": "KEEP",
                "reason": "No candidate replacement found"
            })
            continue

        if best["id"] == track.get("id"):
            report["items"].append({
                "original": track,
                "replacement": None,
                "score": score,
                "action": "KEEP",
                "reason": "Best match is the same track"
            })
            continue

        action = "REPLACE" if score >= ask_threshold else "ASK"
        reason = "High confidence replacement" if score >= ask_threshold else "Manual approval recommended"

        report["items"].append({
            "original": track,
            "replacement": best,
            "score": score,
            "action": action,
            "reason": reason
        })

    return report
