# src/export_sessions.py
"""Convert session meta.json files into a normalized CSV for reporting."""
import json
from pathlib import Path
import pandas as pd
import time

def extract_session_info(meta_path):
    """Extract key fields from a session meta.json file."""
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    events = meta.get("events", [])
    # Extract key fields
    info = {
        "session_id": meta.get("session_id", ""),
        "src_ip": meta.get("src_ip", ""),
        "src_port": meta.get("src_port", -1),
        "timestamp": pd.to_datetime(meta.get("start_time", time.ctime())),
        "dst_port": 2222,  # default honeypot port
        "attack_type": "unknown",
        "success": 0,
        "bytes_in": 0,
        "bytes_out": 0,
        "username": "",
        "password": "",
        "transcript": "",
    }

    # Parse events for key info
    cmds = []
    for ev in events:
        text = ev.get("text", "")
        ts = pd.to_datetime(time.ctime(ev.get("ts", 0)))
        info["timestamp"] = min(info["timestamp"], ts)  # use earliest event time

        if "[CLASS]=" in text:
            parts = text.split("=")[1].split("|")
            if len(parts) >= 2:
                info["attack_type"] = parts[0]
                info["success"] = 1 if "success" in parts[0].lower() else 0

        elif "[STRUCT_EVENT]=" in text:
            try:
                struct = json.loads(text.split("=", 1)[1])
                if struct.get("type") == "classification":
                    info["attack_type"] = struct.get("label", info["attack_type"])
                    info["success"] = 1 if "success" in str(struct.get("label", "")).lower() else 0
                    if "vector" in struct:
                        info["attack_type"] = f"{info['attack_type']}_{struct['vector']}"
            except:
                pass

        elif "[PAYLOAD_SAVED]=" in text:
            info["success"] = 1  # if payload captured, mark as successful
            try:
                payload = json.loads(text.split("=", 1)[1])
                info["bytes_in"] += int(payload.get("size", 0))
            except:
                pass

        elif not text.startswith("["):  # capture raw command transcript
            cmds.append(text)

    info["transcript"] = "\n".join(cmds)
    return info

def sessions_to_csv(sessions_dir, output_csv):
    """Convert all session meta.json files under sessions_dir into a single CSV."""
    sessions_dir = Path(sessions_dir)
    rows = []

    # Find all meta.json files
    for meta in sessions_dir.glob("*/meta.json"):
        try:
            info = extract_session_info(meta)
            rows.append(info)
        except Exception as e:
            print(f"Error processing {meta}: {e}")

    if not rows:
        print("No sessions found!")
        return False

    # Convert to DataFrame and save
    df = pd.DataFrame(rows)
    # Ensure output directory exists
    Path(output_csv).parent.mkdir(parents=True, exist_ok=True)
    # Write to temp then rename for atomic operation
    tmp_path = str(output_csv) + ".tmp"
    df.to_csv(tmp_path, index=False)
    Path(tmp_path).rename(output_csv)
    return True

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python export_sessions.py <sessions_dir> <output_csv>")
        sys.exit(1)
    if sessions_to_csv(sys.argv[1], sys.argv[2]):
        print(f"Wrote CSV: {sys.argv[2]}")
    else:
        print("Failed to create CSV (no sessions found)")
        sys.exit(1)