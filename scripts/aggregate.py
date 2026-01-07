#!/usr/bin/env python3
"""
Aggregate honeypot session data from VM directories into a canonical CSV.
Run this after sessions are created, or periodically to refresh the CSV.
"""
import pandas as pd
from pathlib import Path
import json
import glob
import sys

def aggregate_sessions(sessions_dir="data/sessions", output_csv="output/honeypot_sessions.csv"):
    """Aggregate meta.json files from session directories into a single CSV."""
    out = []
    
    if not Path(sessions_dir).exists():
        print(f"ERROR: Sessions directory '{sessions_dir}' not found.")
        return False
    
    session_files = glob.glob(f"{sessions_dir}/*/meta.json")
    if not session_files:
        print(f"WARNING: No meta.json files found in {sessions_dir}/*")
        return False
    
    for meta_path in sorted(session_files):
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                m = json.load(f)
        except Exception as e:
            print(f"  Skipping {meta_path}: {e}")
            continue
        
        # Extract and normalize fields
        session_id = m.get("session_id", "unknown")
        src_ip = m.get("src_ip", "127.0.0.1")
        src_port = int(m.get("src_port", 0)) if m.get("src_port") else None
        
        # Get timestamp from end_time or first event
        timestamp = m.get("end_time") or m.get("start_ts")
        if isinstance(timestamp, (int, float)):
            # Unix timestamp
            timestamp = pd.Timestamp.fromtimestamp(timestamp).isoformat()
        
        # Format events as readable summary
        events_list = m.get("events", [])
        events_text = " | ".join([
            e.get("text", "")[:60] 
            for e in events_list 
            if isinstance(e, dict) and e.get("text") and not any(
                skip in e.get("text", "") 
                for skip in ['[STRUCT_EVENT]', '[PAYLOAD_SAVED]', '[ACTION]=', '[CLASS]=', '[HIGH_ENGAGEMENT]=']
            )
        ])[:500] if events_list else "No events"
        
        # Extract attack type from [CLASS]= marker
        attack_type = "unknown"
        if isinstance(events_list, list):
            for e in events_list:
                if isinstance(e, dict) and '[class]=' in e.get("text", "").lower():
                    import re
                    m_match = re.search(r'\[class\]=([a-z_]+)', e.get("text", "").lower())
                    if m_match:
                        attack_type = m_match.group(1)
                        break
        
        dst_port = int(m.get("dst_port", 2222))
        instance = m.get("instance", "default")
        src_country = m.get("src_country", "LOCAL")
        
        out.append({
            "session_id": session_id,
            "src_ip": src_ip,
            "src_port": src_port,
            "timestamp": timestamp,
            "events": events_text,
            "dst_port": dst_port,
            "instance": instance,
            "attack_type": attack_type,
            "src_country": src_country
        })
    
    if not out:
        print("ERROR: No sessions aggregated.")
        return False
    
    df = pd.DataFrame(out)
    
    # Normalize types
    df['dst_port'] = pd.to_numeric(df['dst_port'], errors='coerce').astype('Int64')
    df['src_port'] = pd.to_numeric(df['src_port'], errors='coerce').astype('Int64')
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    
    # Write output
    Path("output").mkdir(exist_ok=True)
    df.to_csv(output_csv, index=False)
    print(f"✓ Wrote {len(df)} sessions to {output_csv}")
    return True

if __name__ == "__main__":
    success = aggregate_sessions()
    sys.exit(0 if success else 1)
