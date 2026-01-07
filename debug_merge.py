from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).parent
SESSIONS_ROOT = ROOT / "data" / "sessions"

def read_json_meta(p: Path):
    try:
        txt = p.read_text(encoding="utf-8").strip()
        if not txt:
            print(f"  {p.name}: empty")
            return None
        # Try to parse as single JSON object or list
        obj = json.loads(txt)
        print(f"  {p.name}: loaded as {type(obj).__name__}")
        if isinstance(obj, list):
            return pd.DataFrame(obj)
        elif isinstance(obj, dict):
            return pd.DataFrame([obj])
        return None
    except json.JSONDecodeError as e:
        # Try JSON lines format (one object per line)
        try:
            print(f"  {p.name}: trying JSON lines format")
            rows = [json.loads(line) for line in txt.splitlines() if line.strip()]
            if rows:
                print(f"    -> got {len(rows)} rows from JSON lines")
                return pd.DataFrame(rows)
        except Exception as e2:
            print(f"    -> JSON lines also failed: {e2}")
            pass
        print(f"  {p.name}: ERROR: {e}")
        return None
    except Exception as e:
        print(f"  {p.name}: ERROR: {e}")
        return None

# Test on first few
jsons = sorted(SESSIONS_ROOT.rglob("meta*.json"))[:3]
print(f"Testing {len(jsons)} JSON files:")
for p in jsons:
    df = read_json_meta(p)
    if df is not None:
        print(f"    -> DataFrame shape: {df.shape}, cols: {list(df.columns)[:5]}")
    else:
        print(f"    -> None")
