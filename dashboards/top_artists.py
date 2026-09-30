from collections import Counter
from core.core import load_tracks_from_file

class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    MAGENTA = "\033[95m"


def count_top_artists(path: str):
    data = load_tracks_from_file(path)
    tracks = data["items"]
    artists = []
    for t in tracks:
        artists.extend(t.get("artists", []))
    return Counter(artists), tracks

def print_dashboard(path: str, top_n: int = 10):
    counter, tracks = count_top_artists(path)

    total_tracks = len(tracks)
    total_artists = sum(counter.values())
    unique_artists = len(counter)
    avg_artists_per_track = total_artists / total_tracks if total_tracks else 0

    print("=" * 50)
    print("🎧 PLAYLIST DASHBOARD")
    print("=" * 50)
    print(f"📀 Tracks:            {total_tracks}")
    print(f"👤 Unique artists:    {unique_artists}")
    print(f"🎤 Total artist refs: {total_artists}")
    print(f"📊 Avg artists/track: {avg_artists_per_track:.2f}")
    print(f"\n{Colors.YELLOW}🔥 TOP ARTISTS:{Colors.RESET}")
    print(f"{Colors.CYAN}{'-' * 50}{Colors.RESET}")

    top = counter.most_common(top_n)
    max_count = top[0][1] if top else 1

    for i, (artist, count) in enumerate(top, 1):
        bar_len = int((count / max_count) * 30)
        bar = "█" * bar_len
        print(
            f"{Colors.GREEN}{i}.{Colors.RESET} {Colors.BOLD}{artist:<25}{Colors.RESET} "
            f"{Colors.MAGENTA}{count:>4}{Colors.RESET} | {bar}"
        )

    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 50}{Colors.RESET}")


if __name__ == "__main__":
    print_dashboard("playlist_8261bf14-e681-4d8d-8e72-33011a8d70f4.json")
