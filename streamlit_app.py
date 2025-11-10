import streamlit as st
import pathlib, json, time
from datetime import datetime

DATA = pathlib.Path("data/sessions")

st.set_page_config(page_title="Honeypot Dashboard", layout="wide")

def human_time(ts):
    try:
        return datetime.fromtimestamp(float(ts)).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(ts)

st.title("AI Honeypot — Live Dashboard")
st.caption(" Auto-refreshes every ~2s. Close tab to stop.")

# Simple JS auto-refresh (works reliably across Streamlit versions)
refresh_interval = 2
st.markdown(f"""
<script>
setTimeout(()=>window.location.reload(), {refresh_interval*1000});
</script>
""", unsafe_allow_html=True)

# Sidebar: session selection
st.sidebar.header("Controls")
all_sessions = []
if DATA.exists() and any(DATA.iterdir()):
    all_sessions = sorted(DATA.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
else:
    st.sidebar.write("No sessions yet (run the honeypot & test client).")

selected = st.sidebar.selectbox("Pick session", ["(latest)"] + [p.name for p in all_sessions])

if selected == "(latest)":
    session_path = all_sessions[0] if all_sessions else None
else:
    session_path = DATA / selected

if not session_path:
    st.info("No session available. Start honeypot and run test client to generate a session.")
    st.stop()

meta_file = session_path / "meta.json"
if not meta_file.exists():
    st.error(f"meta.json not found for session: {session_path}")
    st.stop()

meta = json.loads(meta_file.read_text(encoding="utf-8"))

col1, col2, col3, col4 = st.columns([1,1,1,2])
col1.metric("Session ID", meta.get("session_id", "N/A"))
col2.metric("Source", f"{meta.get('src_ip')}:{meta.get('src_port')}")
col3.metric("Events", len(meta.get("events", [])))
col4.metric("Recorded", meta.get("end_time", "running"))

left, right = st.columns([2.5,1.5])
with left:
    st.subheader("Event timeline")
    for ev in meta.get("events", []):
        ts = human_time(ev.get("ts", 0))
        txt = ev.get("text", "")
        if txt.startswith("[STRUCT_EVENT]"):
            try:
                payload = json.loads(txt.split("=",1)[1])
                st.markdown(f"**{ts}** — **{payload.get('type','STRUCT')}**: {payload.get('summary', payload)}")
            except Exception:
                st.markdown(f"**{ts}** — {txt}")
        elif txt.startswith("[CLASS]") or txt.startswith("[ACTION]") or txt.startswith("[PAYLOAD_SAVED]"):
            st.markdown(f"**{ts}** — {txt}")
        else:
            st.markdown(f"{ts} — {txt}")

with right:
    st.subheader("Payloads & Metadata")
    payloads = []
    for ev in meta.get("events", []):
        t = ev.get("text","")
        if t.startswith("[PAYLOAD_SAVED]") or t.startswith("[STRUCT_EVENT]") and '"payload_saved"' in t:
            payloads.append(t)
    if not payloads:
        st.info("No payloads captured in this session.")
    else:
        for idx, ptxt in enumerate(payloads):
            st.markdown(f"**Payload {idx+1}**")
            try:
                if ptxt.startswith("[STRUCT_EVENT]"):
                    raw = ptxt.split("=",1)[1]
                    pm = json.loads(raw.replace("'", '"'))
                else:
                    pm = json.loads(ptxt.split("=",1)[1].replace("'", '"'))
            except Exception:
                pm = {"path": ptxt}
            ppath = pathlib.Path(pm.get("path", ""))
            st.write("Filename:", pm.get("file", ppath.name))
            st.write("Path:", str(ppath))
            st.write("Size:", pm.get("size", "unknown"))
            st.write("SHA256:", pm.get("sha256", "unknown"))
            if ppath.exists():
                with open(ppath, "rb") as fh:
                    b = fh.read()
                st.download_button("Download payload", data=b, file_name=ppath.name, mime="application/octet-stream")
                preview = b[:1024]
                try:
                    st.code(preview.decode("utf-8", errors="replace"))
                except Exception:
                    st.write(str(preview))

st.sidebar.markdown("---")
if st.sidebar.button("Open sessions folder"):
    import os
    try:
        os.startfile(str(DATA.resolve()))
    except Exception:
        st.sidebar.write("Can't open automatically on this OS.")
