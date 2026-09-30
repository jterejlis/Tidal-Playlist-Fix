class TidalSearchEngine:
    def __init__(self, tidal_client):
        self.tidal_client = tidal_client
        self.cache = {}

    def _key(self, query, limit):
        return f"{query.lower().strip()}::{limit}"

    def search(self, query, limit=10):
        key = self._key(query, limit)

        # 🔥 CACHE HIT
        if key in self.cache:
            return self.cache[key]

        # 🔴 API CALL
        results = self.tidal_client.session.search(query, limit=limit)

        raw_tracks = []

        # -------------------------
        # NORMALIZE RESPONSE SHAPE
        # -------------------------

        if isinstance(results, dict):
            tracks_block = results.get("tracks")

            if isinstance(tracks_block, dict):
                raw_tracks = tracks_block.get("items", [])
            elif isinstance(tracks_block, list):
                raw_tracks = tracks_block
            else:
                raw_tracks = []

        elif isinstance(results, list):
            raw_tracks = results

        else:
            raw_tracks = []

        # -------------------------
        # NORMALIZE TRACKS
        # -------------------------

        items = []

        for t in raw_tracks:
            if isinstance(t, dict):
                raw_artists = t.get("artists", [])
                track_id = t.get("id")
                title = t.get("title") or t.get("name")
                isrc = t.get("isrc")
            else:
                raw_artists = getattr(t, "artists", None) or getattr(t, "artist", None) or []
                track_id = getattr(t, "id", None)
                title = getattr(t, "title", None) or getattr(t, "name", None)
                isrc = getattr(t, "isrc", None)

            if track_id is None or title is None:
                continue

            artist_names = []
            if isinstance(raw_artists, list):
                for a in raw_artists:
                    if isinstance(a, dict):
                        name = a.get("name")
                    else:
                        name = getattr(a, "name", None)
                    if name:
                        artist_names.append(name)
            elif raw_artists is not None and not isinstance(raw_artists, str):
                name = getattr(raw_artists, "name", None)
                if name:
                    artist_names.append(name)

            items.append({
                "id": track_id,
                "name": title,
                "artists": artist_names,
                "isrc": isrc
            })

        result = {"items": items}

        # 🔥 CACHE STORE
        self.cache[key] = result

        return result