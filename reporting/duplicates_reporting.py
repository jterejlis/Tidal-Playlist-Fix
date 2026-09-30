from duplicates.find_duplicates import find_duplicates
from duplicates.cleaning_decision import build_decisions
from duplicates.exact_duplicates import find_exact_duplicates
from core.core import load_tracks_from_file
from datetime import datetime
from collections import Counter
from colorama import init, Fore, Style
from reporting.formatters import format_duplicate_report, format_replacement_report
import json


class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"

    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    GRAY = "\033[90m"



def debug_generate_duplicate_report(duplicates_data, exact_duplicates=None):
    duplicates = duplicates_data
    report = {
        "total_pairs": len(duplicates),
        "generated_at": datetime.now().isoformat(),
        "duplicates": []
    }

    if exact_duplicates is not None:
        report["exact_duplicates"] = exact_duplicates

    for d in duplicates:
        t1 = d["track1"]
        t2 = d["track2"]

        report["duplicates"].append({
            "score": d["score"],
            "label": (
                "PERFECT_MATCH" if d["score"] == 1.0
                else "HIGH_SIMILARITY" if d["score"] >= 0.85
                else "FUZZY_MATCH"
            ),
            "track_a": {
                "id": t1.get("id"),
                "name": t1.get("name"),
                "artists": t1.get("artists", [])
            },
            "track_b": {
                "id": t2.get("id"),
                "name": t2.get("name"),
                "artists": t2.get("artists", [])
            }
        })

    return report


def debug_print_exact_duplicates(exact_duplicates):
    print("\n" + "=" * 80)
    print(Fore.CYAN + Style.BRIGHT + "🔴 EXACT DUPLICATES (same track repeated)")
    print("-" * 80)

    if not exact_duplicates:
        print(Fore.GREEN + "✔ No exact duplicates found")
        return

    for d in exact_duplicates:
        track = d.get("track", {})
        name = track.get("name", "Unknown")
        artists = ", ".join(track.get("artists", [])) or "Unknown artist"

        print(Fore.RED + f"\n🎵 {name}")
        print(Fore.CYAN + f"🎤 {artists}")
        print(f"📌 ID: {d['track_id']}")
        print(f"🔁 Occurrences: {d['count']}")
        print(f"📍 Positions: {d['positions']}")


def debug_print_duplicates_report(report):
    exact_duplicates = report.get("exact_duplicates")
    if exact_duplicates is not None:
        debug_print_exact_duplicates(exact_duplicates)

    formatted_report = format_duplicate_report(report)
    print(formatted_report)
    return formatted_report


def debug_export_duplicates_report_json(duplicates, output_path="duplicates_report.json"):
    report = debug_generate_duplicate_report(duplicates)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    return output_path


def generate_decisions_report(decisions, exact_duplicates):
    print("\n" + "=" * 80)
    print(Fore.CYAN + Style.BRIGHT + "🎧 PLAYLIST HEALTH REPORT (FULL SYSTEM)")
    print("=" * 80)

    print("\n" + Fore.RED + Style.BRIGHT + "🔴 EXACT DUPLICATES (same track repeated)")
    print("-" * 80)

    if not exact_duplicates:
        print(Fore.GREEN + "✔ No exact duplicates found")
    else:
        for d in exact_duplicates:
            track_id = d["track_id"]
            count = d["count"]
            positions = d["positions"]

            track = d.get("track")

            if track:
                name = track.get("name", "Unknown")
                artists = ", ".join(track.get("artists", []))
            else:
                name = "Unknown"
                artists = "Unknown"

            print(Fore.RED + f"\n🎵 {name}")
            print(Fore.CYAN + f"🎤 {artists}")
            print(f"📌 ID: {track_id}")
            print(f"🔁 Occurrences: {count}")
            print(f"📍 Positions: {positions}")

    print("\n" + Fore.YELLOW + Style.BRIGHT + "📊 DECISIONS SUMMARY")
    print("-" * 80)

    actions = Counter(d["action"] for d in decisions)
    print(f"Groups: {len(decisions)}")
    print(Fore.RED + f"MERGE:  {actions.get('MERGE', 0)}")
    print(Fore.MAGENTA + f"REVIEW: {actions.get('REVIEW', 0)}")
    print(Fore.GREEN + f"KEEP:   {actions.get('KEEP', 0)}")

    print("\n" + Fore.YELLOW + Style.BRIGHT + "🧠 DECISION DETAILS")
    print("-" * 80)

    for i, d in enumerate(decisions, 1):
        action = d["action"]
        confidence = d["confidence"]

        if action == "MERGE":
            color = Fore.RED
        elif action == "REVIEW":
            color = Fore.MAGENTA
        else:
            color = Fore.GREEN

        print(
            f"\n[{i}] {color}{Style.BRIGHT}{action}"
            f"{Style.RESET_ALL} | confidence: {confidence:.2f}"
        )
        print(Fore.YELLOW + f"Reason: {d['reason']}")
        for t in d["group"]:
            artists = ", ".join(t.get("artists", []))
            print(f" • {t.get('name')} — {artists} (id={t.get('id')})")

    print("\n" + "=" * 80)


def export_decisions_report_json(decisions, exact_duplicates, output_path="playlist_report.json"):
    report = {
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_decision_groups": len(decisions),
            "merge": sum(d["action"] == "MERGE" for d in decisions),
            "review": sum(d["action"] == "REVIEW" for d in decisions),
            "keep": sum(d["action"] == "KEEP" for d in decisions),
            "exact_duplicates_groups": len(exact_duplicates),
            "exact_duplicates_tracks": sum(d["count"] for d in exact_duplicates),
        },
        "exact_duplicates": [
            {
                "track_id": d["track_id"],
                "count": d["count"],
                "positions": d["positions"],
                "track": {
                    "name": d["track"].get("name"),
                    "artists": d["track"].get("artists"),
                    "id": d["track"].get("id"),
                } if d.get("track") else None
            }
            for d in exact_duplicates
        ],
        "decisions": decisions
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Exported full report → {output_path}")


def run_playlist_analysis(file_path: str, print_report=False, export_json=False, path_to_export="duplicates_report.json"):
    data = load_tracks_from_file(file_path)
    tracks = data["items"]
    exact_duplicates = find_exact_duplicates(tracks)
    duplicates = find_duplicates(tracks)

    report = build_decisions(duplicates)

    if print_report:
        generate_decisions_report(report, exact_duplicates)
    if export_json:
        export_decisions_report_json(report, exact_duplicates, output_path=path_to_export)

    return report


def print_replacement_report(report):
    formatted = format_replacement_report(report)
    print(formatted)
    return formatted


def open_saved_replacement_report(path):
    with open(path, "r", encoding="utf-8") as f:
        report = json.load(f)
    return print_replacement_report(report)



