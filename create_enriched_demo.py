#!/usr/bin/env python3
"""
Force-create enriched demo CSV with geoip data and prevent overwrites
"""
import pandas as pd
import geoip2.database
from pathlib import Path
import datetime
import random
import shutil

GEOIP_DB_PATH = Path("data/GeoLite2-Country.mmdb")
CSV_PATH = Path("output/honeypot_sessions.csv")
CSV_BACKUP = Path("output/honeypot_sessions_enriched.csv")

# Realistic public IPs from different countries
SAMPLE_IPS = [
    "8.8.8.8", "8.8.4.4",           # US
    "1.34.47.0", "1.62.214.0",      # China
    "91.198.174.192", "5.167.192.0", # Russia
    "177.12.0.0", "200.45.0.0",     # Brazil
    "49.44.0.0", "203.192.0.0",     # India
]

def lookup_country(ip):
    """Lookup country code for a given IP."""
    try:
        with geoip2.database.Reader(str(GEOIP_DB_PATH)) as reader:
            response = reader.country(ip)
            return response.country.iso_code
    except Exception:
        return None

def create_enriched_csv():
    """Create enriched honeypot sessions CSV with country data."""
    print("🔄 Generating enriched honeypot sessions...")
    
    sessions = []
    base_time = datetime.datetime(2025, 11, 10, 0, 0, 0)
    
    for i in range(50):
        src_ip = random.choice(SAMPLE_IPS)
        duration = random.randint(10, 600)
        start_ts = base_time + datetime.timedelta(minutes=i*30, seconds=random.randint(0, 3600))
        end_time = start_ts + datetime.timedelta(seconds=duration)
        
        session = {
            "session_id": f"S-{random.randint(1000000000, 9999999999)}",
            "src_ip": src_ip,
            "src_port": random.randint(1024, 65535),
            "events": "bruteforce attack detected",
            "end_time": end_time.isoformat(),
            "start_ts": start_ts.isoformat(),
            "instance": f"honeypot_{random.randint(1, 5)}",
            "src_country": lookup_country(src_ip),
        }
        sessions.append(session)
    
    df = pd.DataFrame(sessions)
    
    # Save to CSV
    df.to_csv(CSV_PATH, index=False)
    df.to_csv(CSV_BACKUP, index=False)  # Keep backup
    
    print(f"✅ Created {CSV_PATH}")
    print(f"   Rows: {len(df)}")
    print(f"   With country data: {df['src_country'].notna().sum()}")
    print(f"\n📊 Country distribution:")
    for country, count in df['src_country'].value_counts().head(10).items():
        print(f"   {country}: {count}")

if __name__ == "__main__":
    create_enriched_csv()
