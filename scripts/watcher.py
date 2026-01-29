# watcher.py
# Simple watcher that detects new CSV files in C:\project\data and runs generate_reports.py
import time
from pathlib import Path
import subprocess

DATA_DIR = Path(r"C:\project\data")
LAST_PROCESSED = None
SLEEP = 5

if __name__ == '__main__':
    print("Starting watcher for CSV files in:", DATA_DIR)
    while True:
        try:
            files = sorted(DATA_DIR.glob("*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
            if not files:
                time.sleep(10)
                continue
            latest = files[0]
            if str(latest) != LAST_PROCESSED:
                print("Detected new CSV:", latest)
                try:
                    subprocess.run(["python", r"C:\project\generate_reports.py", "--input", str(latest), "--outdir", r"C:\project\out"], check=True)
                    print("Generation complete for", latest)
                    LAST_PROCESSED = str(latest)
                except subprocess.CalledProcessError as e:
                    print("Generator failed:", e)
            time.sleep(SLEEP)
        except KeyboardInterrupt:
            print("Watcher exiting")
            break
        except Exception as e:
            print("Watcher error:", e)
            time.sleep(5)
