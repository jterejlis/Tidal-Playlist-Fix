from core.core import load_tracks_from_file
from matching.replacement import find_replacement
from pipeline.playlist_worker import process_playlist
from reporting.duplicates_reporting import generate_decisions_report, run_playlist_analysis
from tidal.search import TidalSearchEngine
from tidal.client import TidalClient


def run():
    path = "playlist_8261bf14-e681-4d8d-8e72-33011a8d70f4.json"

    data = load_tracks_from_file(path)
    items = data["items"]

    client = TidalClient()
    client.login()

    search_engine = TidalSearchEngine(client)

    result = process_playlist(
        items,
        search_engine,
        audit_path="audit_report.json",
        export_path="cleaned.json"
    )

    print(f"Done. Final tracks: {len(result)}")


if __name__ == "__main__":
    run()
    # run_playlist_analysis("playlist_8261bf14-e681-4d8d-8e72-33011a8d70f4.json", print_report=True, export_json=True, path_to_export="final_report.json")
