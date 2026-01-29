"""Start the orchestrator in-thread, connect a test client, and print the created session.

This script is for local testing only.
"""
import time
import socket
import json
from threading import Thread
from pathlib import Path

from src.orchestrator import Orchestrator


def start_orchestrator():
    orch = Orchestrator()
    orch.start()


def wait_for_port(host, port, timeout=5.0):
    end = time.time() + timeout
    while time.time() < end:
        try:
            s = socket.create_connection((host, port), timeout=0.5)
            s.close()
            return True
        except Exception:
            time.sleep(0.1)
    return False


def run_client(host='127.0.0.1', port=2222):
    try:
        s = socket.create_connection((host, port), timeout=3)
    except Exception as e:
        print('Client: connection failed:', e)
        return
    try:
        try:
            b = s.recv(4096)
            print('Client: Banner:', b.decode(errors='ignore'))
        except Exception:
            pass
        # send a wget style command to trigger payload saving
        cmd = 'wget http://example.com/test.bin\n'
        print('Client: Sending:', cmd.strip())
        s.sendall(cmd.encode())
        time.sleep(0.5)
        try:
            r = s.recv(4096)
            print('Client: Response:', r.decode(errors='ignore'))
        except Exception:
            pass
    finally:
        s.close()


def print_latest_session():
    base = Path(__file__).resolve().parents[1] / 'data' / 'sessions'
    if not base.exists():
        print('No sessions directory found:', base)
        return
    sessions = sorted([p for p in base.iterdir() if p.is_dir()], key=lambda p: p.name)
    if not sessions:
        print('No sessions found in', base)
        return
    last = sessions[-1]
    meta = last / 'meta.json'
    if not meta.exists():
        print('No meta.json in', last)
        return
    print('\n--- Latest session meta.json ---')
    print(json.dumps(json.load(open(meta, 'r', encoding='utf-8')), indent=2))


def main():
    t = Thread(target=start_orchestrator, daemon=True)
    t.start()
    print('Started orchestrator thread, waiting for port...')
    if not wait_for_port('127.0.0.1', 2222, timeout=5.0):
        print('Orchestrator did not open port 2222 within timeout')
        return
    print('Port 2222 open — running client')
    run_client()
    time.sleep(0.8)
    print_latest_session()


if __name__ == '__main__':
    main()
