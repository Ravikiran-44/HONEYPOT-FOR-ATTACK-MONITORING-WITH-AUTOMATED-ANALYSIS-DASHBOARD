import json
import pandas as pd
from pathlib import Path
import sys
sys.path.insert(0, str(Path.cwd()))

# Import the functions from app_auto
import importlib.util
spec = importlib.util.spec_from_file_location("app_auto", "app_auto.py")
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)

# Test the new loader
SESSIONS_ROOT = Path("data/sessions")
df = app.load_vm_sessions(SESSIONS_ROOT)

if df is not None and len(df) > 0:
    print(f"✓ Loaded {len(df)} sessions from VM data")
    print(f"✓ Columns: {df.columns.tolist()}")
    print(f"\nFirst 3 rows:")
    print(df[['session_id', 'src_ip', 'dst_port', 'timestamp', 'attack_type']].head(3))
    
    # Test normalization
    df_norm = app.normalize_honeypot_data(df)
    print(f"\n✓ After normalize_honeypot_data():")
    print(f"  Columns: {df_norm.columns.tolist()}")
    print(f"  attack_type values: {df_norm['attack_type'].unique()[:5]}")
    print(f"  timestamp sample: {df_norm['timestamp'].iloc[0]}")
    
    # Test enrichment
    df_enriched = app.enrich_geo(df_norm)
    print(f"\n✓ After enrich_geo():")
    print(f"  src_country values: {df_enriched['src_country'].unique()}")
    print(f"\n✓ FULL PIPELINE WORKS - {len(df_enriched)} rows ready for dashboard")
else:
    print("✗ No sessions loaded")
