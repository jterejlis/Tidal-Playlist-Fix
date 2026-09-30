import argparse
import json
import os
from datetime import datetime

from core.core import load_tracks_from_file as load_tracks
from dashboards.top_artists import count_top_artists, print_dashboard
from duplicates.find_duplicates import find_duplicates
from duplicates.exact_duplicates import find_exact_duplicates
from duplicates.cleaning_decision import build_decisions, apply_decisions
from reporting.health_audit_reporting import save_playlist_audit, load_playlist_audit, show_report as show_health_report
from reporting.formatters import (
    format_duplicate_report,
    format_decision_report,
    format_health_audit_report,
    format_playlists,
    format_tracks,
    format_search_results,
    format_replacement_report,
)
from reporting.duplicates_reporting import (
    debug_generate_duplicate_report,
    debug_print_duplicates_report,
    debug_export_duplicates_report_json,
    generate_decisions_report,
    export_decisions_report_json,
    run_playlist_analysis,
)
from matching.replacement import build_replacement_report
from pipeline.playlist_worker import apply_replacements, manual_accept_replacements, remove_exact_duplicates
from tidal.client import TidalClient
from tidal.playlist import PlaylistService as TidalPlaylistService
from tidal.search import TidalSearchEngine

_tidal_client = None
_tidal_service = None

def get_tidal_client():
    global _tidal_client, _tidal_service
    if _tidal_client and _tidal_client.is_logged_in():
        return _tidal_client

    _tidal_client = TidalClient()
    _tidal_client.login()
    _tidal_service = TidalPlaylistService(_tidal_client)
    return _tidal_client


def get_tidal_service():
    global _tidal_service
    if _tidal_service and _tidal_service.client.is_logged_in():
        return _tidal_service

    client = get_tidal_client()
    _tidal_service = TidalPlaylistService(client)
    return _tidal_service


def ensure_file(path):
    if not os.path.isfile(path):
        raise FileNotFoundError(f"File not found: {path}")
    return path


def load_and_print_tracks(path):
    path = ensure_file(path)
    data = load_tracks(path)
    if isinstance(data, dict) and "items" in data:
        print(format_tracks(data["items"], title=f"Loaded tracks from {os.path.basename(path)}"))
    else:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    return data


def calculate_top_artists(path, limit=20):
    path = ensure_file(path)
    print_dashboard(path, top_n=limit)
    counter, _ = count_top_artists(path)
    top_artists = [
        {"artist": artist, "count": count}
        for artist, count in counter.most_common(limit)
    ]
    return top_artists


def find_duplicates_command(path):
    path = ensure_file(path)
    tracks = load_tracks(path)["items"]
    exact_duplicates = find_exact_duplicates(tracks)
    duplicates = find_duplicates(tracks)
    report = debug_generate_duplicate_report(duplicates, exact_duplicates=exact_duplicates)
    debug_print_duplicates_report(report)
    return duplicates


def find_exact_duplicates_command(path):
    path = ensure_file(path)
    tracks = load_tracks(path)["items"]
    exact = find_exact_duplicates(tracks)
    if not exact:
        print("No exact duplicates found.")
        return exact
    print("\nExact duplicates:\n")
    for i, item in enumerate(exact, 1):
        track = item.get("track", {})
        name = track.get("name", "Unknown")
        artists = ", ".join(track.get("artists", [])) or "Unknown artist"
        print(f"{i}. \"{name}\" by {artists} - ID: {item['track_id']} (count={item['count']}, positions={item['positions']})")
    return exact


def build_decisions_command(path):
    path = ensure_file(path)
    tracks = load_tracks(path)["items"]
    duplicates = find_duplicates(tracks)
    decisions = build_decisions(duplicates)
    exact_duplicates = find_exact_duplicates(tracks)
    generate_decisions_report(decisions, exact_duplicates)
    return decisions


def audit_health_command(path=None, playlist_id=None, export_json=False, output="playlist_audit.json"):
    if not path and not playlist_id:
        raise ValueError("Provide either --path or --playlist-id for health audit")

    service = get_tidal_service()

    if path:
        path = ensure_file(path)
        tracks = load_tracks(path)["items"]
        if playlist_id is None:
            playlist_id = os.path.splitext(os.path.basename(path))[0]

        report = {
            "playlist_id": playlist_id,
            "total": len(tracks),
            "ok": [],
            "dead": [],
            "exact_duplicates": find_exact_duplicates(tracks),
        }

        for track in tracks:
            if service.track_exists(track.get("id")):
                report["ok"].append(track)
            else:
                report["dead"].append(track)
    else:
        report = service.playlist_audit(playlist_id)

    show_health_report(report=report)
    if export_json:
        save_playlist_audit(report, filename=output)
        print(f"Saved audit to {output}")
    return report


def generate_replacement_report(health_report_path, output_path=None):
    report = load_playlist_audit(health_report_path)
    dead_tracks = report.get("dead", [])

    engine = TidalSearchEngine(get_tidal_client())

    replacement_report = build_replacement_report(engine, dead_tracks)
    print(format_replacement_report(replacement_report))

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(replacement_report, f, ensure_ascii=False, indent=2)
        print(f"Saved replacement report to {output_path}")

    return replacement_report


def tidal_login():
    return get_tidal_client()


def tidal_search(query, limit=10):
    engine = TidalSearchEngine(get_tidal_client())
    results = engine.search(query, limit=limit)
    print(format_search_results(results, title=f"Tidal Search: {query}"))
    return results


def tidal_user_playlists():
    service = get_tidal_service()
    playlists = service.get_user_playlists()
    print(format_playlists(playlists, title="Tidal Playlists"))
    return playlists


def tidal_playlist_tracks(playlist_id, export=False, output=None):
    service = get_tidal_service()
    tracks = service.get_playlist_tracks(playlist_id)
    print(format_tracks(tracks, title=f"Tidal Playlist Tracks ({playlist_id})"))

    if export or output:
        filename = output or f"tidal_playlist_{playlist_id}.json"
        service.save_playlist_tracks(playlist_id, filename=filename)
        print(f"Saved Tidal playlist tracks to {filename}")

    return tracks


def open_saved_duplicate_report(path):
    path = ensure_file(path)
    with open(path, "r", encoding="utf-8") as f:
        report = json.load(f)
    print(format_duplicate_report(report))
    return report


def open_saved_health_report(path):
    path = ensure_file(path)
    show_health_report(file=path)
    return path


def interactive_menu():
    while True:
        print("\nTidal Playlist Fix")
        print("  1) List playlists")
        print("  2) Show playlist tracks")
        print("  3) Run health analysis")
        print("  4) Open saved health report")
        print("  5) Run duplicate analysis")
        print("  6) Open saved duplicate report")
        print("  7) Top artists from saved playlist")
        print("  8) Build replacement report from health audit")
        print("  9) Run full fix workflow")
        print(" 10) Search Tidal tracks")
        print("  q) Quit")

        choice = input("action> ").strip().lower()

        if choice in {"q", "quit", "exit"}:
            print("Exiting interactive mode.")
            return

        try:
            if choice == "1":
                tidal_user_playlists()
            elif choice == "2":
                playlist_id = input("Tidal playlist ID: ").strip()
                export = input("Export playlist tracks? (y/N): ").strip().lower() == "y"
                output = input("Output filename [tidal_playlist_<id>.json]: ").strip() or None
                tidal_playlist_tracks(playlist_id, export=export, output=output)
            elif choice == "3":
                path_or_id = input("Saved playlist JSON path or Tidal playlist ID: ").strip()
                if path_or_id.endswith(".json") and os.path.isfile(path_or_id):
                    audit_health_command(
                        path=path_or_id,
                        export_json=input("Export audit JSON? (y/N): ").strip().lower() == "y",
                        output=input("Output file [playlist_audit.json]: ").strip() or "playlist_audit.json",
                    )
                else:
                    audit_health_command(
                        playlist_id=path_or_id,
                        export_json=input("Export audit JSON? (y/N): ").strip().lower() == "y",
                        output=input("Output file [playlist_audit.json]: ").strip() or "playlist_audit.json",
                    )
            elif choice == "4":
                report_path = input("Saved health report JSON path: ").strip()
                open_saved_health_report(report_path)
            elif choice == "5":
                path = input("Saved playlist JSON path for duplicate analysis: ").strip()
                find_duplicates_command(path)
            elif choice == "6":
                report_path = input("Saved duplicate report JSON path: ").strip()
                open_saved_duplicate_report(report_path)
            elif choice == "7":
                path = input("Saved playlist JSON path: ").strip()
                calculate_top_artists(path)
            elif choice == "8":
                health_report = input("Health report JSON path: ").strip()
                output = input("Output file [replacement_report.json] (optional): ").strip() or None
                generate_replacement_report(health_report, output_path=output)
            elif choice == "9":
                path_or_id = input("Playlist file path or Tidal playlist ID: ").strip()
                if path_or_id.endswith(".json") and os.path.isfile(path_or_id):
                    tracks = load_tracks(path_or_id)["items"]
                    audit = {"playlist_id": os.path.splitext(os.path.basename(path_or_id))[0], "dead": [t for t in tracks if not get_tidal_service().track_exists(t.get("id"))], "unknown": []}
                else:
                    service = get_tidal_service()
                    tracks = service.get_playlist_tracks(path_or_id)
                    audit = service.playlist_audit(path_or_id)

                engine = TidalSearchEngine(get_tidal_client())
                result_tracks, report = apply_replacements(tracks, engine, audit=audit, missing_replacements_path="missing_replacements.json")

                if report.get("manual_review"):
                    should_accept = input("Accept edge-case replacements manually? [y/N]: ").strip().lower()
                    if should_accept in {"y", "yes"}:
                        result_tracks = manual_accept_replacements(result_tracks, report, export_path=None)

                exact_duplicates = find_exact_duplicates(result_tracks)
                if exact_duplicates:
                    result_tracks = remove_exact_duplicates(result_tracks)
                duplicates = find_duplicates(result_tracks)
                if duplicates:
                    decisions = build_decisions(duplicates)
                    result_tracks = apply_decisions(result_tracks, decisions)

                output_path = input("Output cleaned playlist JSON path [cleaned.json]: ").strip() or "cleaned.json"
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump({"items": result_tracks}, f, ensure_ascii=False, indent=2)
                print(f"Saved cleaned playlist to {output_path}")

                publish = input("Publish cleaned playlist to Tidal? [y/N]: ").strip().lower()
                if publish in {"y", "yes"}:
                    name = input("Playlist name [Auto cleaned playlist]: ").strip() or "Auto cleaned playlist"
                    description = input("Description [Created by Tidal-Playlist-Fix]: ").strip() or "Created by Tidal-Playlist-Fix"
                    created = get_tidal_service().create_playlist(
                        track_ids=[t.get("id") for t in result_tracks if t.get("id")],
                        name=name,
                        description=description,
                    )
                    print(f"Published playlist: {created.get('name')} (id={created.get('id')})")

                print(f"Fix workflow finished. Replaced: {report.get('replaced', 0)}, Not restored: {report.get('not_restored', 0)}")
            elif choice == "10":
                query = input("Search query: ").strip()
                limit = input("Limit (default 10): ").strip() or "10"
                tidal_search(query, limit=int(limit))
            else:
                print("Unknown action. Choose a listed number.")
        except Exception as exc:
            print(f"Error: {exc}")
            continue


def main():
    parser = argparse.ArgumentParser(description="Tidal playlist audit, replacement and reporting CLI")
    subparsers = parser.add_subparsers(dest="command")

    parser_load = subparsers.add_parser("load-tracks", help="Load and print JSON track file")
    parser_load.add_argument("path", help="Path to playlist JSON")

    parser_top = subparsers.add_parser("top-artists", help="Print top artists from a playlist file")
    parser_top.add_argument("path", help="Path to playlist JSON")
    parser_top.add_argument("--limit", type=int, default=20)

    parser_dup = subparsers.add_parser("find-duplicates", help="Run duplicate finder")
    parser_dup.add_argument("path", help="Path to playlist JSON")

    parser_exact = subparsers.add_parser("find-exact-duplicates", help="Run exact duplicates finder")
    parser_exact.add_argument("path", help="Path to playlist JSON")

    parser_decision = subparsers.add_parser("build-decisions", help="Build decision groups from duplicates")
    parser_decision.add_argument("path", help="Path to playlist JSON")

    parser_audit = subparsers.add_parser("health-audit", help="Run playlist health audit")
    parser_audit.add_argument("--path", help="Path to saved playlist tracks JSON")
    parser_audit.add_argument("--playlist-id", help="Tidal playlist ID for live audit")
    parser_audit.add_argument("--export-json", action="store_true")
    parser_audit.add_argument("--output", default="playlist_audit.json")

    parser_replace = subparsers.add_parser("replacement-report", help="Build replacement report for dead tracks")
    parser_replace.add_argument("--health-report", required=True, help="Path to saved health audit JSON report")
    parser_replace.add_argument("--output", default=None, help="Optional output filename for replacement report JSON")

    subparsers.add_parser("shell", help="Start the interactive terminal shell")


    subparsers.add_parser("tidal-playlists", help="List Tidal playlists")
    parser_tidal_playlist = subparsers.add_parser("tidal-playlist-tracks", help="Get Tidal playlist tracks")
    parser_tidal_playlist.add_argument("playlist_id", help="Tidal playlist ID")
    parser_tidal_playlist.add_argument("--export", action="store_true", help="Export playlist tracks to JSON")
    parser_tidal_playlist.add_argument("--output", default=None, help="Output filename for exported Tidal tracks")
    parser_tidal_search = subparsers.add_parser("tidal-search", help="Search Tidal tracks")
    parser_tidal_search.add_argument("query", help="Search query")
    parser_tidal_search.add_argument("--limit", type=int, default=10)

    # Convenience / new commands
    subparsers.add_parser("tidal-login", help="Login to Tidal (persistent via tidalapi)")

    parser_audit_short = subparsers.add_parser("audit", help="Run playlist health audit (alias)")
    parser_audit_short.add_argument("--path", help="Path to saved playlist tracks JSON")
    parser_audit_short.add_argument("--playlist-id", help="Tidal playlist ID for live audit")
    parser_audit_short.add_argument("--export-json", action="store_true")
    parser_audit_short.add_argument("--output", default="playlist_audit.json")

    parser_fix = subparsers.add_parser("fix", help="Run replacement workflow for a playlist or saved JSON")
    parser_fix.add_argument("--path", help="Path to saved playlist tracks JSON (optional)")
    parser_fix.add_argument("--playlist-id", help="Tidal playlist ID (optional)")
    parser_fix.add_argument("--auto-approve", action="store_true", help="Automatically accept borderline replacements (ASK)")
    parser_fix.add_argument("--manual-accept", action="store_true", help="Manually accept ASK candidates during fix")
    parser_fix.add_argument("--create-playlist", action="store_true", help="Create a playlist with fixed tracks")
    parser_fix.add_argument("--name", default=None, help="Name for created playlist (optional)")
    parser_fix.add_argument("--description", default=None, help="Description for created playlist (optional)")
    parser_fix.add_argument("--missing-report", default=None, help="Path to save missing replacements report JSON")

    parser_add = subparsers.add_parser("add", help="Create playlist from saved JSON file")
    parser_add.add_argument("json_path", help="Saved playlist JSON path (must contain items with 'id')")
    parser_add.add_argument("name", nargs="?", default=None, help="Playlist name (optional)")
    parser_add.add_argument("description", nargs="?", default=None, help="Playlist description (optional)")

    parser_show_report = subparsers.add_parser("show-report", help="Show a saved replacement report")
    parser_show_report.add_argument("report_path", help="Path to replacement report JSON")

    args = parser.parse_args()

    if args.command == "load-tracks":
        load_and_print_tracks(args.path)
    elif args.command == "top-artists":
        calculate_top_artists(args.path, limit=args.limit)
    elif args.command == "find-duplicates":
        find_duplicates_command(args.path)
    elif args.command == "find-exact-duplicates":
        find_exact_duplicates_command(args.path)
    elif args.command == "build-decisions":
        build_decisions_command(args.path)
    elif args.command == "health-audit":
        if not args.path and not args.playlist_id:
            parser.error("health-audit requires --path or --playlist-id")
        audit_health_command(args.path, playlist_id=args.playlist_id, export_json=args.export_json, output=args.output)
    elif args.command == "replacement-report":
        generate_replacement_report(args.health_report, output_path=args.output)
    elif args.command == "tidal-playlists":
        tidal_user_playlists()
    elif args.command == "tidal-login":
        tidal_login()
    elif args.command == "audit":
        if not args.path and not args.playlist_id:
            parser.error("audit requires --path or --playlist-id")
        audit_health_command(args.path, playlist_id=args.playlist_id, export_json=args.export_json, output=args.output)
    elif args.command == "fix":
        if not args.path and not args.playlist_id:
            parser.error("fix requires --path or --playlist-id")

        # Load tracks + audit
        service = get_tidal_service()
        if args.path:
            path = ensure_file(args.path)
            tracks = load_tracks(path)["items"]
            audit = None
            # build audit from saved tracks
            dead = [t for t in tracks if not service.track_exists(t.get("id"))]
            audit = {"playlist_id": os.path.splitext(os.path.basename(path))[0], "dead": dead, "unknown": []}
        else:
            tracks = service.get_playlist_tracks(args.playlist_id)
            audit = service.playlist_audit(args.playlist_id)

        # use Tidal as the search provider
        engine = TidalSearchEngine(get_tidal_client())

        result_tracks, report = apply_replacements(tracks, engine, audit=audit, missing_replacements_path=args.missing_report)

        # auto-approve ASK candidates if requested
        auto_approved = 0
        if args.auto_approve and report.get("manual_review"):
            for item in report.get("manual_review", []):
                cand = item.get("candidate")
                if not cand:
                    continue
                # replace original in result_tracks
                for i, r in enumerate(result_tracks):
                    if r.get("id") == item.get("id"):
                        result_tracks[i] = cand
                        auto_approved += 1
                        break
            report["auto_approved"] = auto_approved

        if args.manual_accept and report.get("manual_review"):
            print("Starting manual acceptance for ASK candidates...")
            result_tracks = manual_accept_replacements(result_tracks, report)
            print("Manual acceptance complete.")

        # Remove exact duplicates
        exact_duplicates = find_exact_duplicates(result_tracks)
        if exact_duplicates:
            removed_exact = sum(d["count"] - 1 for d in exact_duplicates)
            print(f"Removing {removed_exact} exact duplicate track(s).")
            result_tracks = remove_exact_duplicates(result_tracks)

        # Find and remove fuzzy duplicates
        duplicates = find_duplicates(result_tracks)
        if duplicates:
            print(f"Found {len(duplicates)} potential duplicate groups. Building decisions...")
            decisions = build_decisions(duplicates)
            result_tracks = apply_decisions(result_tracks, decisions)
            print(f"Removed {len(decisions)} duplicate(s) based on decisions.")

        print("Fix workflow finished.")
        print(f"Replaced: {report.get('replaced',0)}, Auto-approved: {report.get('auto_approved',0) if report.get('auto_approved') else 0}, Not restored: {report.get('not_restored',0)}")

        if args.create_playlist:
            # create playlist on selected provider
            track_ids = [t.get("id") for t in result_tracks if t.get("id")]
            tservice = get_tidal_service()
            created = tservice.create_playlist(track_ids=track_ids, name=args.name, description=args.description)
            print(f"Created playlist: {created.get('name')} (id={created.get('id')})")

    elif args.command == "add":
        path = ensure_file(args.json_path)
        data = load_tracks(path)
        items = data.get("items") if isinstance(data, dict) else None
        if not items:
            print("No items found in JSON file")
        else:
            track_ids = [t.get("id") for t in items if t.get("id")]
            tservice = get_tidal_service()
            created = tservice.create_playlist(track_ids=track_ids, name=args.name, description=args.description)
            print(f"Created playlist: {created.get('name')} (id={created.get('id')})")

    elif args.command == "show-report":
        report_path = ensure_file(args.report_path)
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
        print(format_replacement_report(report))
    elif args.command == "tidal-playlist-tracks":
        tidal_playlist_tracks(args.playlist_id, export=args.export, output=args.output)
    elif args.command == "tidal-search":
        tidal_search(args.query, limit=args.limit)
    elif args.command == "shell" or args.command is None:
        interactive_menu()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

