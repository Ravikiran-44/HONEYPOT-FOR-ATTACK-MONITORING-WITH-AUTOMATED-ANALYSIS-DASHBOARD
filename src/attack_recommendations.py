"""
Attack type recommendations and remediation guidance.
Maps each attack type to structured remediation steps.
"""

ATTACK_RECOMMENDATIONS = {
    "recon": {
        "title": "Reconnaissance / Port Scanning",
        "description": "Attacker is mapping the network: port scans, service enumeration, banner grabbing.",
        "how_got_in": "Unfiltered ports and verbose service banners allow information gathering.",
        "severity": "Medium - Early stage of attack chain",
        "actions": [
            {
                "priority": "HIGH",
                "title": "Minimize exposed ports",
                "description": "Close all unused ports and services.",
                "commands": [
                    "netstat -tulpn | grep LISTEN  # identify listening ports",
                    "ufw default deny incoming",
                    "ufw allow 22/tcp  # only allow SSH"
                ],
                "why": "Reduces attack surface and reconnaissance opportunities"
            },
            {
                "priority": "HIGH",
                "title": "Harden service banners",
                "description": "Remove or obfuscate service version information.",
                "commands": [
                    "# SSH: Edit /etc/ssh/sshd_config",
                    "DebianBanner no",
                    "Banner /etc/issue.net",
                    "systemctl restart ssh"
                ],
                "why": "Prevents fingerprinting and reduces vulnerability disclosure"
            },
            {
                "priority": "MEDIUM",
                "title": "Deploy network IDS",
                "description": "Install Snort or Suricata to detect scanning patterns.",
                "commands": [
                    "apt-get install snort",
                    "snort -d -l ./logs -i eth0 -c /etc/snort/snort.conf"
                ],
                "why": "Detects and alerts on scanning behavior in real-time"
            },
            {
                "priority": "MEDIUM",
                "title": "Enable rate limiting",
                "description": "Limit port scans and connection attempts.",
                "commands": [
                    "iptables -A INPUT -p tcp --dport 22 -m limit --limit 25/minute --limit-burst 100 -j ACCEPT"
                ],
                "why": "Slows down scanning and makes reconnaissance more visible"
            }
        ]
    },
    "exploit": {
        "title": "Exploitation Attempt / Payload Delivery",
        "description": "Attacker is attempting to deliver exploit code or malicious payloads.",
        "how_got_in": "Vulnerable service with known CVE or unpatched software; wget/curl used to retrieve payloads.",
        "severity": "CRITICAL - Active compromise attempt",
        "actions": [
            {
                "priority": "HIGH",
                "title": "Immediately patch vulnerable software",
                "description": "Apply security updates to all services.",
                "commands": [
                    "apt-get update && apt-get upgrade",
                    "systemctl restart affected-service"
                ],
                "why": "Closes the exploit vector immediately"
            },
            {
                "priority": "HIGH",
                "title": "Block payload delivery URLs",
                "description": "Prevent retrieval of malicious files from known attacker infrastructure.",
                "commands": [
                    "iptables -A OUTPUT -d malicious.example -j DROP",
                    "# or use firewall rules in your WAF"
                ],
                "why": "Prevents payload execution even if exploit succeeds"
            },
            {
                "priority": "HIGH",
                "title": "Isolate compromised services",
                "description": "Move vulnerable services behind additional network segmentation.",
                "commands": [
                    "# Create VLAN for isolated service",
                    "# Restrict access to trusted subnets only"
                ],
                "why": "Limits lateral movement if service is compromised"
            },
            {
                "priority": "MEDIUM",
                "title": "Deploy Web Application Firewall (WAF)",
                "description": "Use ModSecurity or similar to block exploit patterns.",
                "commands": [
                    "apt-get install libapache2-mod-security2",
                    "a2enmod security2",
                    "systemctl restart apache2"
                ],
                "why": "Detects and blocks known exploit patterns"
            },
            {
                "priority": "MEDIUM",
                "title": "Enable endpoint detection and response (EDR)",
                "description": "Monitor for suspicious process execution and memory writes.",
                "commands": [
                    "# Install EDR agent (e.g., Crowdstrike, Microsoft Defender, Wazuh)"
                ],
                "why": "Detects payload execution and enables rapid response"
            }
        ]
    },
    "bruteforce": {
        "title": "Brute Force / Credential Attack",
        "description": "Attacker is attempting to guess credentials through repeated login attempts.",
        "how_got_in": "Service (SSH, RDP, etc.) exposed with weak or default credentials.",
        "severity": "High - Direct account compromise risk",
        "actions": [
            {
                "priority": "HIGH",
                "title": "Disable password authentication",
                "description": "Enforce SSH keys only; remove password login.",
                "commands": [
                    "# Edit /etc/ssh/sshd_config",
                    "PasswordAuthentication no",
                    "PubkeyAuthentication yes",
                    "systemctl restart ssh"
                ],
                "why": "Eliminates credential guessing vectors"
            },
            {
                "priority": "HIGH",
                "title": "Enforce strong password policy",
                "description": "Set password complexity and expiration rules.",
                "commands": [
                    "apt-get install libpam-pwquality",
                    "# Configure /etc/security/pwquality.conf"
                ],
                "why": "Weakens dictionary attacks"
            },
            {
                "priority": "HIGH",
                "title": "Implement login lockout after N failures",
                "description": "Lock account or IP after failed attempts.",
                "commands": [
                    "apt-get install fail2ban",
                    "systemctl enable fail2ban",
                    "systemctl start fail2ban"
                ],
                "why": "Stops brute force attacks by blocking repeated attempts"
            },
            {
                "priority": "MEDIUM",
                "title": "Use multi-factor authentication (MFA)",
                "description": "Require second factor (TOTP, hardware key) for login.",
                "commands": [
                    "apt-get install libpam-google-authenticator",
                    "# Configure PAM for TOTP"
                ],
                "why": "Makes credential compromise alone insufficient for access"
            },
            {
                "priority": "MEDIUM",
                "title": "Rate limit login attempts",
                "description": "Throttle authentication endpoints.",
                "commands": [
                    "iptables -A INPUT -p tcp --dport 22 -m state --state NEW -m recent --set",
                    "iptables -A INPUT -p tcp --dport 22 -m state --state NEW -m recent --update --seconds 60 --hitcount 5 -j DROP"
                ],
                "why": "Slows down brute force significantly"
            }
        ]
    },
    "malware": {
        "title": "Malware / Ransomware Activity",
        "description": "Attacker has executed malicious code on the system; potential data theft or encryption.",
        "how_got_in": "Exploit chain or phishing leading to payload execution.",
        "severity": "CRITICAL - Active compromise with data risk",
        "actions": [
            {
                "priority": "HIGH",
                "title": "Isolate the system immediately",
                "description": "Disconnect from network to prevent spread.",
                "commands": [
                    "# Unplug network cable or disable network interface",
                    "ip link set eth0 down  # disable network"
                ],
                "why": "Stops malware from exfiltrating data or spreading"
            },
            {
                "priority": "HIGH",
                "title": "Kill suspicious processes",
                "description": "Terminate malware and backdoor processes.",
                "commands": [
                    "ps aux | grep suspicious_process",
                    "kill -9 <PID>"
                ],
                "why": "Stops active malware execution"
            },
            {
                "priority": "HIGH",
                "title": "Block command & control (C2) connections",
                "description": "Blacklist all outbound connections to attacker infrastructure.",
                "commands": [
                    "iptables -A OUTPUT -d attacker.ip.address -j DROP",
                    "# Use DNS sinkhole to block C2 domains"
                ],
                "why": "Severs malware communication with attacker"
            },
            {
                "priority": "HIGH",
                "title": "Restore from clean backup",
                "description": "Rebuild system from known-good backup before compromise.",
                "commands": [
                    "# Boot from backup media or snapshot",
                    "# Validate backup integrity before restore"
                ],
                "why": "Most reliable way to remove malware completely"
            },
            {
                "priority": "MEDIUM",
                "title": "Implement full-disk encryption",
                "description": "Encrypt all data at rest to protect against ransomware.",
                "commands": [
                    "luks-setup / with LUKS2",
                    "# Enable BitLocker on Windows"
                ],
                "why": "Prevents ransomware from encrypting data"
            },
            {
                "priority": "MEDIUM",
                "title": "Deploy EDR and forensic tools",
                "description": "Install endpoint detection and conduct forensic analysis.",
                "commands": [
                    "# Install Wazuh, Crowdstrike, or similar",
                    "# Perform memory dump and disk forensics"
                ],
                "why": "Detects future compromise and aids investigation"
            }
        ]
    },
    "unknown": {
        "title": "Unknown / Unclassified Activity",
        "description": "Attack type could not be determined from event signatures.",
        "how_got_in": "Insufficient telemetry or new attack pattern.",
        "severity": "Medium - Requires investigation",
        "actions": [
            {
                "priority": "HIGH",
                "title": "Collect detailed logs",
                "description": "Enable verbose logging for all services.",
                "commands": [
                    "# Enable auditd",
                    "auditctl -a always,exit -F arch=b64 -S execve -k exec",
                    "# Enable packet capture",
                    "tcpdump -i eth0 -w capture.pcap host <attacker_ip>"
                ],
                "why": "Gathers evidence for classification"
            },
            {
                "priority": "HIGH",
                "title": "Investigate session events",
                "description": "Review all commands and connections from the attacker.",
                "commands": [
                    "cat logs/honeypot_sessions.csv | grep <session_id>",
                    "# Review all events in session"
                ],
                "why": "May reveal attack intent"
            },
            {
                "priority": "MEDIUM",
                "title": "Submit samples to threat intelligence",
                "description": "Send payloads or observables to security research.",
                "commands": [
                    "# Upload to VirusTotal, Hybrid Analysis, or internal TI platform"
                ],
                "why": "Helps identify malware family and attack source"
            }
        ]
    }
}

def get_recommendations(attack_type):
    """Retrieve recommendations for a given attack type."""
    return ATTACK_RECOMMENDATIONS.get(attack_type, ATTACK_RECOMMENDATIONS["unknown"])

def format_action_for_display(action):
    """Format a single action for Streamlit display."""
    priority_colors = {
        "HIGH": "🔴",
        "MEDIUM": "🟡",
        "LOW": "🟢"
    }
    icon = priority_colors.get(action.get("priority", "MEDIUM"), "⚪")
    title = action.get("title", "")
    desc = action.get("description", "")
    why = action.get("why", "")
    return f"{icon} **{title}** — {desc}\n\n*Why: {why}*"
