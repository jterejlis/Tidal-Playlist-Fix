class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"


def header(title, icon=""):
    title_text = f"{icon} {title}".strip()
    border = "=" * len(title_text)
    return f"{Colors.BOLD}{Colors.BLUE}{border}\n{title_text}\n{border}{Colors.RESET}\n"


def format_playlists(playlists, title="Playlists"):
    formatted = header(title, "🎧")
    if not playlists:
        return formatted + f"{Colors.YELLOW}No playlists found.{Colors.RESET}\n"

    for i, p in enumerate(playlists, 1):
        formatted += (
            f"{Colors.CYAN}{i}.{Colors.RESET} {Colors.BOLD}\"{p.get('name', 'Unknown')}\"{Colors.RESET} - "
            f"{Colors.MAGENTA}{p.get('id', 'unknown')}{Colors.RESET}\n"
        )

    return formatted


def format_tracks(tracks, title="Tracks"):
    formatted = header(title, "🎵")
    if not tracks:
        return formatted + f"{Colors.YELLOW}No tracks found.{Colors.RESET}\n"

    for i, t in enumerate(tracks, 1):
        name = t.get("name", "Unknown")
        artists = ", ".join(t.get("artists", [])) or "Unknown artist"
        isrc = t.get("isrc")
        formatted += f"{Colors.CYAN}{i}.{Colors.RESET} {Colors.BOLD}\"{name}\"{Colors.RESET} by {Colors.GREEN}{artists}{Colors.RESET}\n"
        formatted += f"   {Colors.MAGENTA}ID:{Colors.RESET} {t.get('id', 'unknown')}"
        if isrc:
            formatted += f" {Colors.YELLOW}[ISRC: {isrc}]{Colors.RESET}"
        formatted += "\n"

    return formatted


def format_search_results(search_result, title="Search Results"):
    items = search_result.get("items") if isinstance(search_result, dict) else search_result
    return format_tracks(items, title=title)


def format_duplicate_report(report):
    formatted = header("Duplicate Track Report", "🧩")
    formatted += f"Generated: {report['generated_at']}\n"
    formatted += f"Total pairs analyzed: {report['total_pairs']}\n"
    formatted += f"Total duplicates found: {len(report['duplicates'])}\n\n"

    for i, d in enumerate(report["duplicates"], 1):
        score = d["score"]
        label = d["label"]
        a = d["track_a"]
        b = d["track_b"]
        formatted += (
            f"{Colors.YELLOW}{i}.{Colors.RESET} [{Colors.RED}{label}{Colors.RESET}] "
            f"Score: {Colors.BOLD}{score:.2f}{Colors.RESET}\n"
        )
        formatted += (
            f"   {Colors.GREEN}- Track A:{Colors.RESET} {Colors.BOLD}\"{a['name']}\"{Colors.RESET} by "
            f"{', '.join(a['artists'])} (ID: {a['id']})\n"
        )
        formatted += (
            f"   {Colors.GREEN}- Track B:{Colors.RESET} {Colors.BOLD}\"{b['name']}\"{Colors.RESET} by "
            f"{', '.join(b['artists'])} (ID: {b['id']})\n\n"
        )

    return formatted


def format_decision_report(report):
    formatted = header("Duplicate Decision Report", "📝")
    formatted += f"Generated: {report['generated_at']}\n"
    formatted += f"Total pairs analyzed: {report['total_pairs']}\n"
    formatted += f"Total duplicates found: {len(report['duplicates'])}\n\n"

    for i, d in enumerate(report["duplicates"], 1):
        score = d["score"]
        label = d["label"]
        decision = "KEEP" if label == "PERFECT_MATCH" else "REVIEW"
        a = d["track_a"]
        b = d["track_b"]
        decision_color = Colors.GREEN if decision == "KEEP" else Colors.YELLOW

        formatted += (
            f"{Colors.YELLOW}{i}.{Colors.RESET} [{Colors.CYAN}{label}{Colors.RESET}] "
            f"Score: {Colors.BOLD}{score:.2f}{Colors.RESET} - Decision: {decision_color}{decision}{Colors.RESET}\n"
        )
        formatted += (
            f"   {Colors.GREEN}- Track A:{Colors.RESET} {Colors.BOLD}\"{a['name']}\"{Colors.RESET} by "
            f"{', '.join(a['artists'])} (ID: {a['id']})\n"
        )
        formatted += (
            f"   {Colors.GREEN}- Track B:{Colors.RESET} {Colors.BOLD}\"{b['name']}\"{Colors.RESET} by "
            f"{', '.join(b['artists'])} (ID: {b['id']})\n\n"
        )

    return formatted


from duplicates.exact_duplicates import find_exact_duplicates


def format_health_audit_report(report):
    total = report.get("total", 0)
    ok = report.get("ok", [])
    dead = report.get("dead", [])
    exact_duplicates = report.get("exact_duplicates")

    if exact_duplicates is None:
        exact_duplicates = find_exact_duplicates(ok + dead)

    formatted = header("Playlist Health Audit", "❤️")
    formatted += f"Playlist ID: {Colors.BOLD}{report.get('playlist_id')}{Colors.RESET}\n"
    formatted += f"Total tracks: {Colors.BOLD}{total}{Colors.RESET}\n"
    formatted += f"{Colors.GREEN}OK tracks:{Colors.RESET} {len(ok)}\n"
    formatted += f"{Colors.RED}DEAD tracks:{Colors.RESET} {len(dead)}\n"

    if total:
        health = len(ok) / total * 100
        health_color = (
            Colors.GREEN if health > 80 else Colors.YELLOW if health > 50 else Colors.RED
        )
        formatted += f"Health: {health_color}{Colors.BOLD}{health:.2f}%{Colors.RESET}\n"

    formatted += f"\n{Colors.RED}EXACT DUPLICATES (same track repeated):{Colors.RESET}\n"
    if not exact_duplicates:
        formatted += f"  {Colors.GREEN}None{Colors.RESET}\n"
    for i, dup in enumerate(exact_duplicates, 1):
        track = dup.get("track", {})
        track_name = track.get("name", "Unknown")
        artists = ", ".join(track.get("artists", [])) or "Unknown artist"
        formatted += (
            f"  {Colors.YELLOW}{i}.{Colors.RESET} {Colors.BOLD}\"{track_name}\"{Colors.RESET} by {Colors.GREEN}{artists}{Colors.RESET}\n"
        )
        formatted += f"    {Colors.MAGENTA}ID:{Colors.RESET} {dup['track_id']} | count={dup['count']} | positions={dup['positions']}\n"

    formatted += f"\n{Colors.RED}DEAD TRACKS:{Colors.RESET}\n"
    if not dead:
        formatted += f"  {Colors.GREEN}None{Colors.RESET}\n"
    for i, t in enumerate(dead, 1):
        formatted += f"  {Colors.RED}{i}.{Colors.RESET} {Colors.BOLD}\"{t['name']}\"{Colors.RESET} (ID: {t['id']})\n"

    formatted += f"\n{Colors.GREEN}OK TRACKS (sample):{Colors.RESET}\n"
    if not ok:
        formatted += f"  {Colors.YELLOW}None{Colors.RESET}\n"
    for i, t in enumerate(ok[:15], 1):
        formatted += f"  {Colors.CYAN}{i}.{Colors.RESET} {Colors.BOLD}\"{t['name']}\"{Colors.RESET} (ID: {t['id']})\n"

    return formatted


def format_replacement_report(report):
    formatted = header("Replacement Suggestions Report", "🔁")
    formatted += f"Generated: {report['generated_at']}\n"
    formatted += f"Dead tracks: {report['total_dead']}\n\n"

    if not report.get("items"):
        return formatted + f"{Colors.YELLOW}No replacement suggestions available.{Colors.RESET}\n"

    for i, item in enumerate(report["items"], 1):
        orig = item["original"]
        replacement = item.get("replacement")
        score = item.get("score", 0.0)
        action = item.get("action", "KEEP")
        reason = item.get("reason", "")

        formatted += (
            f"{Colors.YELLOW}{i}.{Colors.RESET} {Colors.BOLD}\"{orig.get('name', 'Unknown')}\"{Colors.RESET} "
            f"by {Colors.GREEN}{', '.join(orig.get('artists', [])) or 'Unknown artist'}{Colors.RESET}\n"
        )
        formatted += f"   {Colors.MAGENTA}ID:{Colors.RESET} {orig.get('id', 'unknown')}\n"

        if replacement:
            formatted += (
                f"   {Colors.CYAN}Suggested replacement:{Colors.RESET} {Colors.BOLD}\"{replacement.get('name', 'Unknown')}\"{Colors.RESET} "
                f"by {Colors.GREEN}{', '.join(replacement.get('artists', [])) or 'Unknown artist'}{Colors.RESET}\n"
            )
            formatted += f"   {Colors.MAGENTA}Replacement ID:{Colors.RESET} {replacement.get('id', 'unknown')}\n"
            if replacement.get('isrc'):
                formatted += f"   {Colors.YELLOW}[ISRC: {replacement.get('isrc')}]{Colors.RESET}\n"
        else:
            formatted += f"   {Colors.RED}No replacement candidate found{Colors.RESET}\n"

        color = Colors.GREEN if action == "REPLACE" else Colors.YELLOW if action == "ASK" else Colors.RED
        formatted += f"   Action: {color}{action}{Colors.RESET}"
        if reason:
            formatted += f" ({reason})"
        formatted += f" | Score: {Colors.BOLD}{score:.2f}{Colors.RESET}\n\n"

    return formatted
