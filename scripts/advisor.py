# advisor.py
ATTACK_ADVICE = {
    "ssh_bruteforce": {
        "description": "Multiple failed login attempts on SSH port 22 — typical brute-force attempt using weak or default credentials.",
        "how_attacker_got_in": "Attacker scanned port 22, then tried dictionary-based logins using common usernames and passwords.",
        "recommendations": [
            "Disable password-based SSH login — use SSH keys instead.",
            "Change default usernames (e.g., root/admin).",
            "Use fail2ban or similar to block repeated SSH attempts.",
            "Restrict SSH access to specific IP ranges using firewall rules."
        ]
    },
    "web_scan": {
        "description": "Scanner probing web endpoints to detect vulnerable pages or outdated software.",
        "how_attacker_got_in": "The attacker crawled your web server and sent malformed or suspicious HTTP requests.",
        "recommendations": [
            "Keep all web frameworks and plugins updated.",
            "Use a web application firewall (WAF) to filter malicious requests.",
            "Hide admin panels and sensitive endpoints behind authentication."
        ]
    },
    "exploit": {
        "description": "Exploitation attempt targeting a known service or unpatched vulnerability.",
        "how_attacker_got_in": "The attacker exploited a known CVE vulnerability on an exposed service or web component.",
        "recommendations": [
            "Patch and update all software regularly.",
            "Use network segmentation to isolate critical systems.",
            "Monitor logs for signs of privilege escalation."
        ]
    },
    "malware_drop": {
        "description": "Attacker attempted to upload or execute a malicious file on your system.",
        "how_attacker_got_in": "Used file upload, weak authentication, or command injection to drop malware.",
        "recommendations": [
            "Enforce file type and size validation for uploads.",
            "Run uploaded files in sandbox before execution.",
            "Monitor for unusual outbound connections (C2 traffic)."
        ]
    },
    "recon": {
        "description": "Reconnaissance activity — mapping open ports and services.",
        "how_attacker_got_in": "Used nmap or similar scanning tools to detect available services.",
        "recommendations": [
            "Limit open ports to only necessary services.",
            "Implement port-knocking or rate-limiting.",
            "Use intrusion detection tools to alert on scan patterns."
        ]
    }
}