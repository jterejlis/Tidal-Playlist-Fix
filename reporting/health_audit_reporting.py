import json
from datetime import datetime
from reporting.formatters import format_health_audit_report

def save_playlist_audit(audit_data, filename="playlist_audit.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(audit_data, f, ensure_ascii=False, indent=2)

def load_playlist_audit(filename="playlist_audit.json"):
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def show_report(report=None, file=None):
    if file:
        report = load_playlist_audit(file)

    if not report:
        print("No report provided")
        return

    print(format_health_audit_report(report))
