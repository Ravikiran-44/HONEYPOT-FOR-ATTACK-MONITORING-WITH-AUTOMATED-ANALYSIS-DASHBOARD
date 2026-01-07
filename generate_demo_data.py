#!/usr/bin/env python3
"""
Generate sample honeypot sessions with realistic public IPs for demo
"""
import pandas as pd
import geoip2.database
from pathlib import Path
import datetime
import random

GEOIP_DB_PATH = Path("data/GeoLite2-Country.mmdb")
CSV_PATH = Path("output/honeypot_sessions.csv")

# Realistic public IPs from different countries (for demo)
SAMPLE_IPS = [
    # US
    "8.8.8.8", "8.8.4.4",
    # China
    "1.34.47.0", "1.62.214.0",
    # Russia
    "91.198.174.192", "5.167.192.0",
    # Brazil
    "177.12.0.0", "200.45.0.0",
    # India
    "49.44.0.0", "203.192.0.0",
]

ATTACK_TYPES = [
    "bruteforce", "recon", "malware", "exploit", "unknown"
]

def lookup_country(ip):
    """Lookup country code for a given IP."""
    try:
        with geoip2.database.Reader(str(GEOIP_DB_PATH)) as reader:
            response = reader.country(ip)
            return response.country.iso_code
    except Exception:
        return None

def generate_sample_sessions(count=50):
    """Generate sample honeypot session data with real IPs."""
    sessions = []
    
    base_time = datetime.datetime(2025, 11, 10, 0, 0, 0)
    
    for i in range(count):
        # Pick random IP and time
        src_ip = random.choice(SAMPLE_IPS)
        attack_type = random.choice(ATTACK_TYPES)
        duration = random.randint(10, 600)  # 10 seconds to 10 minutes
        
        start_ts = base_time + datetime.timedelta(minutes=i*30, seconds=random.randint(0, 3600))
        end_time = start_ts + datetime.timedelta(seconds=duration)
        
        # Create event log
        events = {
            "attack_type": attack_type,
            "commands": ["id", "whoami", "ls -la"][:random.randint(1, 3)],
            "payloads": random.randint(0, 5)
        }
        
        session = {
            "session_id": f"S-{random.randint(1000000000, 9999999999)}",
            "src_ip": src_ip,
            "src_port": random.randint(1024, 65535),
            "events": str(events),
            "start_ts": start_ts.isoformat(),
            "end_time": end_time.isoformat(),
            "instance": f"honeypot_{random.randint(1, 5)}",
        }
        sessions.append(session)
    
    return pd.DataFrame(sessions)

def main():
    print("🔄 Generating sample honeypot sessions with real IPs...")
    
    # Generate data
    df = generate_sample_sessions(count=50)
    
    # Add GeoIP enrichment
    print("\n🌍 Adding GeoIP enrichment...")
    df["src_country"] = df["src_ip"].apply(lookup_country)
    
    # Save to CSV
    df.to_csv(CSV_PATH, index=False)
    
    print(f"\n✅ Created {CSV_PATH}")
    print(f"   Total sessions: {len(df)}")
    print(f"   With country data: {df['src_country'].notna().sum()}")
    
    print(f"\n📊 Country distribution:")
    for country, count in df["src_country"].value_counts().items():
        print(f"   {country}: {count} sessions")
    
    print(f"\n🎯 Sample rows:")
    print(df[["session_id", "src_ip", "src_country", "instance"]].head(10).to_string())

if __name__ == "__main__":
    main()
