# C:\project\validate_meta.py
import json, glob, sys, os

files = glob.glob(os.path.join("data", "sessions", "**", "meta.json"), recursive=True)
if not files:
    print("NO_META")
    sys.exit(2)

f = sorted(files, key=lambda p: os.path.getmtime(p), reverse=True)[0]
print("FILE:", os.path.abspath(f))
try:
    with open(f, "r", encoding="utf-8") as fh:
        d = json.load(fh)
except Exception as e:
    print("ERROR: failed to parse JSON:", e)
    sys.exit(3)

print("KEYS:", list(d.keys()))
required = ("session_id","src_ip","timestamp","end_time","events","dst_port")
for k in required:
    print(f"{k:12} ->", "PRESENT" if k in d else "MISSING")
print("SAMPLE src_ip/timestamp:", d.get("src_ip"), d.get("timestamp") or d.get("end_time"))
print("\nFull JSON (first 400 chars):")
s = json.dumps(d, indent=2)
print(s[:400] + (" ... (truncated)" if len(s) > 400 else ""))
