# AI-Driven Autonomous Honeypot

## 🔥 EXPOSE TO INTERNET (Real Attackers) — NEW!

Your honeypot is now ready to collect attacks from **real hackers on the internet**.

### Quick Start (15 minutes)

**See:** `START_HERE.md` for the 3-step process:

1. **Configure router port forwarding** (5 min)
   - Add rule: External 2222 → Internal 192.168.56.50:2222
   - See `INTERNET_EXPOSURE_GUIDE.md` for your router model

2. **Test public exposure** (2 min)
   - Go to canyouseeme.org
   - Verify port 2222 is accessible

3. **Monitor real attacks** (automatic)
   - Real attackers arrive in 5 min to 2 hours
   - Dashboard displays real IP, country, commands, malware

### Detailed Guides

- **`START_HERE.md`** — Quick visual summary (read first!)
- **`QUICK_START_INTERNET.md`** — Quick reference card
- **`INTERNET_EXPOSURE_GUIDE.md`** — Router setup by brand (TP-Link, ASUS, Netgear, Linksys, etc.)
- **`DEPLOYMENT_STATUS.md`** — Full technical architecture and timeline
- **`get_router_ip.ps1`** — Auto-detect your router gateway
- **`monitor_attacks.ps1`** — Live attack monitoring

### What You'll Get

Each real attack appears as a new folder in `C:\project\data\sessions\`:

- Real attacker IP address
- Real geographic location (GeoIP)
- Real commands executed
- Real malware samples captured
- AI classification (recon/exploit/malware/bruteforce)
- Professional incident response playbooks
- All viewable in your Streamlit dashboard

---

## Project Layout

```
C:\project/
├── src/                              Core Python modules
├── backend/                          Backend components
├── bin/                              Launcher scripts
├── tools/                            Utilities
├── deploy/                           Deployment helpers
├── docs/                             Documentation
├── data/                             GeoIP DB + session files
├── output/                           Reports and exports
├── logs/                             Runtime logs
├── tests/                            Automated tests
│
├── START_HERE.md                     👈 READ THIS FIRST (internet exposure)
├── INTERNET_EXPOSURE_GUIDE.md        Router setup by model
├── QUICK_START_INTERNET.md           Quick reference
├── DEPLOYMENT_STATUS.md              Technical details
├── Vagrantfile                       Updated with port forwarding
├── run_all.ps1                       One-click launcher
└── README.md                         This file
```

---

## Local Development (Streamlit + Honeypot)

### Start everything:

```powershell
cd C:\project
.\run_all.ps1
```

This starts:
- Honeypot on 127.0.0.1:2222
- Streamlit dashboard on 127.0.0.1:8501

### Or use demo launcher:

```powershell
cd C:\project
.\bin\run_demo.bat
```

### Or run manually:

```powershell
cd C:\project
.\.venv\Scripts\python.exe -m streamlit run src/app_auto.py
```

---

## Expose to Internet (Real Attackers)

**See `START_HERE.md` for complete setup!**

Quick summary:
1. Configure router port forward (5 min)
2. Test with canyouseeme.org (2 min)
3. Wait for real attacks (5 min to 2 hours)

---

## Safety

✅ **Your Windows is 100% safe** because:
- Only port 2222 is exposed
- VM is network-isolated
- Attacker sees fake Ubuntu, not your system
- VM can be reset instantly: `vagrant destroy -f && vagrant up`

❌ **Never expose:**
- Port 22 (SSH)
- Port 80/443 (HTTP)
- Windows directly (bridged network)

---

## Monitoring

### Live attack monitor:
```powershell
.\monitor_attacks.ps1
```

### View latest attack:
```powershell
$latest = (Get-ChildItem C:\project\data\sessions -Directory | 
           Sort-Object CreationTime -Descending | 
           Select-Object -First 1).FullName
Get-Content "$latest\meta.json" | ConvertFrom-Json | Format-List
```

### Count total attacks:
```powershell
(Get-ChildItem C:\project\data\sessions -Directory).Count
```

---

## VM Management

### SSH into VM:
```powershell
vagrant ssh
```

### Restart VM:
```powershell
vagrant reload
```

### Reset everything:
```powershell
vagrant destroy -f
vagrant up
```

---

## Dashboard Features

Your Streamlit dashboard includes:

- **Overview**: Key metrics (attack count, countries, port distribution)
- **Attack Types**: Classification breakdown (recon, exploit, malware, bruteforce)
- **Ports**: Most attacked ports and services
- **Timeline**: Attack timeline graph
- **Geography**: GeoIP world map of attackers
- **Attack Insights**: Professional incident response playbooks with exact bash commands
- **Raw Data**: Full event logs and JSON metadata

---

## Files Created by Agent

For internet exposure setup:

- `Vagrantfile` — Updated with static IP 192.168.56.50 and port forwarding 2222→2222
- `INTERNET_EXPOSURE_GUIDE.md` — Detailed router instructions by brand
- `QUICK_START_INTERNET.md` — Quick reference card
- `DEPLOYMENT_STATUS.md` — Full technical details
- `START_HERE.md` — Visual summary (read first!)
- `get_router_ip.ps1` — Auto-detect router gateway IP
- `monitor_attacks.ps1` — Live attack monitoring script

---

## Next Steps

**TODAY:**
1. Read `START_HERE.md`
2. Configure router port forwarding
3. Test with canyouseeme.org

**WITHIN HOURS:**
- Real attacks will arrive
- Dashboard will show real data

**OPTIONAL:**
- Ask me about Telegram alerts
- Ask me about more honeypots (HTTP, Telnet, DNS)
- Ask me about fake CCTV/IoT device identities

---

## Support

- Detailed router setup: `INTERNET_EXPOSURE_GUIDE.md` (by brand)
- Quick reference: `QUICK_START_INTERNET.md`
- Technical details: `DEPLOYMENT_STATUS.md`
- Monitor attacks: `.\monitor_attacks.ps1`

---

**Your honeypot is ready. Go configure your router!** 🔥

