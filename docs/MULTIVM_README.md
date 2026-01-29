# Multi-VM Honeypot Pipeline

Automated end-to-end honeypot collection with 5 instances writing to aggregated CSV + Streamlit dashboard.

## Architecture

```
VM/Container 1: honeypot1 → data/sessions/honeypot1/sessions.csv + meta.json
VM/Container 2: honeypot2 → data/sessions/honeypot2/sessions.csv + meta.json
VM/Container 3: honeypot3 → data/sessions/honeypot3/sessions.csv + meta.json
VM/Container 4: honeypot4 → data/sessions/honeypot4/sessions.csv + meta.json
VM/Container 5: honeypot5 → data/sessions/honeypot5/sessions.csv + meta.json
                                            ↓
                         merge_sessions.py (every 5s)
                                            ↓
                        output/honeypot_sessions.csv
                                            ↓
                      app_auto.py (Streamlit Dashboard)
                         http://localhost:8501
```

## Option 1: Vagrant VMs (Full Isolation, Heavier)

### Prerequisites
- Vagrant installed
- VirtualBox installed
- ~12 GB RAM minimum
- ~50 GB disk space for 5 VMs

### Run
```powershell
cd C:\project
powershell -ExecutionPolicy Bypass .\run_all.ps1
```

This will:
1. Create 5 Ubuntu VMs (honeypot1..honeypot5)
2. Provision each with venv and dependencies
3. Start honeypot instances in detached screen sessions
4. Start CSV aggregator loop
5. Launch Streamlit dashboard

### First run takes 5-10 minutes for VM provisioning

## Option 2: Docker Containers (Lightweight, Faster)

### Prerequisites
- Docker Desktop installed
- ~4 GB RAM sufficient
- Works on Windows/Mac/Linux

### Run
```powershell
cd C:\project
powershell -ExecutionPolicy Bypass .\run_docker.ps1
```

This will:
1. Build/pull Ubuntu image
2. Start 5 honeypot containers
3. Start CSV aggregator loop
4. Launch Streamlit dashboard

### First run takes 1-2 minutes

## Files Created

| File | Purpose |
|------|---------|
| `Vagrantfile` | VirtualBox VM definitions |
| `vagrant/provision_honeypot.sh` | Per-VM provisioning script |
| `vagrant/run_merge_loop.sh` | Aggregator loop for Unix hosts |
| `docker-compose.yml` | Docker container definitions |
| `run_all.ps1` | Windows launcher for Vagrant |
| `run_docker.ps1` | Windows launcher for Docker |
| `merge_sessions.py` | CSV aggregator |
| `append_session_csv.py` | Safe per-VM CSV writer |
| `test_client_interactive.py` | Enhanced test client |

## Data Flow

### Per-VM (Vagrant or Docker)
1. Client connects to honeypot on port 2222 (+ offset per container)
2. Session created with unique session_id
3. Events captured and structured
4. Session data saved as:
   - `meta.json`: Full session metadata (rich forensics)
   - `sessions.csv`: Flat row for analytics

### Host Aggregator
1. `merge_sessions.py` runs every 5 seconds
2. Scans `data/sessions/*/sessions.csv` and `*/meta.json`
3. Merges all rows into `output/honeypot_sessions.csv`
4. Deduplicates by session_id (keeps latest)

### Streamlit Dashboard
1. Watches `output/honeypot_sessions.csv` for mtime changes
2. Auto-reloads on updates
3. Graphs aggregate data across all instances

## Testing

### Test single honeypot connection
```powershell
python test_client.py
```

### Test multi-VM verification
```powershell
python test_client_interactive.py
```

Outputs:
- Session file verification (meta.json, sessions.csv)
- CSV row counts
- Instance distribution

### Manual aggregation
```powershell
python merge_sessions.py
```

Outputs merged CSV and prints summary.

## Monitoring

### Check running instances
```powershell
# Vagrant
vagrant status

# Docker
docker ps
```

### View logs
```powershell
# Vagrant (SSH into VM)
vagrant ssh honeypot1
sudo screen -r honeypot_honeypot1

# Docker (follow logs)
docker-compose logs -f honeypot1
```

### Check data accumulation
```powershell
# Sessions directory
ls C:\project\data\sessions\

# Per-VM CSV
Get-Content C:\project\data\sessions\honeypot1\sessions.csv | measure -Line

# Aggregated CSV
Get-Content C:\project\output\honeypot_sessions.csv | measure -Line
```

## Stopping

### Graceful shutdown
```powershell
# Vagrant
vagrant destroy -f

# Docker
docker-compose down
```

### Kill Streamlit
```powershell
Get-Process streamlit | Stop-Process -Force
```

### Kill aggregator
```powershell
Get-Process python | Where-Object {$_.CommandLine -like "*merge_sessions*"} | Stop-Process -Force
```

## Troubleshooting

### No sessions appearing
- Check honeypot is running: `docker ps` or `vagrant status`
- Check logs: `docker-compose logs honeypot1`
- Test manually: `python test_client.py`

### CSV not aggregating
- Run manually: `python merge_sessions.py`
- Check permissions on `output/` directory
- Check for Python errors: `python merge_sessions.py 2>&1`

### Streamlit not auto-updating
- Open browser refresh (F5)
- Check CSV mtime: `stat output/honeypot_sessions.csv`
- Restart aggregator loop

### Out of disk space
- Clean old sessions: `rm -r data/sessions/honeypot*/` (be careful!)
- Delete aggregated CSV: `rm output/honeypot_sessions.csv`
- Restart pipeline

## Performance Notes

- **Vagrant**: Each VM uses 1 CPU + 1.8GB RAM
- **Docker**: Containers share OS kernel, use ~300MB each
- **Aggregation**: Fast on <10k rows, consider partitioning if larger
- **Streamlit**: Reloads entire page on CSV change (acceptable for demos)

## Customization

### Change number of instances
Edit `Vagrantfile` line 20 and `docker-compose.yml` services to add/remove honeypot#

### Change CSV merge interval
Edit `run_all.ps1` and `run_docker.ps1`: change `Start-Sleep -Seconds 5`

### Change honeypot port
Edit `vagrant/provision_honeypot.sh` and `docker-compose.yml` ports section

### Add custom data columns
Edit `save_session_data()` in `src/evidence_store.py` to include more fields

## Next Steps

1. **Integration**: Modify your honeypot entrypoint to call `save_session_data()` after each session
2. **Scaling**: Switch to database (PostgreSQL) for >100k sessions
3. **Analytics**: Add ML pipeline on `output/honeypot_sessions.csv`
4. **Alerting**: Add real-time notifications on suspicious patterns
