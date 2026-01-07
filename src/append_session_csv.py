# append_session_csv.py
import os
import csv
import tempfile
from typing import Dict

def append_session_csv(session: Dict, csv_path: str, columns=None):
    """
    Append a single session (dict) to csv_path. Creates file with header if missing.
    Use this from the honeypot process each time you want to persist a session row.
    """
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    file_exists = os.path.exists(csv_path)

    if not file_exists:
        if columns is None:
            columns = list(session.keys())
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(csv_path), prefix=".tmp_honeypot_")
        try:
            with os.fdopen(fd, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=columns)
                writer.writeheader()
                writer.writerow({k: session.get(k, "") for k in columns})
            os.replace(tmp, csv_path)
        except Exception:
            try:
                os.remove(tmp)
            except Exception:
                pass
            raise
    else:
        with open(csv_path, "a", newline="", encoding="utf-8") as f:
            with open(csv_path, "r", encoding="utf-8") as h:
                header = h.readline().strip().split(",")
            writer = csv.DictWriter(f, fieldnames=header)
            writer.writerow({k: session.get(k, "") for k in header})