import json, time
from pathlib import Path

BASE = Path(__file__).resolve().parents[1] / "data" / "sessions"
BASE.mkdir(parents=True, exist_ok=True)

def new_session(src_ip, src_port):
    sid = f"S-{int(time.time())}"
    sdir = BASE / sid; sdir.mkdir(exist_ok=True)
    meta = {"session_id": sid, "src_ip": src_ip, "src_port": src_port, "events": []}
    with open(sdir / "meta.json", "w") as f: json.dump(meta, f, indent=2)
    return sid, sdir

def append_event(sdir, event):
    p = Path(sdir) / "meta.json"
    meta = json.load(open(p)) if p.exists() else {"events": []}
    meta.setdefault("events", []).append(event)
    json.dump(meta, open(p, "w"), indent=2)

def close_session(sdir):
    p = Path(sdir) / "meta.json"
    if p.exists(): meta = json.load(open(p)); meta["end_time"] = time.ctime(); json.dump(meta, open(p, "w"), indent=2)
