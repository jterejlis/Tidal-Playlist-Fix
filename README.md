# Tidal Playlist Fix

Tidal Playlist Fix is a Tidal-first playlist maintenance tool for auditing, repairing, deduplicating, and optionally publishing music playlists.

The project follows this real-world workflow:

1. load a playlist from Tidal or from a saved JSON export,
2. run a health audit and detect dead / missing tracks,
3. search Tidal for replacement candidates,
4. review edge-case replacements manually when needed,
5. remove exact and fuzzy duplicates,
6. export cleaned playlist data or create a new Tidal playlist.

Spotify support was intentionally removed from the active flow. This project is focused on Tidal only.

## AI Transparency & Project Background

In accordance with transparent and ethical AI development practices:

- **AI-Assisted Implementation:** Code generation and low-level script writing were largely executed with the assistance of AI models.
- **Architectural & Design Ownership:** The end-to-end software architecture, modular pipeline structure, system design decisions, edge-case criteria, and CLI/workflow ergonomics were fully designed and directed by the human author.
- **Learning Objective:** This repository serves as a hands-on project to explore and practice software architecture patterns, modular pipeline design, clean project structures, and pragmatic software project management.

## Security & Authentication

- **Native OAuth 2.0 Flow:** User credentials (passwords) are never collected, logged, or handled by this tool.
- **Local & Scoped:** The app connects directly through Tidal's official OAuth flow (via `tidalapi`). On first run requiring Tidal access, the CLI prompts an authorization URL to approve in your browser. Tokens are saved locally to your environment.
- **Private Playlist Support:** Because the tool operates under your authenticated user session, it has full access to both your public and private playlists.

## Quick Start

### Prerequisites

- Python 3.10+
- Tidal account with an active subscription
- Dependencies installed via `requirements.txt`

### Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If setting up minimally:

```bash
pip install tidalapi
```

### Try it out

```bash
python main.py --help
python main.py shell
```

## Project Structure

- `main.py` — primary CLI entry point
- `ui/tui.py` — terminal report viewer / inspector interface
- `pipeline/playlist_worker.py` — end-to-end fix workflow orchestrator
- `matching/replacement.py` — replacement search and evaluation logic
- `duplicates/` — exact and fuzzy duplicate detection
- `reporting/` — formatted console and JSON reporting utilities
- `tidal/` — Tidal client, OAuth handling, search, and playlist operations
- `core/` — shared track normalization and data loaders

## CLI Usage

### General Help

```bash
python main.py --help
```

### Inspect a Saved Playlist JSON

```bash
python main.py load-tracks my_playlist.json
python main.py top-artists my_playlist.json --limit 20
```

### Health Audit

Run an audit on a local JSON export:

```bash
python main.py health-audit --path my_playlist.json --export-json --output playlist_audit.json
```

Run an audit directly on an active Tidal playlist (public or private):

```bash
python main.py health-audit --playlist-id <TIDAL_PLAYLIST_ID> --export-json --output playlist_audit.json
```

### Build Replacement Report

Generate replacement candidates for dead tracks based on an audit report:

```bash
python main.py replacement-report --health-report playlist_audit.json --output replacement_report.json
```

### Run the Fix Workflow

Run on a saved JSON file and export missing replacements:

```bash
python main.py fix --path my_playlist.json --missing-report missing_replacements.json
```

Run directly on a live Tidal playlist:

```bash
python main.py fix --playlist-id <TIDAL_PLAYLIST_ID> --missing-report missing_replacements.json
```

Automatically approve borderline replacements:

```bash
python main.py fix --path my_playlist.json --auto-approve
```

Interactively prompt and approve ambiguous replacements during execution:

```bash
python main.py fix --path my_playlist.json --manual-accept
```

Repair and publish directly as a new playlist on Tidal:

```bash
python main.py fix --path my_playlist.json --manual-accept --create-playlist --name "Cleaned Playlist" --description "Fixed with Tidal Playlist Fix"
```

### Tidal Operations

Search catalog tracks:

```bash
python main.py tidal-search "artist name" --limit 10
```

List your account's playlists (including private ones):

```bash
python main.py tidal-playlists
```

Export tracks from a specific playlist:

```bash
python main.py tidal-playlist-tracks <TIDAL_PLAYLIST_ID> --export
```

### Interactive Shell & TUI Inspector

Launch the interactive menu-driven shell:

```bash
python main.py shell
```

View and inspect a generated report inside the terminal UI:

```bash
python main.py show-report replacement_report.json
```

## Typical End-to-End Workflow

```bash
# 1. Audit playlist health
python main.py health-audit --path playlist.json --export-json --output audit.json

# 2. Build replacement recommendations for missing items
python main.py replacement-report --health-report audit.json --output replacements.json

# 3. Fix duplicates, review edge cases interactively, and publish clean version
python main.py fix --path playlist.json --manual-accept --create-playlist --name "Cleaned Playlist" --description "Fixed with Tidal Playlist Fix"
```

## Report Types

The tool reads and writes several modular JSON report formats to ensure full transparency before making remote changes:

- **Health audit report:** dead tracks, region locks, or unavailable items.
- **Replacement report:** candidate suggestions with match confidence.
- **Duplicate report:** detected exact matches and fuzzy title/version overlaps.
- **Decision report:** track-by-track resolution history.
- **Missing replacements report:** items requiring manual catalog lookup.

## Notes

- The active service provider is Tidal only.
- Authentication relies strictly on Tidal's native OAuth standard; user credentials are never handled directly.
- Full access is maintained for both public and private playlists under the authorized user account.
- Manual review is preserved for edge-case replacements so you never lose control over version changes or live edits.

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.