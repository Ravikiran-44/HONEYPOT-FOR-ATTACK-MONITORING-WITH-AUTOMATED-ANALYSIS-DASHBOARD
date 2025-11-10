# src/orchestrator.py
# Local-only honeypot orchestrator. Overwrite your existing file with this.
# Listens on 127.0.0.1:2222, records sessions under data/sessions,
# classifies events, captures payload placeholders, and enters high-engagement mode.

import socket
import threading
import time
import json
import re
from pathlib import Path

from .session_manager import new_session, append_event, close_session
from .interaction_engine import banner_for, fake_response_for
from .feature_extractor import extract_features
from .classifier import classify
from .policy_engine import decide_engagement
from .evidence_store import save_payload_to_session_dir  # saver

HOST, PORT = "127.0.0.1", 2222
URL_RE = re.compile(r'(https?://[^\s]+)', re.IGNORECASE)


def extract_url(text):
    m = URL_RE.search(text)
    return m.group(1) if m else None


def append_struct_event(sdir, evdict):
    """
    Append a structured event to session meta.
    We store it as a special text event with a JSON payload for compatibility:
       {"ts": timestamp, "text": "[STRUCT_EVENT]={...json...}"}
    """
    if "ts" not in evdict:
        evdict["ts"] = time.time()
    # ensure values are JSON-serializable
    try:
        json.dumps(evdict)
    except Exception:
        # fallback: convert problematic values to string
        for k, v in list(evdict.items()):
            try:
                json.dumps(v)
            except Exception:
                evdict[k] = str(v)
    append_event(sdir, {"ts": evdict["ts"], "text": f"[STRUCT_EVENT]={json.dumps(evdict)}"})


class Orchestrator:
    def __init__(self, host=HOST, port=PORT):
        self.host = host
        self.port = port
        self._stop = threading.Event()

    def initialize_components(self):
        # Initialize or warm up any components here if needed
        print("[INFO] Orchestrator components initialized.")

    def handle_client(self, conn, addr):
        sid, sdir = new_session(addr[0], addr[1])
        print(f"[INFO] Session {sid} started for {addr[0]}:{addr[1]}")
        try:
            # send service banner (may fail if client disconnects quickly)
            try:
                conn.sendall(banner_for("ssh").encode())
            except Exception:
                pass

            buffer = b""
            conn.settimeout(1.0)

            while True:
                try:
                    chunk = conn.recv(4096)
                except OSError:
                    # socket error or timeout; break if connection dead
                    break
                if not chunk:
                    break
                buffer += chunk
                # Wait until we have a newline to process a command
                if b"\n" not in buffer:
                    continue

                parts = buffer.split(b"\n")
                # process all complete lines
                for raw_cmd in parts[:-1]:
                    try:
                        text = raw_cmd.decode(errors="ignore").strip()
                    except Exception:
                        text = ""
                    # log raw input
                    append_event(sdir, {"ts": time.time(), "text": text})

                    # read current meta to extract features
                    try:
                        with open(Path(sdir) / "meta.json", "r", encoding="utf-8") as f:
                            meta = json.load(f)
                    except Exception:
                        meta = {"events": []}

                    features = extract_features(meta.get("events", []))
                    label, conf = classify(features)
                    eng = decide_engagement(label, conf)

                    # Create structured classification event
                    low = text.lower()
                    if "wget " in low or "curl " in low:
                        vector = "download"
                    elif "ssh " in low or "scp " in low:
                        vector = "ssh"
                    else:
                        vector = "command"

                    struct_class = {
                        "type": "classification",
                        "label": label,
                        "confidence": float(conf),
                        "vector": vector,
                        "src_ip": addr[0],
                        "src_port": addr[1],
                        "engagement": eng,
                        "summary": f"{label.upper()} ({vector}) — conf {float(conf):.2f}, ENG={eng}"
                    }
                    append_struct_event(sdir, struct_class)

                    # keep legacy class event for compatibility
                    append_event(sdir, {"ts": time.time(), "text": f"[CLASS]={label}|{conf}|ENG={eng}"})

                    # detect download attempts (wget/curl heuristics)
                    forced_handoff = ("wget " in low) or ("curl " in low)

                    if forced_handoff:
                        url = extract_url(text) or text.strip()
                        try:
                            payload_bytes = (url or "").encode("utf-8", errors="ignore")
                            meta_payload = save_payload_to_session_dir(
                                sdir, payload_bytes, name=f"payload_handoff_{int(time.time())}.bin"
                            )
                            # structured payload event
                            struct_payload = {
                                "type": "payload_saved",
                                "file": meta_payload.get("file"),
                                "path": meta_payload.get("path"),
                                "sha256": meta_payload.get("sha256"),
                                "size": meta_payload.get("size"),
                                "saved_ts": meta_payload.get("saved_ts"),
                                "src_ip": addr[0],
                                "src_port": addr[1],
                                "summary": "Payload saved from suspected download"
                            }
                            append_struct_event(sdir, struct_payload)
                            # legacy payload event
                            append_event(sdir, {"ts": time.time(), "text": f"[PAYLOAD_SAVED]={meta_payload}"})
                        except Exception as e:
                            append_event(sdir, {"ts": time.time(), "text": f"[ERROR]=PAYLOAD_SAVE_FAILED|{e}"})

                    # If high engagement is required or forced by download, hand off to high engagement
                    if eng == "HIGH" or forced_handoff:
                        append_event(sdir, {"ts": time.time(), "text": "[ACTION]=HANDOFF_TO_HIGH_ENGAGEMENT"})
                        try:
                            # high_engagement.start_fake_shell should take (conn, sdir) and manage the connection until done
                            from .high_engagement import start_fake_shell
                            start_fake_shell(conn, sdir)
                        except Exception as he:
                            append_event(sdir, {"ts": time.time(), "text": f"[ERROR]=HIGH_ENGAGEMENT_FAILED|{he}"})
                        # After high engagement we break the main loop — connection handled by high_engagement
                        break
                    else:
                        # send regular fake response
                        resp = fake_response_for(text + "\n")
                        try:
                            conn.sendall(resp.encode())
                        except Exception:
                            # if send fails, stop processing
                            break

                # keep the remaining partial line (if any) in buffer
                buffer = parts[-1]

        except Exception as e:
            append_event(sdir, {"ts": time.time(), "text": f"[ERROR]={e}"})
        finally:
            try:
                close_session(sdir)
            except Exception:
                pass
            try:
                conn.close()
            except Exception:
                pass
            print(f"[INFO] Session {sid} closed.")

    def start(self):
        self.initialize_components()
        print(f"[INFO] Starting honeypot on {self.host}:{self.port}")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.host, self.port))
            s.listen(5)
            try:
                while not self._stop.is_set():
                    conn, addr = s.accept()
                    threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()
            except KeyboardInterrupt:
                print("[INFO] Stopping server...")
                self._stop.set()
