from collections import defaultdict
from core.similarity import artist_consistency_score

def build_decisions(duplicates):
    graph = defaultdict(list)
    tracks_data = {}

    # 1. build graph + registry
    for d in duplicates:
        t1 = d["track1"]
        t2 = d["track2"]
        score = d["score"]

        tracks_data[t1["id"]] = t1
        tracks_data[t2["id"]] = t2

        graph[t1["id"]].append((t2["id"], score))
        graph[t2["id"]].append((t1["id"], score))

    visited = set()
    clusters = []

    # 2. DFS clustering
    def dfs(start, cluster):
        stack = [start]

        while stack:
            node = stack.pop()

            if node in visited:
                continue

            visited.add(node)
            cluster.append(node)

            for neigh_id, _ in graph[node]:
                if neigh_id not in visited:
                    stack.append(neigh_id)

    for node in graph:
        if node not in visited:
            cluster = []
            dfs(node, cluster)
            clusters.append(cluster)

    # 3. decisions
    decisions = []

    for cluster in clusters:
        decisions.append(
            decide_cluster(cluster, graph, tracks_data)
        )

    decisions = [d for d in decisions if d is not None]

    return decisions

def decide_cluster(cluster, graph, tracks_data):
    scores = []

    # similarity scores from graph
    for node in cluster:
        for neigh_id, score in graph[node]:
            scores.append(score)

    avg_score = sum(scores) / len(scores) if scores else 0.0

    artist_score = artist_consistency_score(cluster, tracks_data)

    final_confidence = (avg_score * 0.8) + (artist_score * 0.2)

    group_tracks = [tracks_data[i] for i in cluster if i in tracks_data]

    if len(cluster) < 2:
        return None

    if final_confidence >= 0.95:
        return {
            "group": group_tracks,
            "action": "MERGE",
            "confidence": final_confidence,
            "reason": "Near-perfect duplicates (high similarity + artist match)"
        }

    if final_confidence >= 0.85:
        return {
            "group": group_tracks,
            "action": "REVIEW",
            "confidence": final_confidence,
            "reason": "High similarity but possible remix/feature/version difference"
        }

    return {
        "group": group_tracks,
        "action": "KEEP",
        "confidence": final_confidence,
        "reason": "Low confidence duplication signal"
    }

def apply_decisions(tracks, decisions):

    def extract_id(item):
        if isinstance(item, dict):
            return item.get("id")
        return item

    track_map = {t["id"]: t for t in tracks}

    to_remove = set()

    for decision in decisions:
        action = decision.get("action")
        group = decision.get("group", [])

        if len(group) < 2:
            continue

        if action == "MERGE":
            for item in group[1:]:
                track_id = extract_id(item)
                if track_id in track_map:
                    to_remove.add(track_id)

        elif action == "REVIEW":
            continue

        elif action == "KEEP":
            continue

    cleaned = [
        t for t in tracks
        if t["id"] not in to_remove
    ]

    return cleaned