# enrich_output_csv.py
from pathlib import Path
import pandas as pd
import geoip2.database
import sys

DB = Path("data/GeoLite2-Country.mmdb")
CSV = Path("output/honeypot_sessions.csv")

if not DB.exists():
    print("ERROR: GeoLite2 DB not found at", DB)
    sys.exit(1)
if not CSV.exists():
    print("ERROR: sessions CSV not found at", CSV)
    sys.exit(1)

print("Loading CSV:", CSV)
df = pd.read_csv(CSV, dtype=str)

if 'src_ip' not in df.columns:
    print("ERROR: src_ip column missing in CSV. Columns:", df.columns.tolist())
    sys.exit(1)

# fill blank src_country if missing
try:
    with geoip2.database.Reader(str(DB)) as reader:
        def lookup(ip):
            try:
                if not isinstance(ip, str) or ip.strip()=="" or ip.startswith("127.") or ip.startswith("10.") or ip.startswith("192.168."):
                    return None
                r = reader.country(ip)
                return r.country.iso_code
            except Exception:
                return None
        df['src_country'] = df.get('src_country', pd.NA).fillna(df['src_ip'].map(lookup))
except Exception as e:
    print("GeoIP lookup error:", e)
    sys.exit(1)

print("Non-null src_country after enrichment:", int(df['src_country'].notna().sum()), "of", len(df))
df.to_csv(CSV, index=False)
print("Wrote enriched CSV:", CSV)
