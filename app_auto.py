# app_auto.py  — stable honeypot dashboard (watcher + normalizer)# app_auto.py  — stable honeypot dashboard (watcher + normalizer)

import streamlit as stimport streamlit as st

import pandas as pdimport pandas as pd

import numpy as npimport numpy as np

import plotly.express as pximport plotly.express as px

import plotly.graph_objects as goimport plotly.graph_objects as go

from pathlib import Pathfrom pathlib import Path

import time, reimport time, re



st.set_page_config(layout="wide", page_title="Honeypot Analytics", initial_sidebar_state="expanded")st.set_page_config(layout="wide", page_title="Honeypot Analytics", initial_sidebar_state="expanded")



OUTPUT_CSV = Path("output/honeypot_sessions.csv")OUTPUT_CSV = Path("output/honeypot_sessions.csv")

POLL_SECS = 3.0POLL_SECS = 3.0



# ---------------------# ---------------------

# Simple watcher: force rerun when output CSV mtime changes# Simple watcher: force rerun when output CSV mtime changes

# ---------------------# ---------------------

if "watcher_mtime" not in st.session_state:if "watcher_mtime" not in st.session_state:

    st.session_state["watcher_mtime"] = None    st.session_state["watcher_mtime"] = None



def check_reload():def check_reload():

    if OUTPUT_CSV.exists():    if OUTPUT_CSV.exists():

        m = OUTPUT_CSV.stat().st_mtime        m = OUTPUT_CSV.stat().st_mtime

        prev = st.session_state.get("watcher_mtime")        prev = st.session_state.get("watcher_mtime")

        if prev is None:        if prev is None:

            st.session_state["watcher_mtime"] = m            st.session_state["watcher_mtime"] = m

        elif m != prev:        elif m != prev:

            st.session_state["watcher_mtime"] = m            st.session_state["watcher_mtime"] = m

            # force reload safely            # force reload safely

            try:            try:

                if hasattr(st, "experimental_rerun"):                if hasattr(st, "experimental_rerun"):

                    st.experimental_rerun()                    st.experimental_rerun()

            except Exception:            except Exception:

                st.experimental_set_query_params(_t=str(time.time()))                st.experimental_set_query_params(_t=str(time.time()))



# call watcher at top# call watcher at top

check_reload()check_reload()



# ---------------------# ---------------------

# Normalizer# Normalizer

# ---------------------# ---------------------

def normalize_honeypot_data(df):def normalize_honeypot_data(df):

    if df is None:    if df is None:

        return df        return df

    df = df.copy()    df = df.copy()

    df.rename(columns={c: c.strip() for c in df.columns}, inplace=True)    df.rename(columns={c: c.strip() for c in df.columns}, inplace=True)

    lowermap = {c.lower(): c for c in df.columns}    lowermap = {c.lower(): c for c in df.columns}

    rename_map = {}    rename_map = {}

    for cand in ("src","src_ip","source_ip","saddr"):    for cand in ("src","src_ip","source_ip","saddr"):

        if cand in lowermap:        if cand in lowermap:

            rename_map[lowermap[cand]] = "src_ip"; break            rename_map[lowermap[cand]] = "src_ip"; break

    for cand in ("dst","dst_ip","destination_ip","daddr"):    for cand in ("dst","dst_ip","destination_ip","daddr"):

        if cand in lowermap:        if cand in lowermap:

            rename_map[lowermap[cand]] = "dst_ip"; break            rename_map[lowermap[cand]] = "dst_ip"; break

    for cand in ("dst_port","dpt","dest_port","port","dstport"):    for cand in ("dst_port","dpt","dest_port","port","dstport"):

        if cand in lowermap:        if cand in lowermap:

            rename_map[lowermap[cand]] = "dst_port"; break            rename_map[lowermap[cand]] = "dst_port"; break

    for cand in ("timestamp","time","datetime"):    for cand in ("timestamp","time","datetime"):

        if cand in lowermap:        if cand in lowermap:

            rename_map[lowermap[cand]] = "timestamp"; break            rename_map[lowermap[cand]] = "timestamp"; break

    if rename_map:    if rename_map:

        df = df.rename(columns=rename_map)        df = df.rename(columns=rename_map)



    # helper to extract port    # helper to extract port

    port_re = re.compile(r"(\d{1,5})")    port_re = re.compile(r"(\d{1,5})")

    def extract_port(v):    def extract_port(v):

        if pd.isna(v): return None        if pd.isna(v): return None

        if isinstance(v, (int, float)) and not np.isnan(v): return int(v)        if isinstance(v, (int, float)) and not np.isnan(v): return int(v)

        s = str(v)        s = str(v)

        # ip:port or tcp/2222 patterns        # ip:port or tcp/2222 patterns

        if ":" in s:        if ":" in s:

            tail = s.rsplit(":", 1)[-1]            tail = s.rsplit(":", 1)[-1]

            if tail.isdigit(): return int(tail)            if tail.isdigit(): return int(tail)

        if "/" in s:        if "/" in s:

            tail = s.rsplit("/", 1)[-1]            tail = s.rsplit("/", 1)[-1]

            if tail.isdigit(): return int(tail)            if tail.isdigit(): return int(tail)

        if s.isdigit(): return int(s)        if s.isdigit(): return int(s)

        m = port_re.search(s)        m = port_re.search(s)

        if m:        if m:

            p = int(m.group(1))            p = int(m.group(1))

            if 0 < p < 65536: return p            if 0 < p < 65536: return p

        return None        return None



    if "dst_port" in df.columns:    if "dst_port" in df.columns:

        df["dst_port"] = df["dst_port"].apply(extract_port)        df["dst_port"] = df["dst_port"].apply(extract_port)

        df["dst_port"] = pd.to_numeric(df["dst_port"], errors="coerce").astype("Int64")        df["dst_port"] = pd.to_numeric(df["dst_port"], errors="coerce").astype("Int64")

    if "timestamp" in df.columns:    if "timestamp" in df.columns:

        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", infer_datetime_format=True)        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", infer_datetime_format=True)

    return df    return df



# ---------------------# ---------------------

# Load data: always prefer OUTPUT_CSV if exists; fallback to demo only if user wants# Load data: always prefer OUTPUT_CSV if exists; fallback to demo only if user wants

# ---------------------# ---------------------

use_demo = st.sidebar.checkbox("Use demo data", value=False)use_demo = st.sidebar.checkbox("Use demo data", value=False)

uploaded = st.sidebar.file_uploader("Upload honeypot CSV", type=["csv"])uploaded = st.sidebar.file_uploader("Upload honeypot CSV", type=["csv"])



df = Nonedf = None

# uploaded override (manual)# uploaded override (manual)

if uploaded is not None:if uploaded is not None:

    try:    try:

        df = pd.read_csv(uploaded)        df = pd.read_csv(uploaded)

        df = normalize_honeypot_data(df)        df = normalize_honeypot_data(df)

        st.sidebar.success(f"Loaded uploaded CSV ({len(df)} rows)")        st.sidebar.success(f"Loaded uploaded CSV ({len(df)} rows)")

    except Exception as e:    except Exception as e:

        st.sidebar.error("Failed to load uploaded file: " + str(e))        st.sidebar.error("Failed to load uploaded file: " + str(e))



# primary: aggregated output CSV# primary: aggregated output CSV

if df is None and OUTPUT_CSV.exists():if df is None and OUTPUT_CSV.exists():

    try:    try:

        df = pd.read_csv(OUTPUT_CSV)        df = pd.read_csv(OUTPUT_CSV)

        df = normalize_honeypot_data(df)        df = normalize_honeypot_data(df)

        st.sidebar.info(f"Loaded {OUTPUT_CSV} ({len(df)} rows)")        st.sidebar.info(f"Loaded {OUTPUT_CSV} ({len(df)} rows)")

    except Exception as e:    except Exception as e:

        st.sidebar.error("Failed to read output CSV: " + str(e))        st.sidebar.error("Failed to read output CSV: " + str(e))



# fallback: demo# fallback: demo

if df is None and use_demo:if df is None and use_demo:

    # small demo    # small demo

    rows = []    rows = []

    for i in range(60):    for i in range(60):

        rows.append({"session_id":f"demo{i}", "timestamp":pd.Timestamp.now()-pd.Timedelta(minutes=i*7),        rows.append({"session_id":f"demo{i}", "timestamp":pd.Timestamp.now()-pd.Timedelta(minutes=i*7),

                     "src_ip":f"10.9.{i%255}.{(i*3)%255}", "dst_port": int(np.random.choice([22,80,443,8080,23]))})                     "src_ip":f"10.9.{i%255}.{(i*3)%255}", "dst_port": int(np.random.choice([22,80,443,8080,23]))})

    df = pd.DataFrame(rows)    df = pd.DataFrame(rows)

    df = normalize_honeypot_data(df)    df = normalize_honeypot_data(df)

    st.sidebar.info("Using demo dataset")    st.sidebar.info("Using demo dataset")



# if still nothing -> stop# if still nothing -> stop

if df is None:if df is None:

    st.warning("No dataset loaded. Upload a CSV, enable demo, or create output/honeypot_sessions.csv.")    st.warning("No dataset loaded. Upload a CSV, enable demo, or create output/honeypot_sessions.csv.")

    st.stop()    st.stop()



# -------------# -------------

# Sidebar debug (small)# Sidebar debug (small)

# -------------# -------------

st.sidebar.markdown("**Dataset**")st.sidebar.markdown("**Dataset**")

st.sidebar.write("Rows:", len(df))st.sidebar.write("Rows:", len(df))

st.sidebar.write("Columns:", list(df.columns))st.sidebar.write("Columns:", list(df.columns))

if "dst_port" in df.columns:if "dst_port" in df.columns:

    st.sidebar.write("dst_port sample:", df["dst_port"].dropna().astype(str).unique()[:8].tolist())    st.sidebar.write("dst_port sample:", df["dst_port"].dropna().astype(str).unique()[:8].tolist())



# -------------# -------------

# UI: simple graphs# UI: simple graphs

# -------------# -------------

st.title("🏠 Honeypot Analytics Dashboard")st.title("🏠 Honeypot Analytics Dashboard")

st.markdown("Dataset overview")st.markdown("Dataset overview")

c1, c2, c3, c4 = st.columns(4)c1, c2, c3, c4 = st.columns(4)

c1.metric("Total sessions", f"{len(df):,}")c1.metric("Total sessions", f"{len(df):,}")

c2.metric("Columns", f"{len(df.columns)}")c2.metric("Columns", f"{len(df.columns)}")

c3.metric("Unique sources", f"{df['src_ip'].nunique() if 'src_ip' in df.columns else 0:,}")c3.metric("Unique sources", f"{df['src_ip'].nunique() if 'src_ip' in df.columns else 0:,}")

c4.metric("Rows", f"{len(df):,}")c4.metric("Rows", f"{len(df):,}")



st.markdown("### First rows")st.markdown("### First rows")

st.dataframe(df.head(20), use_container_width=True)st.dataframe(df.head(20), use_container_width=True)



st.markdown("### Attack analysis")st.markdown("### Attack analysis")

tabs = st.tabs(["Attack Types","Ports","Timeline","Geography","Raw Data"])tabs = st.tabs(["Attack Types","Ports","Timeline","Geography","Raw Data"])

with tabs[0]:with tabs[0]:

    if "attack_type" not in df.columns:    if "attack_type" not in df.columns:

        st.info("No attack_type column found")        st.info("No attack_type column found")

    else:    else:

        s = df['attack_type'].fillna("unknown").value_counts().reset_index()        s = df['attack_type'].fillna("unknown").value_counts().reset_index()

        s.columns = ["attack_type","count"]        s.columns = ["attack_type","count"]

        st.plotly_chart(px.bar(s, x="attack_type", y="count", title="Attack Types"), use_container_width=True)        st.plotly_chart(px.bar(s, x="attack_type", y="count", title="Attack Types"), use_container_width=True)

with tabs[1]:with tabs[1]:

    if "dst_port" not in df.columns or df["dst_port"].dropna().empty:    if "dst_port" not in df.columns or df["dst_port"].dropna().empty:

        st.info("No destination port data available")        st.info("No destination port data available")

    else:    else:

        ports = df["dst_port"].dropna().astype(int).value_counts().reset_index().rename(columns={"index":"port","dst_port":"count"})        ports = df["dst_port"].dropna().astype(int).value_counts().reset_index().rename(columns={"index":"port","dst_port":"count"})

        st.plotly_chart(px.bar(ports, x="port", y="count", title="Top Destination Ports"), use_container_width=True)        st.plotly_chart(px.bar(ports, x="port", y="count", title="Top Destination Ports"), use_container_width=True)

with tabs[2]:with tabs[2]:

    if "timestamp" not in df.columns or df["timestamp"].isna().all():    if "timestamp" not in df.columns or df["timestamp"].isna().all():

        st.info("No timestamps")        st.info("No timestamps")

    else:    else:

        ts = df.set_index("timestamp").resample("H").size().reset_index(name="count")        ts = df.set_index("timestamp").resample("H").size().reset_index(name="count")

        st.plotly_chart(px.line(ts, x="timestamp", y="count", title="Sessions over time"), use_container_width=True)        st.plotly_chart(px.line(ts, x="timestamp", y="count", title="Sessions over time"), use_container_width=True)

with tabs[3]:with tabs[3]:

    if "src_country" in df.columns:    if "src_country" in df.columns:

        s = df['src_country'].fillna("UNKNOWN").value_counts().reset_index()        s = df['src_country'].fillna("UNKNOWN").value_counts().reset_index()

        s.columns = ["country","count"]        s.columns = ["country","count"]

        st.plotly_chart(px.bar(s, x="country", y="count", title="Top source countries"), use_container_width=True)        st.plotly_chart(px.bar(s, x="country", y="count", title="Top source countries"), use_container_width=True)

    else:    else:

        st.info("No geo data")        st.info("No geo data")

with tabs[4]:with tabs[4]:

    st.dataframe(df.head(500), use_container_width=True)    st.dataframe(df.head(500), use_container_width=True)



# Footer note# Footer note

st.markdown("---")st.markdown("---")

st.write("Tip: For live data, ensure per-VM instances write into `data/sessions/<inst>/` and run the aggregator to produce `output/honeypot_sessions.csv`. The dashboard watches that CSV and reloads automatically.")st.write("Tip: For live data, ensure per-VM instances write into `data/sessions/<inst>/` and run the aggregator to produce `output/honeypot_sessions.csv`. The dashboard watches that CSV and reloads automatically.")

        rows.append({
            "session_id": f"demo_{i:06d}",
            "timestamp": ts.isoformat(),
            "host": "demo-honeypot",
            "src_ip": src,
            "src_asn": f"AS{1000 + np.random.randint(1, 200)}",
            "src_country": np.random.choice(['CN', 'US', 'RU', 'IN', 'BR', 'DE', 'UNKNOWN']),
            "dst_ip": "10.0.0.5",
            "dst_port": int(np.random.choice([22, 80, 443, 8080, 23, 3389, 445, 21])),
            "protocol": "tcp",
            "attack_type": label,
            "username": np.random.choice(['root', 'admin', 'user', 'test', 'NULL'], p=[0.15, 0.12, 0.25, 0.1, 0.38]),
            "password": np.random.choice(['123456', 'password', 'admin', 'NULL'], p=[0.12, 0.12, 0.1, 0.66]),
            "success": int(np.random.rand() < 0.02),
            "bytes_in": int(np.random.randint(40, 200000)),
            "bytes_out": int(np.random.randint(20, 50000)),
            "payload_hash": "" if np.random.rand() < 0.85 else f"sha256:{np.random.bytes(8).hex()}",
            "files_dropped": int(np.random.choice([0, 0, 0, 1, 2])),
            "transcript": "demo_transcript"
        })
    return pd.DataFrame(rows)

def normalize_honeypot_data(df):
    """Normalize honeypot CSV columns."""
    if df.empty:
        return df
    
    # Create lowercase mapping
    lowermap = {col.lower(): col for col in df.columns}
    rename_map = {}
    
    # Normalize username
    for cand in ("user", "username", "uname", "account"):
        if cand in lowermap:
            rename_map[lowermap[cand]] = "username"
            break
    
    # Normalize password
    for cand in ("pass", "password", "pwd"):
        if cand in lowermap:
            rename_map[lowermap[cand]] = "password"
            break
    
    # Apply renames
    if rename_map:
        df = df.rename(columns=rename_map)
    
    # Port extractor
    port_re = re.compile(r"(\d{1,5})")
    
    def extract_port(val):
        if pd.isna(val):
            return None
        try:
            if isinstance(val, (int, float)) and not np.isnan(val):
                return int(val)
            s = str(val).strip()
            if s.isdigit():
                return int(s)
            if ":" in s:
                tail = s.split(":")[-1]
                if tail.isdigit():
                    return int(tail)
            if "/" in s:
                tail = s.split("/")[-1]
                if tail.isdigit():
                    return int(tail)
            if "," in s:
                first = s.split(",")[0].strip()
                if first.isdigit():
                    return int(first)
            m = port_re.search(s)
            if m:
                p = int(m.group(1))
                if 0 < p < 65536:
                    return p
        except Exception:
            return None
        return None
    
    # Populate dst_port if missing
    if "dst_port" not in df.columns:
        for cand in ("service", "connection", "endpoint", "dst", "dpt", "dest", "port"):
            if cand in df.columns:
                df["dst_port"] = df[cand].apply(extract_port)
                break
    
    if "dst_port" in df.columns:
        df["dst_port"] = df["dst_port"].apply(extract_port)
        df["dst_port"] = pd.to_numeric(df["dst_port"], errors="coerce").astype("Int64")
    
    if "src_port" in df.columns:
        df["src_port"] = df["src_port"].apply(extract_port)
        df["src_port"] = pd.to_numeric(df["src_port"], errors="coerce").astype("Int64")
    
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", infer_datetime_format=True)
    
    if "attack_type" in df.columns:
        df["attack_type"] = df["attack_type"].astype(str).str.lower().str.replace(r"\s+", "_", regex=True)
    
    # Ensure IP columns
    if "src_ip" not in df.columns:
        for cand in ("src", "source", "saddr"):
            if cand in df.columns:
                df = df.rename(columns={cand: "src_ip"})
                break
    
    if "dst_ip" not in df.columns:
        for cand in ("dst", "destination", "daddr"):
            if cand in df.columns:
                df = df.rename(columns={cand: "dst_ip"})
                break
    
    for ipcol in ("src_ip", "dst_ip"):
        if ipcol in df.columns:
            df[ipcol] = df[ipcol].astype(str).str.strip().replace({"nan": None, "None": None})
    
    return df

# ============ DATA LOADING ============

st.sidebar.header("📊 Data Source")
use_demo = st.sidebar.checkbox("Use demo data", value=True)

# File uploader
uploader = st.sidebar.file_uploader("Upload honeypot CSV", type=["csv"])

# Load data
df = None

if uploader is not None:
    try:
        df = safe_load_csv(uploader)
        df = normalize_honeypot_data(df)
        st.sidebar.success(f"Loaded {len(df)} rows from uploaded file")
    except Exception as e:
        st.sidebar.error(f"Error loading file: {e}")
elif WATCH_PATH.exists():
    try:
        df = safe_load_csv(WATCH_PATH)
        df = normalize_honeypot_data(df)
        st.sidebar.info(f"Loaded {len(df)} rows from {WATCH_PATH.name}")
    except Exception as e:
        st.sidebar.warning(f"Error loading watch file: {e}")

# Use demo if no CSV loaded
if df is None or df.empty:
    if use_demo:
        df = make_demo(1200)
        st.sidebar.info("Loaded demo data (1200 rows)")
    else:
        st.error("No data loaded. Upload a file or enable demo mode.")
        st.stop()

# ============ DATA DISPLAY ============

st.subheader("📈 Dataset Overview")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Sessions", len(df))
with col2:
    if "attack_type" in df.columns:
        st.metric("Attack Types", df["attack_type"].nunique())
    else:
        st.metric("Columns", len(df.columns))
with col3:
    if "src_ip" in df.columns:
        st.metric("Unique Sources", df["src_ip"].nunique())
    else:
        st.metric("Rows", len(df))
with col4:
    if "dst_port" in df.columns:
        st.metric("Ports Used", df["dst_port"].nunique())
    else:
        st.metric("Rows", len(df))

# Data preview
st.write("**First 10 rows:**")
st.dataframe(df.head(10), use_container_width=True)

# ============ VISUALIZATIONS ============

st.subheader("🔍 Attack Analysis")

tabs = st.tabs(["Attack Types", "Ports", "Timeline", "Geography", "Raw Data"])

with tabs[0]:
    if "attack_type" in df.columns:
        attack_counts = df["attack_type"].value_counts()
        fig = px.bar(x=attack_counts.index, y=attack_counts.values, labels={"x": "Attack Type", "y": "Count"}, title="Attacks by Type")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No attack_type column found")

with tabs[1]:
    if "dst_port" in df.columns:
        port_counts = df[df["dst_port"].notna()]["dst_port"].value_counts().head(15)
        fig = px.bar(x=port_counts.index.astype(str), y=port_counts.values, labels={"x": "Destination Port", "y": "Count"}, title="Top 15 Ports Targeted")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No dst_port column found")

with tabs[2]:
    if "timestamp" in df.columns:
        df_ts = df.copy()
        df_ts["timestamp"] = pd.to_datetime(df_ts["timestamp"], errors="coerce")
        df_ts = df_ts.dropna(subset=["timestamp"])
        if not df_ts.empty:
            df_ts = df_ts.set_index("timestamp").resample("1H").size()
            fig = px.line(x=df_ts.index, y=df_ts.values, labels={"x": "Time", "y": "Sessions"}, title="Sessions Over Time")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No valid timestamps")
    else:
        st.info("No timestamp column found")

with tabs[3]:
    if "src_country" in df.columns:
        geo_counts = df["src_country"].value_counts().head(10)
        fig = px.pie(values=geo_counts.values, names=geo_counts.index, title="Top 10 Source Countries")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No src_country column found")

with tabs[4]:
    st.write("**Full Dataset:**")
    st.dataframe(df, use_container_width=True)

# ============ EXPORT ============

st.subheader("💾 Export")
csv_data = df.to_csv(index=False)
st.download_button("Download CSV", csv_data, "honeypot_data.csv", "text/csv")
