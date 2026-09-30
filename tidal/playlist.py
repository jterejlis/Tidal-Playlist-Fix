import json
from datetime import datetime
from duplicates.exact_duplicates import find_exact_duplicates

class PlaylistService:
    def __init__(self, client):
        self.client = client

    def get_user_playlists(self):
        playlists = self.client.session.user.playlists()

        clean_playlists = [
            {"id": p.id, "name": p.name}
            for p in playlists
        ]

        return clean_playlists

    def get_playlist_tracks(self, playlist_id):
        playlist = self.client.session.playlist(playlist_id)

        clean_tracks = []
        for t in playlist.tracks():
            artists = []
            if hasattr(t, "artists") and t.artists:
                artists = [a.name for a in t.artists if getattr(a, "name", None)]
            elif getattr(t, "artist", None):
                artists = [t.artist.name]

            clean_tracks.append({
                "id": t.id,
                "name": t.name,
                "artists": artists,
                "isrc": t.isrc,
            })

        return clean_tracks

    def save_playlists(self, filename="playlists.json"):
        data = {
            "saved_at": datetime.now().isoformat(),
            "items": self.get_user_playlists()
        }

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def save_playlist_tracks(self, playlist_id, filename=None):
        data = {
            "saved_at": datetime.now().isoformat(),
            "items": self.get_playlist_tracks(playlist_id)
        }

        filename = filename or f"playlist_{playlist_id}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def create_playlist(self, track_ids=None, name=None, description=None):
        self.client._require_login()

        name = name or datetime.now().strftime("Playlist %Y-%m-%d %H:%M:%S UTC")
        description = description or "Created by Tidal-Playlist-Fix"

        playlist = self.client.session.user.create_playlist(name, description)
        if track_ids:
            playlist.add(track_ids)

        return {
            "id": playlist.id,
            "name": playlist.name,
            "description": description,
        }

    def track_exists(self, track_id):
        try:
            track = self.client.session.track(track_id)
            return track is not None
        except Exception:
            return False

    def playlist_audit(self, playlist_id):
        tracks = self.get_playlist_tracks(playlist_id)

        dead = []
        ok = []

        for track in tracks:
            if self.track_exists(track["id"]):
                ok.append(track)
            else:
                dead.append(track)

        return {
            "playlist_id": playlist_id,
            "total": len(tracks),
            "ok": ok,
            "dead": dead,
            "exact_duplicates": find_exact_duplicates(tracks),
        }
