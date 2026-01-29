# show_latest_session.py
# Utility to show the most recent honeypot session log (meta.json)

import pathlib, json

data_dir = pathlib.Path("data/sessions")

if not data_dir.exists():
    print("No sessions folder found.")
    raise SystemExit

sessions = sorted(data_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
if not sessions:
    print("No sessions yet.")
    raise SystemExit

latest = sessions[0]
meta_file = latest / "meta.json"

print(f"USING SESSION DIR: {latest}")
if not meta_file.exists():
    print("No meta.json found in that session.")
else:
    with open(meta_file, "r", encoding="utf-8") as f:
        meta = json.load(f)
    print(json.dumps(meta, indent=2))
