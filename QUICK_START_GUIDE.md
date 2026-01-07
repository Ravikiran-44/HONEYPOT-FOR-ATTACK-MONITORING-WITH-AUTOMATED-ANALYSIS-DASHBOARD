# 🚀 QUICK START GUIDE — Honeypot Analytics Dashboard

## Running the Complete System (No VM)

### Option 1: Batch Script (Recommended for Windows)

Double-click `run_demo.bat` in `C:\project`. This will:
1. Start the honeypot orchestrator (port 2222)
2. Start the Streamlit dashboard (port 8501)
3. Run the test client to create a sample session
4. Open dashboard at http://localhost:8501

### Option 2: Manual Terminal Steps

**Terminal 1 - Start Honeypot:**
```powershell
cd C:\project
python -m src.orchestrator_runner
```
You should see: `Starting honeypot on 127.0.0.1:2222`

**Terminal 2 - Start Dashboard:**
```powershell
cd C:\project
streamlit run app_auto.py --server.port 8501 --server.address 127.0.0.1
```
Then open: http://127.0.0.1:8501

**Terminal 3 - Generate Sample Session:**
```powershell
cd C:\project
python test_client_interactive.py
```

---

## What You'll See in the Dashboard

### 📊 Overview Metrics
- Total sessions detected
- Unique attacker IPs
- Attack types identified

### 🔍 Analysis Tabs

1. **Attack Types** — Bar chart of attack classifications (recon, exploit, malware, etc.)
2. **Ports** — Top destination ports being targeted
3. **Timeline** — Sessions over time (hourly breakdown)
4. **Geography** — Geographic origin of attacks (shows "LOCAL" for 127.0.0.1)
5. **Attack Insights** — 🎯 **DETAILED REMEDIATION STEPS**
6. **Raw Data** — Full session details

### 🛠️ Attack Insights Tab (Key Feature)

Select an attack type to view:
- **What happened:** Detailed description of the attack
- **How they got in:** Attack vector explanation
- **Severity level:** Critical/High/Medium
- **Step-by-step remediation:**
  - Priority-ranked actions
  - Bash commands to execute
  - Why each step matters
- **Download checklist** as text file for incident response

---

## Data Flow

```
Honeypot (port 2222)
  ↓ [creates sessions in data/sessions/S-xxxx/meta.json]
  ↓
Dashboard (port 8501) loads from data/sessions/
  ↓ [normalizes and extracts attack type]
  ↓
Display with clean graphs, recommendations, and exports
```

---

## Troubleshooting

### Honeypot won't start
```powershell
netstat -ano | findstr :2222
# Should show: 127.0.0.1:2222 LISTENING
```
If not listening, check that `python -m src.orchestrator_runner` is running.

### Dashboard shows "No dataset loaded"
1. Ensure honeypot is running and listening on 2222
2. Run `python test_client_interactive.py` to create a session
3. Refresh browser (Ctrl+F5)

### Test client times out
```powershell
# Test connection manually
telnet 127.0.0.1 2222
# Should get SSH banner
```
If no response, honeypot not started or bound to wrong address.

### Streamlit won't open
Ensure you're using: http://127.0.0.1:8501 (not 0.0.0.0)

---

## Key Files

| File | Purpose |
|------|---------|
| `app_auto.py` | Main Streamlit dashboard |
| `src/orchestrator.py` | Honeypot server |
| `test_client_interactive.py` | Creates sample sessions |
| `scripts/aggregate.py` | Merges session data into CSV |
| `src/attack_recommendations.py` | Remediation guides database |
| `data/sessions/S-xxxx/meta.json` | Individual session metadata |
| `output/honeypot_sessions.csv` | Aggregated canonical CSV |

---

## Advanced: Aggregating Session Data

To manually refresh the CSV from sessions directory:
```powershell
python scripts/aggregate.py
# Outputs: output/honeypot_sessions.csv
```

The dashboard auto-loads this CSV if VM sessions unavailable.

---

## Next Steps

1. ✅ Run `run_demo.bat` to start everything
2. ✅ Open http://127.0.0.1:8501
3. ✅ Click "Attack Insights" tab
4. ✅ Select an attack type and review remediation steps
5. ✅ Download checklist for incident response
6. ✅ Export session data as CSV or Excel

---

## For Presentations / Demos

- **Screenshot the Attack Insights tab** — shows professional-looking remediation steps
- **Download the checklist** — proves incident response workflow
- **Show the timeline** — demonstrates attack detection over time
- **Display raw session data** — proves authentic honeypot capture

Enjoy! 🎯
