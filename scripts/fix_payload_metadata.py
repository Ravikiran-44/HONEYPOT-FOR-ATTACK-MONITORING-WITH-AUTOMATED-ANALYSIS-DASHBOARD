# fix_payload_metadata.py
import json, pathlib, hashlib, sys, time

DATA = pathlib.Path("data/sessions")
if not DATA.exists():
    print("No data/sessions folder found.")
    sys.exit(1)

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while True:
            b = f.read(8192)
            if not b:
                break
            h.update(b)
    return h.hexdigest()

fixed = 0
for s in sorted(DATA.iterdir(), key=lambda p: p.stat().st_mtime):
    meta_file = s / "meta.json"
    if not meta_file.exists():
        continue
    meta = json.loads(meta_file.read_text(encoding="utf-8"))
    changed = False
    for ev in meta.get("events", []):
        txt = ev.get("text","")
        if txt.startswith("[PAYLOAD_SAVED]="):
            payload_info = txt.split("=",1)[1].strip()
            # If payload_info looks like a JSON dict already, skip
            if payload_info.startswith("{") and payload_info.endswith("}"):
                continue
            # Otherwise treat it as path or filename
            p = pathlib.Path(payload_info)
            if not p.exists():
                # try resolve relative to session dir
                p = s / p.name
            if not p.exists():
                print("WARNING: payload file not found for session", s, "value:", payload_info)
                continue
            sha = sha256_file(p)
            size = p.stat().st_size
            meta_payload = {
                "file": p.name,
                "path": str(p.resolve()),
                "sha256": sha,
                "size": size,
                "saved_ts": time.time()
            }
            ev["text"] = f"[PAYLOAD_SAVED]={meta_payload}"
            changed = True
            fixed += 1
    if changed:
        meta_file.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        print("Updated meta.json for", s)
print("Done. Fixed payload entries:", fixed)
