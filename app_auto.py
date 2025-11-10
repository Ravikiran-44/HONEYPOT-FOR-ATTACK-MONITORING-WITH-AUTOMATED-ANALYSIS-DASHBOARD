# app_auto.py — stable honeypot dashboard (watcher + normalizer)
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import time, re

st.set_page_config(layout="wide", page_title="Honeypot Analytics", initial_sidebar_state="expanded")

OUTPUT_CSV = Path("output/honeypot_sessions.csv")
POLL_SECS = 3.0

# ---------------------
# Simple watcher: force rerun when output CSV mtime changes
# ---------------------
if "watcher_mtime" not in st.session_state:
    st.session_state["watcher_mtime"] = None

def check_reload():
    if OUTPUT_CSV.exists():
        m = OUTPUT_CSV.stat().st_mtime
        prev = st.session_state.get("watcher_mtime")
        if prev is None:
            st.session_state["watcher_mtime"] = m
        elif m != prev:
            st.session_state["watcher_mtime"] = m
            try:
                if hasattr(st, "experimental_rerun"):
                    st.experimental_rerun()
            except Exception:
                st.experimental_set_query_params(_t=str(time.time()))

check_reload()

# ---------------------
# Normalizer
# ---------------------
def normalize_honeypot_data(df):
    if df is None:
        return df
    df = df.copy()
    df.rename(columns={c: c.strip() for c in df.columns}, inplace=True)
    lowermap = {c.lower(): c for c in df.columns}
    rename_map = {}
    for cand in ("src","src_ip","source_ip","saddr"):
        if cand in lowermap:
            rename_map[lowermap[cand]] = "src_ip"
            break
    for cand in ("dst","dst_ip","destination_ip","daddr"):
        if cand in lowermap:
            rename_map[lowermap[cand]] = "dst_ip"
            break
    for cand in ("dst_port","dpt","dest_port","port","dstport"):
        if cand in lowermap:
            rename_map[lowermap[cand]] = "dst_port"
            break
    for cand in ("timestamp","time","datetime"):
        if cand in lowermap:
            rename_map[lowermap[cand]] = "timestamp"
            break
    if rename_map:
        df = df.rename(columns=rename_map)

    port_re = re.compile(r"(\d{1,5})")
    def extract_port(v):
        if pd.isna(v): 
            return None
        if isinstance(v, (int, float)) and not np.isnan(v): 
            return int(v)
        s = str(v)
        if ":" in s:
            tail = s.rsplit(":", 1)[-1]
            if tail.isdigit(): 
                return int(tail)
        if "/" in s:
            tail = s.rsplit("/", 1)[-1]
            if tail.isdigit(): 
                return int(tail)
        if s.isdigit(): 
            return int(s)
        m = port_re.search(s)
        if m:
            p = int(m.group(1))
            if 0 < p < 65536: 
                return p
        return None

    if "dst_port" in df.columns:
        df["dst_port"] = df["dst_port"].apply(extract_port)
        df["dst_port"] = pd.to_numeric(df["dst_port"], errors="coerce").astype("Int64")
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", infer_datetime_format=True)
    return df

# ---------------------
# Load data
# ---------------------
use_demo = st.sidebar.checkbox("Use demo data", value=False)
uploaded = st.sidebar.file_uploader("Upload honeypot CSV", type=["csv"])

df = None
if uploaded is not None:
    try:
        df = pd.read_csv(uploaded)
        df = normalize_honeypot_data(df)
        st.sidebar.success(f"Loaded uploaded CSV ({len(df)} rows)")
    except Exception as e:
        st.sidebar.error("Failed to load uploaded file: " + str(e))

if df is None and OUTPUT_CSV.exists():
    try:
        df = pd.read_csv(OUTPUT_CSV)
        df = normalize_honeypot_data(df)
        st.sidebar.info(f"Loaded {OUTPUT_CSV} ({len(df)} rows)")
    except Exception as e:
        st.sidebar.error("Failed to read output CSV: " + str(e))

if df is None and use_demo:
    rows = []
    for i in range(60):
        rows.append({"session_id":f"demo{i}", "timestamp":pd.Timestamp.now()-pd.Timedelta(minutes=i*7),
                     "src_ip":f"10.9.{i%255}.{(i*3)%255}", "dst_port": int(np.random.choice([22,80,443,8080,23]))})
    df = pd.DataFrame(rows)
    df = normalize_honeypot_data(df)
    st.sidebar.info("Using demo dataset")

if df is None:
    st.warning("No dataset loaded. Upload a CSV, enable demo, or create output/honeypot_sessions.csv.")
    st.stop()

# Sidebar debug
st.sidebar.markdown("**Dataset**")
st.sidebar.write("Rows:", len(df))
st.sidebar.write("Columns:", list(df.columns))
if "dst_port" in df.columns:
    st.sidebar.write("dst_port sample:", df["dst_port"].dropna().astype(str).unique()[:8].tolist())

# UI
st.title(" Honeypot Analytics Dashboard")
st.markdown("Dataset overview")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total sessions", f"{len(df):,}")
c2.metric("Columns", f"{len(df.columns)}")
c3.metric("Unique sources", f"{df['src_ip'].nunique() if 'src_ip' in df.columns else 0:,}")
c4.metric("Rows", f"{len(df):,}")

st.markdown("### First rows")
st.dataframe(df.head(20), use_container_width=True)

st.markdown("### Attack analysis")
tabs = st.tabs(["Attack Types","Ports","Timeline","Geography","Raw Data"])
with tabs[0]:
    if "attack_type" not in df.columns:
        st.info("No attack_type column found")
    else:
        s = df['attack_type'].fillna("unknown").value_counts().reset_index()
        s.columns = ["attack_type","count"]
        st.plotly_chart(px.bar(s, x="attack_type", y="count", title="Attack Types"), use_container_width=True)
with tabs[1]:
    if "dst_port" not in df.columns or df["dst_port"].dropna().empty:
        st.info("No destination port data available")
    else:
        ports = df["dst_port"].dropna().astype(int).value_counts().reset_index().rename(columns={"index":"port","dst_port":"count"})
        st.plotly_chart(px.bar(ports, x="port", y="count", title="Top Destination Ports"), use_container_width=True)
with tabs[2]:
    if "timestamp" not in df.columns or df["timestamp"].isna().all():
        st.info("No timestamps")
    else:
        ts = df.set_index("timestamp").resample("H").size().reset_index(name="count")
        st.plotly_chart(px.line(ts, x="timestamp", y="count", title="Sessions over time"), use_container_width=True)
with tabs[3]:
    if "src_country" in df.columns:
        s = df['src_country'].fillna("UNKNOWN").value_counts().reset_index()
        s.columns = ["country","count"]
        st.plotly_chart(px.bar(s, x="country", y="count", title="Top source countries"), use_container_width=True)
    else:
        st.info("No geo data")
with tabs[4]:
    st.dataframe(df.head(500), use_container_width=True)

st.markdown("---")
st.write("Tip: For live data, ensure per-VM instances write into 'data/sessions/<inst>/' and run the aggregator to produce 'output/honeypot_sessions.csv'. The dashboard watches that CSV and reloads automatically.")
