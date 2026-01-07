# QUICK START - Multi-VM Honeypot Pipeline

## One-Liner to Get Started

### Choose ONE:

**Option A: Docker (Recommended for Windows, 1-2 min startup)**
```powershell
cd C:\project; powershell -ExecutionPolicy Bypass .\run_docker.ps1
```

**Option B: Vagrant VMs (Full isolation, 5-10 min startup)**
```powershell
cd C:\project; powershell -ExecutionPolicy Bypass .\run_all.ps1
```

## What Happens

1. ✅ 5 honeypot instances start (ports 2222-2226 for Docker, auto-assigned for Vagrant)
2. ✅ Each writes sessions to `data/sessions/honeypotX/` (JSON + CSV)
3. ✅ Aggregator merges to `output/honeypot_sessions.csv` every 5 seconds
4. ✅ Streamlit dashboard opens at **http://localhost:8501**
5. ✅ Graphs update live as data arrives

## Test It

In another PowerShell window:
```powershell
python test_client_interactive.py
```

Outputs:
- ✓ Session files created
- ✓ CSV rows written
- ✓ Instance distribution shown

## Stop Everything

```powershell
# Kill all processes
Get-Process streamlit,python | Stop-Process -Force

# Clean up containers/VMs
docker-compose down    # (if using Docker)
# or
vagrant destroy -f     # (if using Vagrant)
```

## File Structure After Run

```
C:\project\
├── data/sessions/
│   ├── honeypot1/
│   │   ├── meta.json          (per-session metadata)
│   │   └── sessions.csv       (flat rows for analytics)
│   ├── honeypot2/
│   │   ├── meta.json
│   │   └── sessions.csv
│   └── ... (honeypot3-5)
├── output/
│   └── honeypot_sessions.csv  (AGGREGATED - dashboard reads this)
├── app_auto.py                (Streamlit dashboard)
└── logs/                       (if any errors)
```

## Data Flow in 3 Steps

```
Per-VM Honeypot          Aggregator               Dashboard
─────────────────        ──────────────           ─────────
events captured    →     merge_sessions.py   →   Streamlit
write sessions.csv       (every 5s)              (auto-refresh)
```

## Common Commands

| Task | Command |
|------|---------|
| Test connection | `python test_client.py` |
| Manual merge | `python merge_sessions.py` |
| View sessions | `dir C:\project\data\sessions` |
| Check aggregated CSV | `Get-Content C:\project\output\honeypot_sessions.csv | head -10` |
| View Docker logs | `docker-compose logs -f` |
| View Vagrant status | `vagrant status` |

## Troubleshooting

**No data appearing?**
- Check instances: `docker ps` or `vagrant status`
- Test: `python test_client_interactive.py`

**Dashboard not updating?**
- Refresh browser (F5)
- Check CSV updated: `ls -l C:\project\output\honeypot_sessions.csv`

**Out of space?**
- Delete old sessions: `rm -r C:\project\data\sessions\*`

## Resource Usage

| Setup | RAM | CPU | Time | Notes |
|-------|-----|-----|------|-------|
| Docker | ~2 GB | 2+ cores | 1-2 min | Recommended |
| Vagrant | ~12 GB | 4+ cores | 5-10 min | Full isolation |

## Next Steps

1. ✅ System is ready
2. Run tests to verify
3. Modify honeypot to integrate `save_session_data()` if needed
4. Add custom fields to session data
5. Scale to database for production

---

**Need help?** Check `MULTIVM_README.md` for full documentation.
