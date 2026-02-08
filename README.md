# HONEYPOT FOR ATTACK MONITORING WITH AUTOMATED ANALYSIS DASHBOARD

## Overview

This project implements a production-style honeypot platform for collecting,
enriching, and analysing network attack sessions, paired with an automated
analysis dashboard. It is designed for research, monitoring, and demonstrations
of attack telemetry, providing end-to-end ingestion, enrichment (GeoIP,
timestamp normalization), automated classification of attack types, and
visualization of results.

Key goals:
- Capture real-world attacker behaviour and payloads in structured session
  records
- Enrich and normalise captured data for reliable analysis
- Provide an interactive dashboard for exploring attack trends and anomalies
- Support reproducible demos and deployment via container / Vagrant tooling

## Key Features

- Lightweight honeypot components for session capture
- Aggregation pipeline that watches CSV outputs and normalises session data
- GeoIP enrichment using MaxMind GeoLite2
- Automated attack-type inference and advisory panel
- Streamlit-based dashboard with charts, timelines and drill-downs
- Scripts for generating demo data and validating outputs

## Architecture

Major components:

- `backend/` — server and database helpers
- `scripts/` — ingestion, enrichment, aggregation, demo data generators
- `output/`, `data/` — generated session CSVs and enriched outputs
- `docs/` — deployment guides, evidence, and README templates

The pipeline follows: capture -> CSV session write -> aggregator/normalizer ->
enrichment -> dashboard visualization.

## Quick Start

Prerequisites:

- Python 3.8+ (tested on 3.10)
- `pip` and virtual environment tooling
- Optional: Docker and Vagrant for reproducible environments

Minimal local run (development):

1. Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Run the aggregator and demo server (examples):

```powershell
python scripts/run_honeypot.py
python scripts/aggregate.py
python scripts/streamlit_app.py
```

3. Open the dashboard (Streamlit) at the address printed in the console.

See `docs/QUICK_START.md` and `docs/DEPLOYMENT_READY.md` for full deployment
instructions and production recommendations.

## Demo Data and Validation

- Use `scripts/generate_demo_data.py` to create representative session data for
  demos or offline analysis.
- Use `scripts/verify_csv.py` and `scripts/verify_csv_writes.py` to validate
  CSV outputs and atomic write behaviour.

## Deployment

This repository contains Docker and Vagrant artifacts for reproducible
deployments. For production-like demonstration, follow the steps in
`docs/QUICK_START_INTERNET.md` and `docs/DEPLOYMENT_READY.md`.

## Contributing

This is a student project; contributions are welcome but please follow the
project guidelines in `docs/README.md`. When contributing:

- Open an issue describing the change
- Submit small, focused pull requests
- Keep secrets and private keys out of the repository

## License

See `LICENSE` or repository metadata for license details.

## Contact

For questions about this submission, contact the repository owner.

---
_Prepared for demonstration and evaluation: a complete honeypot pipeline with_
_automated analysis and an interactive dashboard._
