# app_auto.py — stable honeypot dashboard (watcher + normalizer)
import importlib, os, time, tempfile
from pathlib import Path
import pandas as pd
import numpy as np
import re
import json
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import io
import zipfile
import plotly.io as pio
from datetime import datetime

try:
    from src.attack_recommendations import get_recommendations, format_action_for_display
except ImportError:
    # Fallback if module not available
    def get_recommendations(attack_type):
        return {"title": attack_type, "actions": []}
    def format_action_for_display(action):
        return str(action)

ROOT = Path(__file__).parent
OUT_CSV = ROOT / "output" / "honeypot_sessions.csv"
MERGE_SCRIPT = ROOT / "merge_sessions.py"
SESSIONS_ROOT = ROOT / "data" / "sessions"

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
# DISABLED: merge_sessions overwrites demo data - comment back in for production
# try:
#     if MERGE_SCRIPT.exists():
#         # import as module to reuse functions if available
#         spec = importlib.util.spec_from_file_location("merge_sessions", str(MERGE_SCRIPT))
#         mod = importlib.util.module_from_spec(spec)
#         spec.loader.exec_module(mod)
#         # call gather_and_merge if present
#         if hasattr(mod, "gather_and_merge"):
#             try:
#                 mod.gather_and_merge()
#             except Exception:
#                 # ignore any runtime error from aggregator; continue to load existing CSV
#                 pass
# except Exception:
#     pass

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
                params = st.query_params
                params["_refresh"] = str(time.time())
                st.query_params.update(params)
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


# GeoIP lookup - offline MaxMind GeoLite2 database (Option A - self-contained)
GEOIP_DB_PATH = ROOT / "data" / "GeoLite2-Country.mmdb"
_geoip_reader = None

def get_geoip_reader():
    """Lazy-load geoip2 reader (cached)."""
    global _geoip_reader
    if _geoip_reader is not None:
        return _geoip_reader
    if not GEOIP_DB_PATH.exists():
        return None
    try:
        from geoip2.database import Reader
        _geoip_reader = Reader(str(GEOIP_DB_PATH))
        return _geoip_reader
    except Exception as e:
        st.warning(f"Could not load GeoIP database: {e}")
        return None

def lookup_country_maxmind(ip):
    """Lookup country code from MaxMind offline database."""
    if not ip or ip == "nan" or ip == "127.0.0.1" or ip == "localhost":
        return None
    reader = get_geoip_reader()
    if not reader:
        return None
    try:
        response = reader.country(ip)
        return response.country.iso_code
    except Exception:
        return None

def enrich_geo(df):
    """Add src_country column if not present, using MaxMind offline database."""
    if "src_country" in df.columns and df["src_country"].notna().any():
        return df
    # Resolve src_ip -> country code using offline MaxMind
    vals = []
    for ip in df.get("src_ip", pd.Series([])).fillna("").astype(str):
        if not ip or ip == "nan":
            vals.append(None)
            continue
        # Skip localhost IPs (demo data)
        if ip in ("127.0.0.1", "localhost", "::1"):
            vals.append("LOCAL")  # Mark as local for demo/testing
            continue
        c = lookup_country_maxmind(ip)
        vals.append(c if c else "UNKNOWN")
    df["src_country"] = pd.Series(vals, index=df.index)
    return df

def _atomic_write_csv(df, out_path: Path):
    """
    Write df to out_path atomically: write to tmp file then replace.
    Returns True on success, False on failure.
    """
    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        # create a secure temp file in same directory (same filesystem)
        dir_for_tmp = out_path.parent
        fd, tmp_name = tempfile.mkstemp(prefix="._tmp_honeypot_", dir=str(dir_for_tmp))
        try:
            # Use pandas to_csv which accepts a filename
            os.close(fd)  # close fd because pandas will open the file path
            df.to_csv(tmp_name, index=False)
            # atomic replace
            os.replace(tmp_name, str(out_path))
            # Ensure mtime updated
            out_path.touch()
        finally:
            # if tmp still exists (error path), remove
            if os.path.exists(tmp_name):
                try:
                    os.remove(tmp_name)
                except Exception:
                    pass
        return True
    except Exception as e:
        # keep errors visible in the dashboard (sidebar) or logs
        try:
            import streamlit as _st
            _st.sidebar.warning(f"Could not write CSV {out_path}: {e}")
        except Exception:
            print(f"[WARN] Could not write CSV {out_path}: {e}")
        return False

# ----- Plotting & export helpers -----
def make_all_plots(df, top_n_ips=10, top_n_ports=20, time_freq='H'):
    """Return dict of plotly figures keyed by name."""
    figs = {}
    # Attack type frequency
    if "attack_type" in df.columns:
        btc = df['attack_type'].value_counts().reset_index()
        btc.columns = ['attack_type','count']
        figs['attack_type_freq'] = px.bar(btc, x='attack_type', y='count', title="Attack Types Frequency")
    else:
        figs['attack_type_freq'] = None

    # Top attacker IPs
    if "src_ip" in df.columns:
        top_ips = df['src_ip'].value_counts().head(top_n_ips).reset_index()
        top_ips.columns = ['src_ip','sessions']
        figs['top_ips'] = px.bar(top_ips, x='src_ip', y='sessions', title=f"Top {top_n_ips} Attacker IPs")
    else:
        figs['top_ips'] = None

    # Top ports
    if "dst_port" in df.columns:
        top_ports = df['dst_port'].dropna().astype(int).value_counts().head(top_n_ports).reset_index()
        top_ports.columns = ['dst_port','count']
        figs['top_ports'] = px.bar(top_ports, x='dst_port', y='count', title=f"Top {top_n_ports} Destination Ports")
    else:
        figs['top_ports'] = None

    # Time-series sessions (if timestamp exists)
    if "timestamp" in df.columns and not df['timestamp'].isna().all():
        ts = df.copy()
        ts['timestamp'] = pd.to_datetime(ts['timestamp'], errors='coerce', infer_datetime_format=True)
        bytime = ts.set_index('timestamp').resample(time_freq).size().reset_index(name='sessions')
        figs['time_series'] = px.line(bytime, x='timestamp', y='sessions', title='Sessions Over Time')
    else:
        figs['time_series'] = None

    # Geo bar if src_country present
    if 'src_country' in df.columns and df['src_country'].notna().any():
        gc = df['src_country'].value_counts().reset_index()
        gc.columns = ['country','count']
        figs['geo_bar'] = px.bar(gc, x='country', y='count', title='Attacks by Country')
    else:
        figs['geo_bar'] = None

    return figs

def fig_to_png_bytes(fig):
    """Return PNG bytes for a Plotly figure. Requires kaleido."""
    if fig is None:
        return None
    try:
        img_bytes = pio.to_image(fig, format='png', engine="kaleido")
        return img_bytes
    except Exception as e:
        st.warning(f"PNG export failed: {e}")
        return None

def build_all_png_zip(figs):
    """Return bytes of a zip file that contains PNGs for all figs in figs dict."""
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, mode="w") as zf:
        for name, fig in figs.items():
            if fig is None:
                continue
            png = fig_to_png_bytes(fig)
            if png:
                zf.writestr(f"{name}.png", png)
    mem.seek(0)
    return mem.getvalue()

def generate_clean_excel_bytes(df, top_n_lists=50, alert_threshold=70):
    """Create a clean Excel workbook in-memory with multiple sheets."""
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="xlsxwriter") as writer:
        # raw sheet
        df.to_excel(writer, sheet_name="raw_events", index=False)
        # aggregated by src_ip
        if 'src_ip' in df.columns:
            agg = df.groupby(['src_ip'], dropna=False).agg(
                sessions=('session_id','nunique') if 'session_id' in df.columns else ('src_ip','size')
            ).reset_index().sort_values('sessions', ascending=False)
            agg.to_excel(writer, sheet_name="by_src", index=False)
        # Top lists sheet
        if 'dst_port' in df.columns:
            top_ports = df['dst_port'].dropna().astype(int).value_counts().head(top_n_lists).reset_index()
            top_ports.columns = ['dst_port','count']
            top_ports.to_excel(writer, sheet_name="top_ports", index=False)
        if 'attack_type' in df.columns:
            top_attacks = df['attack_type'].value_counts().reset_index()
            top_attacks.columns = ['attack_type','count']
            top_attacks.to_excel(writer, sheet_name="attack_types", index=False)
        # small summary
        summary = {
            "total_sessions": [len(df)],
            "unique_src_ips": [df['src_ip'].nunique() if 'src_ip' in df.columns else 0]
        }
        pd.DataFrame(summary).to_excel(writer, sheet_name="summary", index=False)
    out.seek(0)
    return out.getvalue()

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
    
    # Skip if already processed (no brackets means it's already cleaned)
    if '[' not in s and '|' not in s:
        # Look for action keywords in plain text summary
        if any(k in s for k in ("wget ", "curl ", "download ", "exploit", "payload")):
            return "exploit"
        if any(k in s for k in ("cmd:", "attacker_cmd")):
            return "malware"
        if any(k in s for k in ("connection events only", "no events")):
            return "recon"
    
    # Heuristic inference from event text
    if any(k in s for k in ("wget ", "curl ", "download ", "exploit", "payload", "meterpreter", "reverse")):
        return "exploit"
    if any(k in s for k in ("nmap", "masscan", "scan", "port scan", "syn scan", "sweep")):
        return "recon"
    if any(k in s for k in ("password", "login", "ssh", "bruteforce", "failed password", "authentication")):
        return "bruteforce"
    if any(k in s for k in ("uname", "id ", "whoami", "ls ", "pwd", "hostname", "cat /etc", "cmd:")):
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
            # First try to extract from events dict string (if events contains {'attack_type': ...})
            def extract_attack_type_from_events_dict(ev_str):
                if pd.isna(ev_str):
                    return "unknown"
                try:
                    # Try to parse as Python dict string
                    import ast
                    ev_dict = ast.literal_eval(str(ev_str))
                    if isinstance(ev_dict, dict) and 'attack_type' in ev_dict:
                        return str(ev_dict['attack_type']).lower().strip()
                except Exception:
                    pass
                # Fallback to heuristic inference
                return infer_attack_type_from_events(ev_str)
            
            df["attack_type"] = df["events"].apply(extract_attack_type_from_events_dict)
        else:
            df["attack_type"] = "unknown"
    
    # Ensure attack_type is canonical but preserve distinct labels
    if 'attack_type' in df.columns:
        # coerce to str, strip, lowercase; fill missing with 'unknown'
        df['attack_type'] = df['attack_type'].astype(str).fillna('unknown')
        df['attack_type'] = df['attack_type'].str.strip().str.lower().replace({'': 'unknown'})
    else:
        df['attack_type'] = 'unknown'
    
    # optional: normalize only obvious synonyms (don't collapse everything)
    attack_map = {
        'bruteforce': 'bruteforce',
        'brute-force': 'bruteforce',
        'brute force': 'bruteforce',
        'exploit': 'exploit',
        'malware': 'malware',
        'recon': 'recon',
        'unknown': 'unknown',
    }
    df['attack_type'] = df['attack_type'].map(lambda x: attack_map.get(x, x))
    return df

# ---------------------
# Load data from VM sessions
# ---------------------

def extract_attack_type_from_meta(events_list):
    """Extract attack type from events list by looking for [CLASS]= marker."""
    if not isinstance(events_list, list):
        return 'unknown'
    
    for event in events_list:
        if isinstance(event, dict):
            text = event.get('text', '').lower()
            if '[class]=' in text:
                # Extract: [CLASS]=recon|0.6|ENG=HIGH → recon
                import re
                m = re.search(r'\[class\]=([a-z_]+)', text)
                if m:
                    return m.group(1)
    return 'unknown'

def format_events_summary(events_list):
    """Format events as readable summary lines."""
    if not isinstance(events_list, list):
        return 'No events'
    
    summaries = []
    for event in events_list:
        if isinstance(event, dict):
            text = event.get('text', '').strip()
            # Skip structural/noise events, keep actionable ones
            if any(skip in text for skip in ['[STRUCT_EVENT]', '[PAYLOAD_SAVED]', '[ACTION]=', '[HIGH_ENGAGEMENT]=', '[CLASS]=']):
                continue
            if text and not text.startswith('['):
                # Clean up and truncate
                if text.startswith('ATTACKER_CMD:'):
                    text = text.replace('ATTACKER_CMD: ', '🔴 CMD: ')
                summaries.append(text[:60])
    
    return ' | '.join(summaries[:3]) if summaries else 'Connection events only'

def load_vm_sessions(root_dir: Path = SESSIONS_ROOT):
    """Load JSON meta files from VM session directories and normalize to standard schema."""
    dfs = []
    if not root_dir.exists():
        return None
    
    # Collect meta.json files from each session directory
    for session_dir in sorted(root_dir.glob("S-*")):
        meta_file = session_dir / "meta.json"
        if meta_file.exists():
            try:
                with open(meta_file, 'r', encoding='utf-8') as f:
                    obj = json.load(f)
                    if isinstance(obj, dict):
                        events = obj.get('events', [])
                        # Normalize VM meta structure to standard honeypot schema
                        row = {
                            'session_id': obj.get('session_id', ''),
                            'src_ip': obj.get('src_ip', '127.0.0.1'),
                            'src_port': obj.get('src_port', None),
                            'timestamp': obj.get('end_time') or obj.get('start_ts'),
                            'events': format_events_summary(events),  # Human-readable summary
                            'dst_port': 2222,  # VM honeypot default port
                            'instance': obj.get('instance', 'default'),
                            'attack_type': extract_attack_type_from_meta(events),  # Extract from [CLASS]=
                        }
                        dfs.append(pd.DataFrame([row]))
                    elif isinstance(obj, list):
                        # If it's a list of objects, normalize each
                        rows = []
                        for item in obj:
                            if isinstance(item, dict):
                                events = item.get('events', [])
                                row = {
                                    'session_id': item.get('session_id', ''),
                                    'src_ip': item.get('src_ip', '127.0.0.1'),
                                    'src_port': item.get('src_port', None),
                                    'timestamp': item.get('end_time') or item.get('start_ts'),
                                    'events': format_events_summary(events),
                                    'dst_port': 2222,
                                    'instance': item.get('instance', 'default'),
                                    'attack_type': extract_attack_type_from_meta(events),
                                }
                                rows.append(row)
                        if rows:
                            dfs.append(pd.DataFrame(rows))
            except Exception as e:
                st.sidebar.warning(f"Failed to load {meta_file}: {e}")
                continue
    
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    return None

# Load data from VM sessions or CSV aggregator
uploaded = st.sidebar.file_uploader("Upload honeypot CSV (optional override)", type=["csv"])

df = None
if uploaded is not None:
    try:
        df = pd.read_csv(uploaded, dtype={"dst_port": "Int64", "src_port": "Int64"}, parse_dates=["timestamp"])
        df = normalize_honeypot_data(df)
        df = enrich_geo(df)
        st.sidebar.success(f"Loaded uploaded CSV ({len(df)} rows)")
    except Exception as e:
        st.sidebar.error("Failed to load uploaded file: " + str(e))
else:
    # Load from VM sessions (primary source)
    df = load_vm_sessions(SESSIONS_ROOT)
    if df is not None and len(df) > 0:
        try:
            df = normalize_honeypot_data(df)
            df = enrich_geo(df)
            st.sidebar.success(f"Loaded {len(df)} sessions from VM data")
            
            # Write canonical CSV atomically so output/honeypot_sessions.csv always exists
            try:
                wrote = _atomic_write_csv(df, OUT_CSV)
                if wrote:
                    st.sidebar.info(f"Wrote canonical CSV: {OUT_CSV.name}")
            except Exception as _e:
                st.sidebar.warning(f"CSV write exception: {_e}")
        except Exception as e:
            st.sidebar.error(f"Failed to process VM data: {str(e)}")
            df = None
    
    # Fallback: Load from CSV if VM sessions unavailable or empty
    if df is None or len(df) == 0:
        if OUT_CSV.exists():
            try:
                df = pd.read_csv(OUT_CSV, dtype={"dst_port": "Int64", "src_port": "Int64"}, parse_dates=["timestamp"])
                df = normalize_honeypot_data(df)
                df = enrich_geo(df)
                st.sidebar.success(f"Loaded {len(df)} sessions from CSV (aggregated data)")
            except Exception as e:
                st.sidebar.error(f"Failed to load CSV: {str(e)}")
                df = None
        else:
            st.sidebar.warning("No VM session data or CSV found. Waiting for sessions...")
            st.info("👉 Run: `python -m src.orchestrator_runner` in one terminal, then `python test_client_interactive.py` in another.")
            st.stop()

if df is None:
    st.warning("No dataset loaded.")
    st.stop()

# Coerce timestamp and typical columns
if "timestamp" in df.columns:
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
if "dst_port" in df.columns:
    df["dst_port"] = pd.to_numeric(df["dst_port"], errors="coerce").astype("Int64")

# ---- Normalize attack_type and ensure selector sees all values ----
# make attack_type canonical: string, trimmed, lowercased
if 'attack_type' in df.columns:
    df['attack_type'] = df['attack_type'].astype(str).fillna('unknown').str.strip().str.lower()
else:
    # create column if missing so the UI still works
    df['attack_type'] = 'unknown'

# optional: map common synonyms to canonical names (expand as needed)
attack_map = {
    'brute force': 'bruteforce',
    'bruteforce': 'bruteforce',
    'bf': 'bruteforce',
    'reconnaissance': 'recon',
    'port-scan': 'portscan',
    'port scan': 'portscan',
    'xss': 'xss',
    'lfi': 'lfi',
    'exploit': 'exploit',
    'malware': 'malware',
    'ddos': 'ddos'
}
df['attack_type'] = df['attack_type'].map(lambda v: attack_map.get(v, v))

# Sidebar debug
st.sidebar.markdown("**Dataset**")
st.sidebar.write("Rows:", len(df))
st.sidebar.write("Columns:", list(df.columns))
if "dst_port" in df.columns:
    st.sidebar.write("dst_port sample:", df["dst_port"].dropna().astype(str).unique()[:8].tolist())

# CSV file verification (prove atomic writes are working)
st.sidebar.markdown("---")
st.sidebar.markdown("**📊 CSV File Status**")
if OUT_CSV.exists():
    csv_mtime = OUT_CSV.stat().st_mtime
    from datetime import datetime as dt
    csv_time = dt.fromtimestamp(csv_mtime).strftime("%Y-%m-%d %H:%M:%S")
    csv_size = OUT_CSV.stat().st_size
    st.sidebar.success(f"✅ File exists")
    st.sidebar.write(f"📝 Path: `{OUT_CSV.name}`")
    st.sidebar.write(f"⏰ Last updated: `{csv_time}`")
    st.sidebar.write(f"📏 Size: `{csv_size:,}` bytes")
else:
    st.sidebar.error("❌ CSV not found")

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
    st.markdown("#### Top Destination Ports")
    if "dst_port" not in df.columns or df["dst_port"].dropna().empty:
        st.info("No destination port data available")
    else:
        # coerce dst_port to numeric, drop NA
        ports = pd.to_numeric(df['dst_port'], errors='coerce').dropna().astype(int)
        
        if ports.empty:
            st.info("No valid port data available.")
        else:
            # Top-N selector in sidebar
            top_n = st.sidebar.number_input("Top N ports to show", min_value=5, max_value=100, value=20, step=5)
            port_counts = ports.value_counts().rename_axis('port').reset_index(name='count').sort_values('count', ascending=False)
            top_ports = port_counts.head(int(top_n))
            
            # plot as bar chart
            try:
                fig_ports = px.bar(top_ports, x='port', y='count', text='count',
                                  title=f"Top {int(top_n)} Destination Ports")
                fig_ports.update_layout(xaxis_title='port', yaxis_title='count', 
                                      template='plotly_dark', height=420)
                st.plotly_chart(fig_ports, use_container_width=True)
            except Exception as e:
                st.bar_chart(top_ports.set_index('port')['count'])
            
            # also provide a histogram view toggle
            with st.expander("📊 Show port distribution histogram"):
                try:
                    hist = px.histogram(ports, nbins=50, title="Port Distribution")
                    hist.update_layout(xaxis_title='port', yaxis_title='frequency', 
                                     template='plotly_dark', height=420)
                    st.plotly_chart(hist, use_container_width=True)
                except Exception:
                    st.write("Histogram unavailable (plotting error).")

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
    st.markdown("### 🔎 Attack Types & Insights")
    # compute counts for all attack types
    attack_counts = df['attack_type'].value_counts().rename_axis('attack_type').reset_index(name='count')
    
    if attack_counts.empty:
        st.info("No attack types to show.")
    else:
        # show a bar chart of all attack types (sorted descending)
        attack_counts = attack_counts.sort_values(by='count', ascending=False)
        st.write("#### Attack Types — Distribution")
        
        # use Plotly bar for interactivity
        try:
            fig = px.bar(attack_counts, x='attack_type', y='count', text='count', 
                        title="Attack Types Frequency")
            fig.update_layout(xaxis_title='attack_type', yaxis_title='count', 
                            template='plotly_dark', height=420)
            st.plotly_chart(fig, use_container_width=True)
        except Exception:
            st.bar_chart(attack_counts.set_index('attack_type')['count'])
        
        # Attack Insights table: show one row per attack type with summary
        st.write("#### Attack Summary Table")
        rows = []
        for _, r in attack_counts.iterrows():
            at = r['attack_type']
            cnt = int(r['count'])
            recs = get_recommendations(at)
            description = recs.get('description', 'No description available')
            rows.append({
                "Attack Type": at.upper(), 
                "Count": cnt, 
                "Summary": description[:80] + "..."
            })
        insights_df = pd.DataFrame(rows)
        st.dataframe(insights_df, use_container_width=True, height=200)
        
        # Interactive deep-dive: full recommendations for selected attack type
        st.write("#### 🎯 Detailed Response & Remediation")
        attack_choice = st.selectbox(
            "Select attack type to view full remediation steps:",
            options=attack_counts['attack_type'].tolist(),
            index=0,
            key="attack_selector"
        )
        
        if attack_choice:
            recs = get_recommendations(attack_choice)
            cnt_val = int(attack_counts.loc[attack_counts['attack_type']==attack_choice, 'count'].iloc[0])
            
            st.markdown(f"### {recs.get('title', attack_choice)}")
            st.markdown(f"**Sessions:** {cnt_val} | **Severity:** {recs.get('severity', 'Unknown')}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**What happened:**")
                st.info(recs.get('description', 'No description'))
            with col2:
                st.markdown("**How attacker got in:**")
                st.warning(recs.get('how_got_in', 'Unknown'))
            
            st.markdown("---")
            st.markdown("#### 🔧 Remediation Steps")
            for i, action in enumerate(recs.get('actions', []), 1):
                with st.expander(f"{i}. {action.get('priority', 'MED')} - {action.get('title', 'Action')}"):
                    st.write(f"**Description:** {action.get('description', '')}")
                    if action.get('commands'):
                        st.code("\n".join(action['commands']), language="bash")
                    st.write(f"*{action.get('why', '')}*")
            
            # Download button for checklist
            checklist_text = f"""INCIDENT RESPONSE CHECKLIST
Attack Type: {attack_choice.upper()}
Sessions Affected: {cnt_val}
Generated: {datetime.now().isoformat()}

{recs.get('title', '')}
{recs.get('description', '')}

Remediation Steps:
"""
            for i, action in enumerate(recs.get('actions', []), 1):
                checkbox = "[ ]"
                checklist_text += f"\n{i}. {checkbox} {action.get('title', '')}\n"
                if action.get('commands'):
                    checklist_text += f"   Commands:\n"
                    for cmd in action['commands']:
                        checklist_text += f"   $ {cmd}\n"
            
            st.download_button(
                "📥 Download Checklist",
                checklist_text,
                file_name=f"remediation_{attack_choice}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )

with tabs[5]:
    st.dataframe(df.head(500), use_container_width=True)

st.markdown("---")
st.write("Tip: For live data, ensure per-VM instances write into 'data/sessions/<inst>/' and run the aggregator to produce 'output/honeypot_sessions.csv'. The dashboard watches that CSV and reloads automatically.")
