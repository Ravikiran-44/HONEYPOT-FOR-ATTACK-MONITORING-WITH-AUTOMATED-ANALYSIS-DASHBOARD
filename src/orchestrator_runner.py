# src/orchestrator_runner.py
"""Module runner for the honeypot orchestrator."""
from .orchestrator import Orchestrator
import os
import sys

def main():
    host = os.environ.get("HONEYPOT_HOST", "127.0.0.1")
    port = int(os.environ.get("HONEYPOT_PORT", "2222"))
    orch = Orchestrator(host=host, port=port)
    orch.start()

if __name__ == "__main__":
    main()
