#!/usr/bin/env python3
"""
Standalone script to add GeoIP enrichment to existing CSV
"""
import pandas as pd
import geoip2.database
from pathlib import Path

GEOIP_DB_PATH = Path("data/GeoLite2-Country.mmdb")
CSV_PATH = Path("output/honeypot_sessions.csv")

def lookup_country(ip):
    """Lookup country code for a given IP."""
    if not ip or ip in ["nan", "127.0.0.1", "localhost", None]:
        return None
    try:
        with geoip2.database.Reader(str(GEOIP_DB_PATH)) as reader:
            response = reader.city(ip)
            return response.country.iso_code
    except Exception:
        return None

def enrich_csv_with_geoip():
    """Add src_country column to CSV using GeoIP database."""
    if not CSV_PATH.exists():
        print(f"❌ CSV not found: {CSV_PATH}")
        return
    
    if not GEOIP_DB_PATH.exists():
        print(f"❌ GeoIP database not found: {GEOIP_DB_PATH}")
        return
    
    print(f"📖 Loading CSV: {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)
    
    print(f"📊 CSV has {len(df)} rows")
    print(f"📍 Columns: {list(df.columns)}")
    
    # Check if src_country already exists
    if "src_country" in df.columns:
        print("⚠️  src_country column already exists. Skipping...")
        return
    
    # Get unique IPs (for caching)
    unique_ips = df["src_ip"].unique()
    print(f"\n🔍 Found {len(unique_ips)} unique src_ip values")
    print(f"   Sample IPs: {unique_ips[:5]}")
    
    # Lookup countries for each IP
    ip_to_country = {}
    print("\n🌍 Looking up countries...")
    for i, ip in enumerate(unique_ips):
        country = lookup_country(ip)
        ip_to_country[ip] = country
        if (i + 1) % 5 == 0:
            print(f"   ✓ Processed {i + 1}/{len(unique_ips)}")
    
    # Add src_country column
    df["src_country"] = df["src_ip"].map(ip_to_country)
    
    # Save updated CSV
    df.to_csv(CSV_PATH, index=False)
    print(f"\n✅ Updated CSV: {CSV_PATH}")
    print(f"   Total rows: {len(df)}")
    print(f"   With country data: {df['src_country'].notna().sum()}")
    print(f"\n📊 Country distribution:")
    country_counts = df["src_country"].value_counts()
    for country, count in country_counts.head(10).items():
        country_name = country if country else "Unknown"
        print(f"   {country_name}: {count}")

if __name__ == "__main__":
    enrich_csv_with_geoip()
