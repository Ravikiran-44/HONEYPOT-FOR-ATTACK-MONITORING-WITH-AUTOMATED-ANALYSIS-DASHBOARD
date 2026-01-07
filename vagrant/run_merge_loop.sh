#!/bin/bash
# run_merge_loop.sh - run aggregator every N seconds (host)
ROOT_DIR="$(cd "$(dirname "$0")"/.. && pwd)"
cd "${ROOT_DIR}"
while true; do
  python merge_sessions.py
  sleep 5
done