# src/high_engagement.py (patched to ignore socket.timeout)
import time, random, hashlib, errno, socket
from pathlib import Path
from .session_manager import append_event
from .evidence_store import save_payload

MAX_SESSION_SECONDS = 60 * 20
INACTIVITY_TIMEOUT = 60 * 3
MAX_PAYLOAD_BYTES = 5 * 1024 * 1024

FAKE_FILES = {
    "/etc/passwd": "root:x:0:0:root:/root:/bin/bash\nadmin:x:1000:1000:Admin:/home/admin:/bin/bash\n",
    "/home/admin/.env": "DB_USER=admin\nDB_PASS=Admin123!\nAPI_KEY=abcd-efgh-1234\n",
    "/var/www/html/index.html": "<html><body>ACME Corp Webroot</body></html>\n",
    "/root/notes.txt": "Backup creds: backup_user:Backup#2025\n",
    "/root/db_dump.sql": "-- fake db dump\nCREATE TABLE users (id INT, name TEXT);\nINSERT INTO users VALUES (1,'alice');\n"
}

def now_ts():
    return time.time()

def chunked_send(conn, text, delay_min=0.02, delay_max=0.12, chunk_size=240):
    if not text:
        return True
    try:
        b = text.encode(errors="ignore")
        for i in range(0, len(b), chunk_size):
            conn.sendall(b[i:i+chunk_size])
            time.sleep(random.uniform(delay_min, delay_max))
        return True
    except (ConnectionResetError, BrokenPipeError, ConnectionAbortedError):
        return False
    except OSError as oe:
        if getattr(oe, "winerror", None) == 10053 or getattr(oe, "errno", None) == errno.ECONNABORTED:
            return False
        raise

def compute_sha256_bytes(b):
    h = hashlib.sha256()
    h.update(b)
    return h.hexdigest()

def save_placeholder_payload(sdir, source_hint, data_bytes):
    if data_bytes is None:
        content = source_hint.encode(errors="ignore")
    else:
        content = data_bytes[:MAX_PAYLOAD_BYTES]
    filename = f"payload_{int(time.time())}.bin"
    p = save_payload(sdir, content, name=filename)
    sha256 = compute_sha256_bytes(content)
    meta = {"file": filename, "path": str(p), "sha256": sha256, "note": source_hint}
    return meta

def handle_ls(conn, sdir, cwd, args):
    lines = []
    lines.append("drwxr-xr-x 3 root root 4096 Nov  1 10:01 .")
    for path in FAKE_FILES:
        if path.startswith(cwd):
            name = path[len(cwd):].lstrip("/")
            if "/" not in name and name:
                size = len(FAKE_FILES[path])
                lines.append(f"-rw-r--r-- 1 root root {size} Nov  1 10:01 {name}")
    if not lines:
        lines = ["total 0"]
    return chunked_send(conn, "\n".join(lines) + "\n")

def handle_cat(conn, sdir, target):
    content = FAKE_FILES.get(target)
    if content is None:
        return chunked_send(conn, f"cat: {target}: No such file or directory\n")
    return chunked_send(conn, content)

def handle_uname(conn):
    return chunked_send(conn, "Linux fakehost 4.15.0-99-generic #100~16.04.1 SMP Tue Nov 2 12:34:56 UTC 2021 x86_64 GNU/Linux\n")

def handle_whoami(conn):
    return chunked_send(conn, "root\n")

def handle_ps(conn):
    out = ("USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND\n"
           "root         1  0.0  0.1  22568  4100 ?        Ss   Nov01   0:01 /sbin/init\n"
           "root      2345  0.1  0.3 123456 10344 ?        Ssl  Nov01   0:12 /usr/bin/fake-service\n")
    return chunked_send(conn, out)

def handle_download(conn, sdir, command_text):
    parts = command_text.split()
    url = None
    for p in parts:
        if p.startswith("http://") or p.startswith("https://"):
            url = p
            break
    # log detection immediately (guarantee)
    append_event(sdir, {"ts": now_ts(), "text": f"[PAYLOAD_DETECTED]={url}"})
    meta = save_placeholder_payload(sdir, source_hint=f"download:{url}", data_bytes=(url or "").encode())
    append_event(sdir, {"ts": now_ts(), "text": f"[PAYLOAD_SAVED]={meta}"})
    return chunked_send(conn, f"Attempted download from {url} (placeholder saved)\n")

def start_fake_shell(conn, sdir):
    start_time = now_ts()
    append_event(sdir, {"ts": start_time, "text": "[HIGH_ENGAGEMENT]=START"})
    cwd = "/root"
    last_activity = now_ts()

    # send welcome and prompt
    try:
        if not chunked_send(conn, "Welcome to Ubuntu 16.04.7 LTS (GNU/Linux 4.15.0-99)\n"):
            append_event(sdir, {"ts": now_ts(), "text": "[HIGH_ENGAGEMENT]=CLIENT_CLOSED_BEFORE_START"})
            append_event(sdir, {"ts": now_ts(), "text": "[HIGH_ENGAGEMENT]=END"})
            return
        if not chunked_send(conn, "root@fakehost:~# "):
            append_event(sdir, {"ts": now_ts(), "text": "[HIGH_ENGAGEMENT]=CLIENT_CLOSED_BEFORE_PROMPT"})
            append_event(sdir, {"ts": now_ts(), "text": "[HIGH_ENGAGEMENT]=END"})
            return
    except Exception as e:
        append_event(sdir, {"ts": now_ts(), "text": f"[HIGH_ENGAGEMENT_ERROR_INIT]={e}"})
        append_event(sdir, {"ts": now_ts(), "text": "[HIGH_ENGAGEMENT]=END"})
        return

    buffer = b""
    conn.settimeout(1.0)

    while True:
        # enforce max session time
        if now_ts() - start_time > MAX_SESSION_SECONDS:
            append_event(sdir, {"ts": now_ts(), "text": "[HIGH_ENGAGEMENT]=TIMEOUT_CLOSING"})
            break
        # enforce inactivity timeout
        if now_ts() - last_activity > INACTIVITY_TIMEOUT:
            append_event(sdir, {"ts": now_ts(), "text": "[HIGH_ENGAGEMENT]=INACTIVITY_CLOSING"})
            break

        try:
            chunk = conn.recv(4096)
            if not chunk:
                # remote closed connection
                break
            buffer += chunk
            if b"\n" in buffer:
                parts = buffer.split(b"\n")
                for cmd_bytes in parts[:-1]:
                    cmd_text = cmd_bytes.decode(errors="ignore").strip()
                    last_activity = now_ts()
                    append_event(sdir, {"ts": now_ts(), "text": f"ATTACKER_CMD: {cmd_text}"})

                    lower = cmd_text.lower()
                    ok = True
                    if lower.startswith("ls"):
                        ok = handle_ls(conn, sdir, cwd, cmd_text)
                    elif lower.startswith("cat "):
                        target = cmd_text[4:].strip()
                        if not target.startswith("/"):
                            target = cwd.rstrip("/") + "/" + target
                        ok = handle_cat(conn, sdir, target)
                    elif lower.startswith("uname"):
                        ok = handle_uname(conn)
                    elif lower.startswith("whoami") or lower.startswith("id"):
                        ok = handle_whoami(conn)
                    elif "ps aux" in lower or lower.startswith("ps"):
                        ok = handle_ps(conn)
                    elif "wget" in lower or "curl" in lower:
                        ok = handle_download(conn, sdir, cmd_text)
                    elif lower.startswith("exit") or lower.startswith("logout"):
                        chunked_send(conn, "logout\n")
                        append_event(sdir, {"ts": now_ts(), "text": "[HIGH_ENGAGEMENT]=ATTACKER_EXIT"})
                        return
                    else:
                        ok = chunked_send(conn, f"-bash: {cmd_text}: command not found\n")

                    if not ok:
                        append_event(sdir, {"ts": now_ts(), "text": "[HIGH_ENGAGEMENT]=CLIENT_DISCONNECTED"})
                        append_event(sdir, {"ts": now_ts(), "text": "[HIGH_ENGAGEMENT]=END"})
                        return

                    time.sleep(random.uniform(0.2, 0.7))
                    if not chunked_send(conn, "root@fakehost:~# "):
                        append_event(sdir, {"ts": now_ts(), "text": "[HIGH_ENGAGEMENT]=CLIENT_DISCONNECTED_AFTER_PROMPT"})
                        append_event(sdir, {"ts": now_ts(), "text": "[HIGH_ENGAGEMENT]=END"})
                        return

                buffer = parts[-1]
        except socket.timeout:
            # No data received this cycle — continue waiting
            continue
        except ConnectionResetError:
            break
        except OSError as oe:
            if getattr(oe, "winerror", None) == 10053 or getattr(oe, "errno", None) == errno.ECONNABORTED:
                break
            append_event(sdir, {"ts": now_ts(), "text": f"[HIGH_ENGAGEMENT_ERROR]={oe}"})
            break
        except Exception as e:
            append_event(sdir, {"ts": now_ts(), "text": f"[HIGH_ENGAGEMENT_ERROR]={e}"})
            break

    append_event(sdir, {"ts": now_ts(), "text": "[HIGH_ENGAGEMENT]=END"})
    try:
        chunked_send(conn, "\nConnection closed by remote host.\n")
    except Exception:
        pass
