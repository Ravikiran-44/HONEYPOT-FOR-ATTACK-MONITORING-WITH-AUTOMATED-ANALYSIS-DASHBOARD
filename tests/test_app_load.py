#!/usr/bin/env python3
"""Test if the app's data loading logic works."""
import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).parent
OUT_CSV = ROOT / "output" / "honeypot_sessions.csv"

# Step 1: Check if CSV exists
print(f"CSV exists: {OUT_CSV.exists()}")
print(f"CSV path: {OUT_CSV}")

# Step 2: Try to load CSV
if OUT_CSV.exists():
    try:
        df = pd.read_csv(OUT_CSV)
        print(f"✅ CSV loaded successfully: {len(df)} rows")
        print(f"   Columns: {df.columns.tolist()}")
        print(f"   src_country non-null: {df['src_country'].notna().sum()}")
    except Exception as e:
        print(f"❌ Failed to load CSV: {e}")
        sys.exit(1)
else:
    print(f"❌ CSV not found at {OUT_CSV}")
    sys.exit(1)

# Step 3: Test if normalize_honeypot_data works
sys.path.insert(0, str(ROOT))
try:
    # Import the functions directly
    from app_auto import normalize_honeypot_data, enrich_geo
    
    print("\n🔄 Testing normalize_honeypot_data...")
    df_norm = normalize_honeypot_data(df)
    print(f"✅ Normalized: {len(df_norm)} rows")
    print(f"   Columns after normalize: {df_norm.columns.tolist()}")
    
    print("\n🔄 Testing enrich_geo...")
    df_enriched = enrich_geo(df_norm)
    print(f"✅ Enriched: {len(df_enriched)} rows")
    print(f"   Columns after enrich: {df_enriched.columns.tolist()}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✅ All tests passed! App should load data correctly.")
