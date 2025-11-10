# app_auto.py — stable honeypot dashboard (watcher + normalizer)
import importlib, os, time
from pathlib import Path
import pandas as pd
import numpy as np
import re
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

ROOT = Path(__file__).parent
OUT_CSV = ROOT / "output" / "honeypot_sessions.csv"
MERGE_SCRIPT = ROOT / "merge_sessions.py"

# Attack advice mapping
ATTACK_ADVICE = {
    "bruteforce": {
        "description": "Repeated login attempts / credential guessing",
        "how_attacker_got_in": "Service exposed (SSH/FTP) with weak or reused credentials.",
        "recommendations": [
            "Disable password authentication; use SSH keys.",
            "Enforce strong password policy and lockout after N attempts.",
            "Rate limit / fail2ban on authentication endpoints.",
            "Move service behind VPN or allowlist known IPs."
        ]
    },
    "recon": {
        "description": "Port scans or information discovery",
        "how_attacker_got_in": "Exposed ports and responses revealed services and banners.",
        "recommendations": [
            "Minimize exposed ports, close unused services.",
            "Use port knocking / require auth for service banners.",
            "Deploy network IDS to detect scanning behavior.",
            "Harden service banners and enable minimal responses."
        ]
    },
    "exploit": {
        "description": "Exploit / payload delivery attempts",
        "how_attacker_got_in": "Vulnerable service or software with known CVE or remote command execution.",
        "recommendations": [
            "Patch and update vulnerable software immediately.",
            "Isolate risky services in restricted networks (segmentation).",
            "Use WAF for web services and intrusion prevention systems.",
            "Run services with least privilege; containerize legacy apps."
        ]
    },
    "malware": {
        "description": "Malware or ransomware behavior",
        "how_attacker_got_in": "Malicious payload execution via exploit or phishing.",
        "recommendations": [
            "Block outgoing connections to C2 by default.",
            "Use EDR and periodic scans, restrict file execution paths.",
            "Backup critical data and test recovery procedures.",
            "Use strict process whitelisting for servers."
        ]
    },
    "unknown": {
        "description": "Unknown / unclassified activity",
        "how_attacker_got_in": "Not enough information to classify.",
        "recommendations": [
            "Collect more telemetry (full packet capture, command sequences).",
            "Increase logging detail for further analysis."
        ]
    }
}

st.set_page_config(layout="wide", page_title="Honeypot Analytics", initial_sidebar_state="expanded")

# 1) attempt to run aggregator (safe: won't crash if script missing)
try:
    if MERGE_SCRIPT.exists():
        # import as module to reuse functions if available
        spec = importlib.util.spec_from_file_location("merge_sessions", str(MERGE_SCRIPT))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        # call gather_and_merge if present
        if hasattr(mod, "gather_and_merge"):
            try:
                mod.gather_and_merge()
            except Exception:
                # ignore any runtime error from aggregator; continue to load existing CSV
                pass
except Exception:
    pass

# 2) simple CSV watcher stored in session_state
if "watcher_mtime" not in st.session_state:
    st.session_state["watcher_mtime"] = None

def maybe_reload_from_csv():
    if OUT_CSV.exists():
        m = OUT_CSV.stat().st_mtime
        prev = st.session_state.get("watcher_mtime")
        # first run: set mtime but don't force rerun
        if prev is None:
            st.session_state["watcher_mtime"] = m
        elif m != prev:
            st.session_state["watcher_mtime"] = m
            # try preferred rerun
            try:
                if hasattr(st, "experimental_rerun"):
                    st.experimental_rerun()
                    return
            except Exception:
                pass
            # fallback: tweak query params
            try:
                params = st.experimental_get_query_params()
                params["_refresh"] = [str(time.time())]
                st.experimental_set_query_params(**params)
            except Exception:
                st.session_state["_need_manual_refresh"] = not st.session_state.get("_need_manual_refresh", False)
                st.stop()

maybe_reload_from_csv()
# small yield
time.sleep(0.01)

# 3) Normalizer / extractor used across app
PORT_RE = re.compile(r"(\d{1,5})")
def extract_port(val):
    if pd.isna(val): return None
    if isinstance(val, (int, np.integer)): return int(val)
    s = str(val)
    # common "ip:port" patterns
    if ":" in s:
        tail = s.rsplit(":", 1)[-1]
        if tail.isdigit(): return int(tail)
    # "tcp/2222" etc
    if "/" in s:
        tail = s.rsplit("/", 1)[-1]
        if tail.isdigit(): return int(tail)
    m = PORT_RE.search(s)
    if m:
        p = int(m.group(1))
        if 0 < p < 65536:
            return p
    return None

# GeoIP lookup - try ipinfo API (Option B - simple, internet required)
def lookup_country_ipinfo(ip):
    """Lookup country code from ipinfo.io API."""
    try:
        import requests
        url = f"https://ipinfo.io/{ip}/json"
        r = requests.get(url, timeout=2)
        if r.ok:
            j = r.json()
            return j.get("country")
    except Exception:
        pass
    return None

def enrich_geo(df):
    """Add src_country column if not present, using ipinfo API."""
    if "src_country" in df.columns and df["src_country"].notna().any():
        return df
    # resolve src_ip -> country
    vals = []
    for ip in df.get("src_ip", pd.Series([])).fillna("").astype(str):
        if not ip or ip == "nan":
            vals.append(None)
            continue
        c = lookup_country_ipinfo(ip)
        vals.append(c)
    df["src_country"] = pd.Series(vals, index=df.index)
    return df

# Robust timestamp parser for mixed formats
def robust_parse_timestamps(series):
    """Return DatetimeIndex-friendly series with best-effort parsing."""
    if series is None:
        return pd.Series(dtype="datetime64[ns]")
    s = series.copy().astype(str).replace({"nan":"", "None":"", "NaN":""})
    # 1) try direct parse
    dt = pd.to_datetime(s, errors="coerce")
    # 2) rows still NaT: try numeric epoch seconds or ms
    need = dt.isna()
    if need.any():
        def parse_num(v):
            try:
                v2 = float(v)
            except Exception:
                return pd.NaT
            # heuristic: >1e12 likely ms, >1e9 is seconds
            if v2 > 1e12:
                return pd.to_datetime(int(v2/1000), unit="s", errors="coerce")
            if v2 > 1e9:
                return pd.to_datetime(int(v2), unit="s", errors="coerce")
            return pd.NaT
        parsed = s[need].map(parse_num)
        dt.loc[need] = parsed.values
    return dt

# Basic attack type heuristic using events text/commands
def infer_attack_type_from_events(ev):
    # ev could be JSON-string, python-list-string, or plain text: normalize to string
    if pd.isna(ev): return "unknown"
    s = str(ev).lower()
    # quick heuristics (tweak to your needs)
    if any(k in s for k in ("wget ", "curl ", "download ", "exploit", "payload", "meterpreter", "reverse")):
        return "exploit"
    if any(k in s for k in ("nmap", "masscan", "scan", "port scan", "syn scan", "sweep")):
        return "recon"
    if any(k in s for k in ("password", "login", "ssh", "bruteforce", "failed password", "authentication")):
        return "bruteforce"
    if any(k in s for k in ("uname", "id ", "whoami", "ls ", "pwd", "hostname", "cat /etc")):
        return "recon"
    if any(k in s for k in ("ransom", "encrypt", "encrypting", "locky", "cerber")):
        return "malware"
    # fallback
    return "unknown"

def normalize_honeypot_data(df):
    if df is None: return df
    df = df.copy()
    # safe normalize column names (strip/trailing)
    df.columns = [c.strip() for c in df.columns]
    # map common names
    col_lower = {c.lower(): c for c in df.columns}
    rename_map = {}
    for cand in ("src_ip","source","src"):
        if cand in col_lower:
            rename_map[col_lower[cand]] = "src_ip"; break
    for cand in ("dst_port","dpt","port","dest_port"):
        if cand in col_lower:
            rename_map[col_lower[cand]] = "dst_port"; break
    for cand in ("timestamp","time","start_ts","start_time","end_time"):
        if cand in col_lower:
            rename_map[col_lower[cand]] = "timestamp"; break
    if rename_map:
        df = df.rename(columns=rename_map)
    # coerce timestamp using robust parser
    if "timestamp" in df.columns:
        df["timestamp"] = robust_parse_timestamps(df["timestamp"])
    else:
        # try fallback columns often used: end_time, start_ts
        for cand in ("end_time","start_ts","start_time","time"):
            if cand in df.columns:
                df["timestamp"] = robust_parse_timestamps(df[cand])
                break
    # dst_port extraction
    if "dst_port" in df.columns:
        df["dst_port"] = df["dst_port"].map(extract_port)
    else:
        # try candidate columns that may contain port info
        for c in df.columns:
            if any(k in c.lower() for k in ("port","dpt","dest","conn","endpoint")):
                df["dst_port"] = df[c].map(extract_port)
                if df["dst_port"].notna().any():
                    break
    # ensure numeric int dtype
    if "dst_port" in df.columns:
        df["dst_port"] = pd.to_numeric(df["dst_port"], errors="coerce").astype("Int64")
    # infer attack_type if not present
    if "attack_type" not in df.columns:
        if "events" in df.columns:
            df["attack_type"] = df["events"].apply(infer_attack_type_from_events)
        else:
            df["attack_type"] = "unknown"
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
        df = enrich_geo(df)  # Add geo enrichment
        st.sidebar.success(f"Loaded uploaded CSV ({len(df)} rows)")
    except Exception as e:
        st.sidebar.error("Failed to load uploaded file: " + str(e))

if df is None and OUT_CSV.exists():
    try:
        df = pd.read_csv(OUT_CSV)
        df = normalize_honeypot_data(df)
        df = enrich_geo(df)  # Add geo enrichment
        st.sidebar.info(f"Loaded {OUT_CSV} ({len(df)} rows)")
    except Exception as e:
        st.sidebar.error("Failed to read output CSV: " + str(e))

if df is None and use_demo:
    rows = []
    for i in range(60):
        rows.append({"session_id":f"demo{i}", "timestamp":pd.Timestamp.now()-pd.Timedelta(minutes=i*7),
                     "src_ip":f"10.9.{i%255}.{(i*3)%255}", "dst_port": int(np.random.choice([22,80,443,8080,23]))})
    df = pd.DataFrame(rows)
    df = normalize_honeypot_data(df)
    df = enrich_geo(df)  # Add geo enrichment (will cache IPs if available)
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
tabs = st.tabs(["Attack Types","Ports","Timeline","Geography","Attack Insights","Raw Data"])
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
        ports_vc = df["dst_port"].dropna().astype(int).value_counts().reset_index()
        # pandas 2.0+ names the value_counts result as 'count', so rename it explicitly
        if "count" in ports_vc.columns:
            ports = ports_vc.rename(columns={"dst_port": "port"})
        else:
            ports = ports_vc.rename(columns={"index":"port", ports_vc.columns[1]: "count"})
        st.plotly_chart(px.bar(ports, x="port", y="count", title="Top Destination Ports"), use_container_width=True)
with tabs[2]:
    if "timestamp" not in df.columns or df["timestamp"].isna().all():
        st.info("No timestamps available for time-series")
    else:
        # Use 'h' instead of deprecated 'H'
        ts = df.set_index("timestamp").resample("h").size().reset_index(name="count")
        if not ts.empty and len(ts) > 0:
            st.plotly_chart(px.line(ts, x="timestamp", y="count", title="Sessions per hour"), use_container_width=True)
        else:
            st.info("No valid timestamp data for time-series")
with tabs[3]:
    if "src_country" in df.columns and df["src_country"].notna().any():
        s = df['src_country'].fillna("UNKNOWN").value_counts().reset_index()
        s.columns = ["country","count"]
        st.plotly_chart(px.bar(s, x="country", y="count", title="Top source countries"), use_container_width=True)
    else:
        st.info("No geo data available (run GeoIP enrichment)")
with tabs[4]:
    st.markdown("### 🔎 Attack Insights & Recommendations")
    if "attack_type" not in df.columns:
        st.warning("No 'attack_type' column — attempting to infer from events.")
        df["attack_type"] = df.get("events", "").apply(infer_attack_type_from_events)
    attack_counts = df["attack_type"].value_counts().reset_index()
    attack_counts.columns = ["attack_type","count"]
    col1, col2 = st.columns(2)
    with col1:
        st.dataframe(attack_counts, use_container_width=True)
    with col2:
        selected = st.selectbox("Select attack type for recommendations", attack_counts["attack_type"])
        info = ATTACK_ADVICE.get(selected, ATTACK_ADVICE["unknown"])
        st.subheader(f"📋 {selected.upper()}")
        st.markdown(f"**{info['description']}**")
        st.markdown(f"**How attacker got in:** {info['how_attacker_got_in']}")
        st.markdown("**Recommended actions:**")
        for r in info["recommendations"]:
            st.markdown(f"- {r}")
with tabs[5]:
    st.dataframe(df.head(500), use_container_width=True)

st.markdown("---")
st.write("Tip: For live data, ensure per-VM instances write into 'data/sessions/<inst>/' and run the aggregator to produce 'output/honeypot_sessions.csv'. The dashboard watches that CSV and reloads automatically.")
