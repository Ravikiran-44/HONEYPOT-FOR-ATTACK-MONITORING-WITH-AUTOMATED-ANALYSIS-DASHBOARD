# verify_meta_integrity.py
import hashlib, json, pathlib, sys

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

issues = []
for s in sorted(DATA.iterdir(), key=lambda p: p.stat().st_mtime):
    meta_file = s / "meta.json"
    if not meta_file.exists():
        continue
    meta = json.loads(meta_file.read_text(encoding="utf-8"))
    for ev in meta.get("events", []):
        txt = ev.get("text","")
        if txt.startswith("[PAYLOAD_SAVED]="):
            try:
                payload_meta = txt.split("=",1)[1]
                # evaluate dict safely-ish by replacing single quotes
                if payload_meta.strip().startswith("{"):
                    payload_meta = payload_meta.replace("'", '"')
                    pm = json.loads(payload_meta)
                else:
                    # fallback: treat as string path
                    pm = {"path": payload_meta}
                p = pathlib.Path(pm.get("path") or pm.get("file"))
                if not p.exists():
                    issues.append((s.name, "file_missing", str(p)))
                    continue
                actual_sha = sha256_file(p)
                if pm.get("sha256") != actual_sha:
                    issues.append((s.name, "sha_mismatch", str(p), pm.get("sha256"), actual_sha))
            except Exception as e:
                issues.append((s.name, "parse_error", str(e)))
if not issues:
    print("All payload entries verified OK.")
else:
    print("Issues found:")
    for it in issues:
        print(it)