import json, glob, sys
files = glob.glob("data/sessions/**/meta.json", recursive=True)
if not files:
    print("NO_META")
    sys.exit(2)
f = files[0]
d = json.load(open(f))
print("FILE:", f)
print("KEYS:", list(d.keys()))
for k in ("session_id", "src_ip", "timestamp", "end_time", "events", "dst_port"):
    print(k, "->", ("PRESENT" if k in d else "MISSING"))
print("SAMPLE src_ip/timestamp:", d.get("src_ip"), d.get("timestamp") or d.get("end_time"))