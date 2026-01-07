import json, pathlib, collections

ROOT = pathlib.Path(".")
SESSIONS = ROOT / "data" / "sessions"

counts = collections.Counter()
total = 0
for p in sorted(SESSIONS.rglob("meta*.json")):
    try:
        obj = json.loads(p.read_text(encoding="utf-8").strip())
        # obj may be dict or list; normalize to list of dicts
        rows = obj if isinstance(obj, list) else [obj]
        for r in rows:
            total += 1
            at = r.get("attack_type", None)
            if at is None:
                at = r.get("attack", None)
            if at is None:
                at = "MISSING"
            counts[str(at).lower().strip()] += 1
    except Exception as e:
        print("ERR reading", p, e)

print(f"Total meta.json rows scanned: {total}")
print("Attack-type counts:")
for k, v in counts.most_common():
    print(f"  {k!r}: {v}")
