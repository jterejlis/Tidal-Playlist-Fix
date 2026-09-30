from difflib import SequenceMatcher
import hashlib
from core.normalisation import normalize_title, normalize_artists, title_fingerprint



def title_similarity(n1: str, n2: str):
    if not n1 or not n2:
        return 0.0
    return SequenceMatcher(None, n1, n2).ratio()


def is_strong_duplicate(t1, t2):
    title1 = normalize_title(t1.get("name", ""))
    title2 = normalize_title(t2.get("name", ""))

    if title1 != title2:
        return False

    artists1 = set(a.lower() for a in t1.get("artists", []) if a)
    artists2 = set(a.lower() for a in t2.get("artists", []) if a)

    if artists1 & artists2:
        return True

    return False


def duplicate_score(t1: dict, t2: dict):
    if t1.get("isrc") and t1["isrc"] == t2.get("isrc"):
        return 1.0
    
    if is_strong_duplicate(t1, t2):
        return 1.0

def artist_similarity(a1: list[str], a2: list[str]):
    set1 = set(a.lower().strip() for a in a1 if a)
    set2 = set(a.lower().strip() for a in a2 if a)

    if not set1 or not set2:
        return 0.0

    intersection = set1.intersection(set2)
    if not intersection:
        return 0.0

    coverage1 = len(intersection) / len(set1)
    coverage2 = len(intersection) / len(set2)

    return (coverage1 + coverage2) / 2

def duplicate_score(t1: dict, t2: dict):
    if t1.get("isrc") and t1["isrc"] == t2.get("isrc"):
        return 1.0
    
    if is_strong_duplicate(t1, t2):
        return 1.0

    title_sim = title_similarity(t1.get("name", ""), t2.get("name", ""))
    artist_sim = artist_similarity(t1.get("artists", []), t2.get("artists", []))

    return (title_sim * 0.7) + (artist_sim * 0.3)

def score_candidate(original, candidate):
    title_score = title_similarity(
        normalize_title(original.get("name", "")),
        normalize_title(candidate.get("name", ""))
    )
    artist_score = artist_similarity(
        original.get("artists", []),
        candidate.get("artists", [])
    )

    if original.get("isrc") and candidate.get("isrc"):
        if original["isrc"] == candidate["isrc"]:
            return 1.0

    orig_title = normalize_title(original.get("name", ""))
    cand_title = normalize_title(candidate.get("name", ""))

    if orig_title and cand_title:
        if orig_title == cand_title or orig_title in cand_title or cand_title in orig_title:
            if artist_score >= 0.5:
                return 0.95

    return 0.7 * title_score + 0.3 * artist_score

def artist_consistency_score(cluster, tracks_data):
    artists_sets = []

    for tid in cluster:
        track = tracks_data.get(tid)
        if not track:
            continue

        normalized = normalize_artists(track.get("artists", []))
        if normalized:
            artists_sets.append(normalized)

    if not artists_sets:
        return 0.0

    base = artists_sets[0]

    overlaps = []
    for a in artists_sets:
        if not base or not a:
            overlaps.append(0.0)
        else:
            overlaps.append(len(base.intersection(a)) / len(base.union(a)))

    return sum(overlaps) / len(overlaps) if overlaps else 0.0

