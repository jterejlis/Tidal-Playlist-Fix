import json

def load_tracks_from_file(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
    
def export_playlist(items, export_path):
  

    payload = {
        "items": items
    }

    with open(export_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)