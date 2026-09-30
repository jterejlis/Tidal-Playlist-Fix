import re
import hashlib


def normalize_title(title: str):
    if not title:
        return ""

    title = title.lower()

    # usuń feat / remix / version
    title = re.sub(r"\(.*?feat.*?\)", "", title)
    title = re.sub(r"\b(feat|ft|remix|version)\b.*", "", title)

    title = re.sub(r"[^a-z0-9\s]", "", title)
    title = re.sub(r"\s+", " ", title).strip()

    return title

def normalize_artists(artists):
    return set(a.lower().strip() for a in artists or [])

def title_fingerprint(title: str):
    clean = normalize_title(title)
    return hashlib.md5(clean.encode()).hexdigest() if clean else None



