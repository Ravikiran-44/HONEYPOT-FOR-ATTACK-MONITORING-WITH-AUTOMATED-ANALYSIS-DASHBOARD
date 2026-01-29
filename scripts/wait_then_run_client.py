# -*- coding: utf-8 -*-
"""
wait_then_run_client.py
Tries to connect to 127.0.0.1:2222 until it receives a banner (retries),
then runs the interactive test client (test_client_interactive.py).
"""
import socket, time, subprocess, sys, os

HOST = "127.0.0.1"
PORT = 2222
TIMEOUT = 8.0
RETRY_DELAY = 1.0   # seconds between attempts
MAX_RETRIES = 30    # total wait up to ~30s (adjust if needed)

def wait_for_banner():
    for attempt in range(1, MAX_RETRIES+1):
        try:
            s = socket.socket()
            s.settimeout(TIMEOUT)
            s.connect((HOST, PORT))
            banner = s.recv(4096).decode(errors="ignore")
            s.close()
            if banner:
                print(f"[OK] Banner received on attempt {attempt}: {banner.strip()}")
                return True
            else:
                print(f"[WARN] Connected but no banner (attempt {attempt})")
        except Exception as e:
            print(f"[INFO] Attempt {attempt}: connect error: {e!r}")
        time.sleep(RETRY_DELAY)
    return False

if __name__ == "__main__":
    ok = wait_for_banner()
    if not ok:
        print("[ERROR] Could not get banner after retries. Exiting with failure.")
        sys.exit(2)

    # if banner seen, run the real test client
    print("[INFO] Running test_client_interactive.py now...")
    # ensure using venv python if venv activated; otherwise system python
    py = sys.executable or "python"
    client_path = os.path.join(os.getcwd(), "test_client_interactive.py")
    if not os.path.exists(client_path):
        print(f"[ERROR] test_client_interactive.py not found at {client_path}")
        sys.exit(3)
    # run the test client as a subprocess (stream output)
    p = subprocess.Popen([py, client_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in p.stdout:
        print(line, end="")
    p.wait()
    sys.exit(p.returncode)
