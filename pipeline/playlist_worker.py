
from copy import deepcopy
from matching.replacement import find_replacement
from duplicates.find_duplicates import find_duplicates
from duplicates.exact_duplicates import find_exact_duplicates
from duplicates.cleaning_decision import build_decisions, apply_decisions
from core.core import export_playlist
import json
from datetime import datetime


def process_playlist(

    tracks,

    search_engine,

    audit=None,

    audit_path=None,

    export_path=None,

    missing_replacements_path=None,

    replace_threshold=0.8,

    ask_threshold=0.7

):

    """

    Full pipeline:

    1. Normalize input

    2. Apply replacements (dead track fixing)

    3. Health audit (optional input)

    4. Duplicate detection + decisions

    5. Apply deduplication decisions

    6. Export (optional)

    """

 

    working = [normalize_track(t) for t in deepcopy(tracks)]

  

    working, replacement_report = apply_replacements(

        working,

        search_engine,

        audit=audit,

        audit_path=audit_path,

        missing_replacements_path=missing_replacements_path,

        replace_threshold=replace_threshold,

        ask_threshold=ask_threshold

    )

    if replacement_report.get("manual_review"):
        print("Manual review candidates found. Running manual acceptance now...")
        working = manual_accept_replacements(
            working,
            replacement_report,
            export_path=None
        )
        print("Manual acceptance complete. Continuing duplicate detection.")

    exact_duplicates = find_exact_duplicates(working)
    if exact_duplicates:
        removed_exact = sum(d["count"] - 1 for d in exact_duplicates)
        print(f"Removing {removed_exact} exact duplicate track(s) before duplicate analysis.")
        working = remove_exact_duplicates(working)

    duplicates = find_duplicates(working)

    decisions = build_decisions(duplicates)

    working = apply_decisions(working, decisions)


    if export_path:

        with open(export_path, "w", encoding="utf-8") as f:

            json.dump({"items": working}, f, ensure_ascii=False, indent=2)

    return working
def apply_replacements(tracks, search_engine, audit=None, audit_path=None, missing_replacements_path=None, replace_threshold=0.8, ask_threshold=0.7):

    if audit is None:

        if audit_path is None:

            raise ValueError("Provide either audit or audit_path")

        with open(audit_path, "r") as f:

            audit = json.load(f)

    dead_ids = {t["id"] for t in audit.get("dead", [])}

    unknown_ids = {t["id"] for t in audit.get("unknown", [])}

    bad_tracks = [
        t for t in tracks
        if t.get("id") in dead_ids or t.get("id") in unknown_ids
    ]
    total_bad = len(bad_tracks)

    if total_bad:
        print(f"Searching replacements for dead/unknown tracks: 0/{total_bad}", end="\r", flush=True)

    result = []
    processed = 0
    replaced = 0
    asked = 0
    removed = 0

    failed_replacements = []
    manual_review = []

    for t in tracks:

        track_id = t.get("id")

        if track_id in dead_ids or track_id in unknown_ids:

            processed += 1
            print(
                f"Searching replacements for dead/unknown tracks: {processed}/{total_bad} - {t.get('name', '<unknown>')} (id={track_id})",
                end="\r",
                flush=True
            )

            replacement = find_replacement(
                search_engine,
                t,
                replace_threshold=replace_threshold,
                ask_threshold=ask_threshold
            )

            if replacement["action"] == "REPLACE":

                result.append(replacement["replacement"])
                replaced += 1

            elif replacement["action"] == "ASK":

                asked += 1
                candidate = replacement["replacement"]
                manual_review.append({
                    "id": track_id,
                    "original": {
                        "id": track_id,
                        "name": t.get("name"),
                        "artists": t.get("artists", [])
                    },
                    "candidate": candidate,
                    "score": replacement.get("score"),
                    "reason": replacement.get("reason"),
                    "status": "DEAD" if track_id in dead_ids else "UNKNOWN"
                })
                result.append(t)

            else:

                removed += 1
                failed_replacements.append({
                    "id": track_id,
                    "name": t.get("name"),
                    "artists": t.get("artists", []),
                    "status": "DEAD" if track_id in dead_ids else "UNKNOWN",
                    "reason": replacement.get("reason", "No replacement")
                })

        else:

            result.append(t)

    if total_bad:
        not_restored = total_bad - replaced
        print(
            f"Replacement search finished: {processed}/{total_bad} processed, {replaced} replaced, {asked} edge-case candidates, {removed} removed."
        )
        print(f"Tracks not restored: {not_restored} of {total_bad}")

        if failed_replacements or manual_review:
            if missing_replacements_path:
                with open(missing_replacements_path, "w", encoding="utf-8") as f:
                    json.dump({
                        "generated_at": datetime.now().isoformat(),
                        "removed": failed_replacements,
                        "manual_review": manual_review
                    }, f, ensure_ascii=False, indent=2)
                print(f"Saved replacement report to {missing_replacements_path}")
            else:
                sample = failed_replacements[:20]
                if sample:
                    print("First failed replacements:")
                    for item in sample:
                        print(
                            f" - {item['name']} (id={item['id']}), status={item['status']}, reason={item['reason']}"
                        )
                    if len(failed_replacements) > 20:
                        print(f"... and {len(failed_replacements) - 20} more")

    return result, {
        "generated_at": datetime.now().isoformat(),
        "removed": failed_replacements,
        "manual_review": manual_review,
        "total_bad": total_bad,
        "replaced": replaced,
        "asked": asked,
        "removed_count": removed,
        "not_restored": total_bad - replaced
    }


def manual_accept_replacements(tracks, report_source, export_path=None):
    if isinstance(report_source, dict):
        report = report_source
    else:
        with open(report_source, "r", encoding="utf-8") as f:
            report = json.load(f)

    manual_review = report.get("manual_review", [])
    if not manual_review:
        print("No manual review candidates found in report.")
        return tracks

    final_tracks = list(tracks)

    for item in manual_review:
        original = item["original"]
        candidate = item["candidate"]
        print("\nManual review candidate:")
        print(f"Original: {original.get('name')} (id={original.get('id')})")
        print(f"Original artists: {', '.join(original.get('artists', []))}")
        print(f"Candidate: {candidate.get('name')} (id={candidate.get('id')})")
        print(f"Candidate artists: {', '.join(candidate.get('artists', []))}")
        print(f"Score: {item.get('score'):.2f}")
        print(f"Reason: {item.get('reason')}")

        answer = input("Accept replacement? [y/N]: ").strip().lower()
        if answer in ("y", "yes"):
            final_tracks = [candidate if t.get("id") == original.get("id") else t for t in final_tracks]
            print("Accepted replacement.")
        else:
            final_tracks = [t for t in final_tracks if t.get("id") != original.get("id")]
            print("Removed original track.")

    if export_path:
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump({"items": final_tracks}, f, ensure_ascii=False, indent=2)

    return final_tracks


def remove_exact_duplicates(tracks):
    seen = set()
    result = []

    for track in tracks:
        if track["id"] not in seen:
            seen.add(track["id"])
            result.append(track)

    return result


def apply_health_audit(tracks=None, audit=None, audit_path=None, mode="remove"):
 
    if audit is None:
        if audit_path is None:
            raise ValueError("Provide either audit or audit_path")

        with open(audit_path, "r") as f:
            audit = json.load(f)

    if tracks is None:
        raise ValueError("tracks must be provided")

    dead_ids = {t["id"] for t in audit.get("dead", [])}
    unknown_ids = {t["id"] for t in audit.get("unknown", [])}

    cleaned = []

    for track in tracks:
        track_id = track["id"]

        if track_id in dead_ids:
            if mode == "remove":
                continue

            if mode == "mark":
                track = {**track, "health_status": "DEAD"}
                cleaned.append(track)
                continue

        if track_id in unknown_ids:
            track = {**track, "health_status": "UNKNOWN"}

        cleaned.append(track)

    return cleaned

def normalize_track(track):
    """
    Unifies all track formats into single schema:
    - id (always string)
    - name
    - artists
    """
    return {
        "id": track.get("id") or track.get("track_id"),
        "name": track.get("name"),
        "artists": track.get("artists", []),
        "isrc": track.get("isrc"),
        "raw": track
    }