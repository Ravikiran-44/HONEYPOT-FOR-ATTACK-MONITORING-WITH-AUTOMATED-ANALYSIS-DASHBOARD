# src/evidence_store.py
from pathlib import Path
import hashlib, time

MAX_PAYLOAD_BYTES = 5 * 1024 * 1024  # 5 MB

def sha256_bytes(b: bytes) -> str:
    h = hashlib.sha256()
    h.update(b)
    return h.hexdigest()


def save_payload_to_session_dir(sdir, data: bytes, name=None):
    """Save payload bytes into the session dir and return rich metadata dict.

    Truncates to MAX_PAYLOAD_BYTES to avoid huge files. Returns metadata:
    {file, path, sha256, size, saved_ts}
    """
    sdir = Path(sdir)
    sdir.mkdir(parents=True, exist_ok=True)
    if name is None:
        name = f"payload_{int(time.time())}.bin"
    content = data[:MAX_PAYLOAD_BYTES] if data is not None else b''
    p = sdir / name
    with open(p, "wb") as f:
        f.write(content)
    sha = sha256_bytes(content)
    meta = {
        "file": name,
        "path": str(p.resolve()),
        "sha256": sha,
        "size": len(content),
        "saved_ts": time.time()
    }
    return meta


def save_payload(sdir, data, name="payload.bin"):
    """Backward-compatible shim: saves payload and returns the file path string.

    Prefer using save_payload_to_session_dir for metadata.
    """
    meta = save_payload_to_session_dir(sdir, data, name=name)
    return meta["path"]
