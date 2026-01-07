import pandas as pd

df = pd.read_csv('output/honeypot_sessions.csv')

def infer_attack_type_from_events(ev):
    if pd.isna(ev): return "unknown"
    s = str(ev).lower()
    if any(k in s for k in ("wget ", "curl ", "download ", "exploit", "payload", "meterpreter", "reverse")):
        return "exploit"
    if any(k in s for k in ("nmap", "masscan", "scan", "port scan", "syn scan", "sweep")):
        return "recon"
    if any(k in s for k in ("password", "login", "ssh", "bruteforce", "failed password", "authentication")):
        return "bruteforce"
    if any(k in s for k in ("uname", "id ", "whoami", "ls ", "pwd", "hostname", "cat /etc")):
        return "recon"
    if any(k in s for k in ("ransom", "encrypt", "encrypting", "locky", "cerber")):
        return "malware"
    return "unknown"

df['attack_type'] = df['events'].apply(infer_attack_type_from_events)

print("Attack Type Distribution:")
print(df['attack_type'].value_counts())
print("\nSample attack types:")
for idx in range(min(3, len(df))):
    print(f"\nSession {idx}:")
    print(f"  attack_type: {df['attack_type'].iloc[idx]}")
    events_str = df['events'].iloc[idx][:200]
    print(f"  events (first 200 chars): {events_str}")
