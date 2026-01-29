import json
import pandas as pd
from pathlib import Path

SESSIONS_ROOT = Path("data/sessions")

# Mimic load_vm_sessions from app_auto.py
dfs = []
if SESSIONS_ROOT.exists():
    for session_dir in sorted(SESSIONS_ROOT.glob("S-*")):
        meta_file = session_dir / "meta.json"
        if meta_file.exists():
            try:
                with open(meta_file, 'r', encoding='utf-8') as f:
                    obj = json.load(f)
                    if isinstance(obj, dict):
                        dfs.append(pd.DataFrame([obj]))
            except Exception as e:
                print(f"Error loading {meta_file}: {e}")

if dfs:
    df = pd.concat(dfs, ignore_index=True)
    print(f"Loaded {len(df)} sessions")
    print(f"Columns: {df.columns.tolist()}")
    print(f"\nFirst 2 rows (session_id, src_ip, instance, end_time):")
    print(df[['session_id', 'src_ip', 'instance', 'end_time']].head(2))
    print(f"\nUnique src_ips: {df['src_ip'].unique()}")
else:
    print("No DataFrames loaded")
