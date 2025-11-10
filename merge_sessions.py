# merge_sessions.py
import pandas as pd
from pathlib import Path
import json

ROOT = Path(__file__).parent
SESSIONS_ROOT = ROOT / "data" / "sessions"
OUT_CSV = ROOT / "output" / "honeypot_sessions.csv"

def read_csv(p: Path):
    try:
        return pd.read_csv(p, dtype=str)
    except Exception:
        return None

def read_json_meta(p: Path):
    try:
        txt = p.read_text(encoding="utf-8").strip()
        if not txt:
            return None
        # Try to parse as single JSON object or list
        obj = json.loads(txt)
        if isinstance(obj, list):
            return pd.DataFrame(obj)
        elif isinstance(obj, dict):
            return pd.DataFrame([obj])
        return None
    except json.JSONDecodeError:
        # Try JSON lines format (one object per line)
        try:
            rows = [json.loads(line) for line in txt.splitlines() if line.strip()]
            if rows:
                return pd.DataFrame(rows)
        except Exception:
            pass
        return None
    except Exception:
        return None

def gather_and_merge(root_dir: Path = SESSIONS_ROOT, out_csv: Path = OUT_CSV):
    dfs = []
    if not root_dir.exists():
        return False
    # collect JSON meta files FIRST (they have more data)
    for p in sorted(root_dir.rglob("meta*.json")):
        df = read_json_meta(p)
        if df is not None and not df.empty:
            dfs.append(df)
    # collect CSVs SECOND (they have less data, will be deduplicated)
    for p in sorted(root_dir.rglob("*.csv")):
        df = read_csv(p)
        if df is not None and not df.empty:
            dfs.append(df)
    if not dfs:
        return False
    merged = pd.concat(dfs, ignore_index=True, sort=False)
    # optional dedupe if session_id present - keep FIRST (which is JSON, more data)
    if 'session_id' in merged.columns:
        merged = merged.drop_duplicates(subset=['session_id'], keep='first')
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(out_csv, index=False)
    return True

if __name__ == "__main__":
    ok = gather_and_merge()
    print("Merged:", ok)