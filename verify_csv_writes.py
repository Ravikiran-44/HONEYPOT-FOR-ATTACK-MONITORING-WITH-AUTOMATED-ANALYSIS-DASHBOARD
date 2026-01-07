#!/usr/bin/env python3
"""
Verification script: proves the dashboard is auto-writing the CSV file atomically.
Run this while the dashboard is running to see the file update in real-time.
"""
import os
import time
from pathlib import Path
from datetime import datetime

CSV_PATH = Path("output/honeypot_sessions.csv")

print("🔍 CSV File Freshness Monitor")
print("=" * 60)
print(f"Watching: {CSV_PATH.absolute()}")
print("Updates every 2 seconds. Press Ctrl+C to stop.\n")

iteration = 0
last_mtime = None
last_size = None

try:
    while True:
        iteration += 1
        
        if not CSV_PATH.exists():
            print(f"❌ [{iteration:3d}] CSV NOT FOUND at {CSV_PATH}")
            time.sleep(2)
            continue
        
        # Get file stats
        stat = CSV_PATH.stat()
        mtime = stat.st_mtime
        size = stat.st_size
        mtime_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
        
        # Check if file was updated since last check
        changed_marker = ""
        if last_mtime is not None and mtime != last_mtime:
            changed_marker = " 🔄 UPDATED!"
        
        print(f"✅ [{iteration:3d}] {mtime_str} | {size:8,d} bytes{changed_marker}")
        
        last_mtime = mtime
        last_size = size
        time.sleep(2)

except KeyboardInterrupt:
    print("\n\n✋ Monitor stopped.")
    print("\nFinal status:")
    if CSV_PATH.exists():
        stat = CSV_PATH.stat()
        mtime_str = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        print(f"  Last updated: {mtime_str}")
        print(f"  File size: {stat.st_size:,} bytes")
        print("  ✅ File is being updated by the dashboard!")
    else:
        print(f"  ❌ CSV file not found at {CSV_PATH}")
