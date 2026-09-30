from datetime import datetime
import re
import hashlib
import json
from collections import defaultdict
from itertools import combinations

from core.normalisation import normalize_title, title_fingerprint
from core.similarity import duplicate_score, is_strong_duplicate


def aggregate_tracks(tracks: list[dict]):
    groups = {}

    for t in tracks:
        title = t.get("name", "")
        normalized = normalize_title(title)

        if not normalized:
            continue

        fp = title_fingerprint(normalized)

        # fallback jeśli fingerprint nie działa
        key = fp if fp else normalized
        
        groups.setdefault(key, []).append(t)
   
    return groups


def find_duplicates(tracks: list[dict], threshold=0.8):
    groups = aggregate_tracks(tracks)

    duplicates = []

    for group in groups.values():
        for t1, t2 in combinations(group, 2):
            score = duplicate_score(t1, t2)
            if score >= threshold:
                duplicates.append(
                    {
                        "track1": t1,
                        "track2": t2,
                        "score": score
                    }
                )
    return duplicates
