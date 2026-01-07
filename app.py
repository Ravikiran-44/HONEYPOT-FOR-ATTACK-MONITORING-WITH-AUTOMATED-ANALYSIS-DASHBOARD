#!/usr/bin/env python3
# app.py
"""
Streamlit Honeypot Dashboard + Excel exporter
- Upload a normalized honeypot CSV or use fallback file: /mnt/data/AWS_Honeypot_marx-geo.csv
- Displays raw table + automated graphs
- Provides a one-click multi-sheet Excel export ("clear" sheet + aggregates + alerts)
"""

import streamlit as st
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import networkx as nx
from pathlib import Path
from io import BytesIO
from datetime import datetime
import ipaddress
import base64
import os

st.set_page_config(layout="wide", page_title="Honeypot Auto-Graphs + Excel Export")

# Add refresh button in sidebar
with st.sidebar:
    st.write("## Live Honeypot Graphs")
    if st.button("🔄 Refresh Graphs"):
        st.rerun()  # This will refresh the entire app
    
    # Check for generated graphs
    graphs_dir = Path(__file__).resolve().parent / "out" / "graphs"
    if graphs_dir.exists():
        graph_files = sorted(graphs_dir.glob("*.png"))
        if graph_files:
            st.write("### Latest Generated Graphs")
            for g in graph_files:
                st.image(str(g), caption=g.stem.replace("plot_", "").replace("_", " ").title())
        else:
            st.info("No graphs generated yet. They will appear here after honeypot sessions.")
    else:
        st.info("Waiting for first honeypot session...")

# ---------------------------
# Configuration defaults
# ---------------------------
import pandas as pd
import streamlit as st
from pathlib import Path

# Constants
FALLBACK_CSV_PATH = "/mnt/data/AWS_Honeypot_marx-geo.csv"  # example file provided
DEFAULT_TOP_N_IPS = 25
DEFAULT_TIME_FREQ = "H"  # H=hour D=day

# ---------------------------
# helper functions
# ---------------------------
def safe_parse_df(df):
    # Ensure column names exist and normalize types
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    else:
        df['timestamp'] = pd.NaT
    for col in ['session_id','src_ip','dst_port','attack_type','success','bytes_in','bytes_out','src_country','src_asn','payload_hash','transcript','username','password','dst_ip','files_dropped']:
        if col not in df.columns:
            df[col] = np.nan
    # Try cast numeric
    df['dst_port'] = pd.to_numeric(df['dst_port'], errors='coerce').fillna(-1).astype(int)
    df['success'] = df['success'].fillna(0).astype(int)
    if 'bytes_in' in df.columns:
        df['bytes_in'] = pd.to_numeric(df['bytes_in'], errors='coerce').fillna(0).astype(int)
    else:
        df['bytes_in'] = 0
    if 'bytes_out' in df.columns:
        df['bytes_out'] = pd.to_numeric(df['bytes_out'], errors='coerce').fillna(0).astype(int)
    else:
        df['bytes_out'] = 0
    # Shorten long text fields for display
    if 'transcript' in df.columns:
        df['transcript_preview'] = df['transcript'].astype(str).str.slice(0,300)
    else:
        df['transcript_preview'] = ""
    return df

def rand_ipv4():
    while True:
        # use a safe 24-bit range for random IPv4 to avoid numpy int32 overflow
        ip = ipaddress.IPv4Address(np.random.randint(1, 0xFFFFFF))
        s = str(ip)
        if not (s.startswith("10.") or s.startswith("192.168.") or s.startswith("172.")):
            return s

# fallback demo generator only if fallback file is missing
def generate_demo(n=1000):
    attack_types = ['ssh_bruteforce', 'web_scan', 'exploit', 'malware_drop', 'benign']
    probs = [0.25, 0.30, 0.10, 0.10, 0.25]
    rows = []
    for i in range(n):
        ts = datetime.now() - pd.to_timedelta(np.random.randint(0,30*24*3600), unit='s')
        label = np.random.choice(attack_types, p=probs)
        rows.append({
            "session_id": f"demo_{i}",
            "timestamp": ts,
            "src_ip": rand_ipv4(),
            "src_country": np.random.choice(['CN','US','RU','IN','BR','DE','UNKNOWN']),
            "src_asn": f"AS{1000 + np.random.randint(1,200)}",
            "dst_ip": "10.0.0.5",
            "dst_port": int(np.random.choice([22,80,443,8080,23,3389,445,21])),
            "protocol": "tcp",
            "username": np.random.choice(['root','admin','user','NULL']),
            "password": np.random.choice(['1234','password','NULL']),
            "attack_type": label,
            "success": int(np.random.rand() < 0.02),
            "bytes_in": int(np.random.randint(0,100000)),
            "bytes_out": int(np.random.randint(0,100000)),
            "payload_hash": "" ,
            "files_dropped": 0,
            "transcript": "demo"
        })
    return pd.DataFrame(rows)

# ---------------------------
# Plot helpers (return matplotlib Figure)
# ---------------------------
def top_n_bar(df, col, n=10, title=None):
    s = df[col].fillna('NULL').value_counts().head(n)
    fig, ax = plt.subplots(figsize=(8,4))
    ax.bar(s.index.astype(str), s.values)
    ax.set_title(title or f"Top {n} by {col}")
    ax.set_ylabel("Count")
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
    return fig

def attack_type_freq(df):
    s = df['attack_type'].fillna('unknown').value_counts()
    fig, ax = plt.subplots(figsize=(8,4))
    ax.bar(s.index.astype(str), s.values)
    ax.set_title("Attack Types Frequency")
    ax.set_ylabel("Count")
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
    return fig

def success_ratio(df, groupby=None):
    if groupby is None:
        grp = df.groupby('success').size()
        labels = ['failed','success']
        vals = [grp.get(0,0), grp.get(1,0)]
        fig, ax = plt.subplots(figsize=(6,4))
        ax.bar(labels, vals)
        ax.set_title("Success vs Failed (overall)")
        ax.set_ylabel("Count")
        return fig
    else:
        grp = df.groupby([groupby, 'success']).size().unstack(fill_value=0)
        fig, ax = plt.subplots(figsize=(10,4))
        grp.plot(kind='bar', stacked=True, ax=ax)
        ax.set_title(f"Success vs Failed by {groupby}")
        return fig

def time_series_volume(df, time_col='timestamp', freq='H'):
    df = df.set_index(pd.to_datetime(df[time_col]))
    counts = df.resample(freq).size()
    fig, ax = plt.subplots(figsize=(10,3))
    ax.plot(counts.index, counts.values)
    ax.set_title(f"Sessions per {freq}")
    ax.set_ylabel("Sessions")
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
    return fig

def pie_attack_types(df):
    s = df['attack_type'].fillna('unknown').value_counts()
    fig, ax = plt.subplots(figsize=(6,6))
    ax.pie(s.values, labels=s.index.astype(str), autopct='%1.1f%%')
    ax.set_title("Attack Type Distribution")
    return fig

def heatmap_ip_port(df, top_n=25):
    top_ips = df['src_ip'].value_counts().head(top_n).index
    pivot = df[df['src_ip'].isin(top_ips)].pivot_table(index='src_ip', columns='dst_port', values='session_id', aggfunc='count', fill_value=0)
    if pivot.shape[0] == 0 or pivot.shape[1] == 0:
        return None
    fig, ax = plt.subplots(figsize=(10, max(4, 0.25 * pivot.shape[0])))
    im = ax.imshow(pivot.values, aspect='auto', interpolation='nearest')
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, rotation=90)
    ax.set_title(f"IP vs Port activity (top {top_n} IPs)")
    plt.colorbar(im, ax=ax)
    return fig

def port_scan_matrix(df, top_n=50):
    top_ips = df['src_ip'].value_counts().head(top_n).index
    pivot = df[df['src_ip'].isin(top_ips)].pivot_table(index='src_ip', columns='dst_port', values='session_id', aggfunc='count', fill_value=0)
    if pivot.shape[0] == 0 or pivot.shape[1] == 0:
        return None
    ports = sorted(pivot.columns)
    pivot = pivot[ports]
    fig, ax = plt.subplots(figsize=(12, max(4, 0.2 * pivot.shape[0])))
    im = ax.imshow((pivot.values > 0).astype(int), aspect='auto', interpolation='nearest')
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, rotation=90)
    ax.set_title("Port scanning (binary) by top source IPs")
    return fig

def network_graph(df, top_src=40):
    G = nx.DiGraph()
    top_srcs = df['src_ip'].value_counts().head(top_src).index
    sub = df[df['src_ip'].isin(top_srcs)].copy()
    for _, r in sub.iterrows():
        src = f"SRC:{r['src_ip']}"
        dst = f"PORT:{r['dst_port']}"
        payload = f"HASH:{r.get('payload_hash','')}`" if 'payload_hash' in r else None
        G.add_node(src, type='src')
        G.add_node(dst, type='port')
        G.add_edge(src, dst, weight=G.get_edge_data(src, dst, {}).get('weight',0)+1)
        if payload and str(payload).strip():
            G.add_node(payload, type='payload')
            G.add_edge(dst, payload, weight=G.get_edge_data(dst, payload, {}).get('weight',0)+1)
    if G.number_of_nodes() == 0:
        return None
    fig = plt.figure(figsize=(12,9))
    pos = nx.spring_layout(G, k=0.5, iterations=50, seed=42)
    degrees = np.array([max(1, G.degree(n)) for n in G.nodes()])
    nx.draw_networkx_nodes(G, pos, node_size=100 + (degrees * 15))
    nx.draw_networkx_edges(G, pos, arrowsize=8, alpha=0.6)
    nx.draw_networkx_labels(G, pos, font_size=6)
    plt.title("Network graph: src_ip -> port -> payload")
    plt.axis('off')
    return fig

def command_sequence_analysis(df, top_n=20):
    if 'transcript' not in df.columns:
        return None
    pairs = {}
    for t in df['transcript'].dropna().astype(str):
        toks = t.split()
        for i in range(len(toks)-1):
            p = (toks[i], toks[i+1])
            pairs[p] = pairs.get(p,0) + 1
    if not pairs:
        return None
    items = sorted(pairs.items(), key=lambda x: x[1], reverse=True)[:top_n]
    labels = [f"{a}->{b}" for (a,b),_ in items]
    vals = [v for _,v in items]
    fig, ax = plt.subplots(figsize=(10, max(2, 0.3*len(labels))))
    ax.barh(labels[::-1], vals[::-1])
    ax.set_title("Top command token pairs (sequence analysis)")
    return fig

def country_distribution(df, top_n=20):
    if 'src_country' not in df.columns or df['src_country'].isna().all():
        return None
    s = df['src_country'].fillna('UNKNOWN').value_counts().head(top_n)
    fig, ax = plt.subplots(figsize=(8,4))
    ax.bar(s.index.astype(str), s.values)
    ax.set_title("Top source countries")
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
    return fig

# ---------------------------
# Excel export builder
# ---------------------------
def build_excel_bytes(df, top_n_ips=25):
    """
    Returns bytes for an Excel file with multiple clear sheets:
    - Raw_Clean: cleaned raw rows (normalized columns)
    - Aggregated_By_SrcIP: aggregated metrics per src_ip
    - Top_Alerts: sessions with top threat_score (we compute naive threat_score)
    - Summary: quick metrics table
    """
    dfc = safe_parse_df(df.copy())

    # simple threat_score heuristic (same idea as before)
    # need numeric features — fallback safe defaults
    dfc['threat_model_prob'] = 0.0  # placeholder (if model present you can fill)
    # rule-based boosts
    def compute_rule_boost_row(r):
        boost = 0.0
        if r['dst_port'] == 22 and r.get('failed_auth', 0) >= 10:
            boost += 20.0
        if float(r.get('bytes_in', 0)) > 10000 and float(r.get('payload_entropy', 0)) > 7:
            boost += 25.0
        if int(r.get('unique_uri', 0)) > 100:
            boost += 10.0
        return min(boost, 30.0)
    # ensure columns exist
    for c in ['failed_auth','payload_entropy','unique_uri']:
        if c not in dfc.columns:
            dfc[c] = 0
    dfc['rule_boost'] = dfc.apply(compute_rule_boost_row, axis=1)
    dfc['pred_confidence'] = dfc['threat_model_prob']
    dfc['threat_score'] = (dfc['pred_confidence'] * 70) + dfc['rule_boost']
    dfc['threat_score'] = dfc['threat_score'].clip(0,100).round(1)

    # Aggregation by src_ip
    agg = dfc.groupby(['src_ip','src_country','src_asn','attack_type'], dropna=False).agg(
        sessions=('session_id','nunique'),
        first_seen=('timestamp','min'),
        last_seen=('timestamp','max'),
        bytes_in_sum=('bytes_in','sum'),
        bytes_out_sum=('bytes_out','sum'),
        avg_threat_score=('threat_score','mean')
    ).reset_index()

    # Top alerts: top threat_score sessions
    top_alerts = dfc.sort_values('threat_score', ascending=False).head(200)

    # Summary metrics (single-row or small table)
    summary = {
        "total_sessions": len(dfc),
        "unique_src_ips": int(dfc['src_ip'].nunique()),
        "unique_asns": int(dfc.get('src_asn', pd.Series()).nunique()) if 'src_asn' in dfc.columns else 0,
        "distinct_attack_types": int(dfc['attack_type'].nunique()),
        "max_threat_score": float(dfc['threat_score'].max())
    }
    summary_df = pd.DataFrame([summary])

    # Build Excel in memory
    out = BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
        # Raw clean sheet: keep a column order that is useful
        cols_order = ['session_id','timestamp','src_ip','src_country','src_asn','dst_ip','dst_port','protocol','username','password','attack_type','success','bytes_in','bytes_out','files_dropped','payload_hash','transcript','transcript_preview','failed_auth','unique_uri','payload_entropy','rule_boost','threat_score']
        cols_existing = [c for c in cols_order if c in dfc.columns]
        # write raw clean
        dfc.to_excel(writer, sheet_name='Raw_Clean', index=False, columns=cols_existing)
        # write aggregated
        agg.to_excel(writer, sheet_name='Aggregated_By_SrcIP', index=False)
        # top alerts
        top_alerts.to_excel(writer, sheet_name='Top_Alerts', index=False)
        # summary
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
    # ExcelWriter context manager will save/close automatically
    out.seek(0)
    return out.read()

# ---------------------------
# Streamlit page
# ---------------------------
def main():
    st.sidebar.header("Input / Options")
    uploaded = st.sidebar.file_uploader("Upload honeypot CSV (one row per session/event)", type=['csv'])
    use_fallback = False
    if uploaded is None:
        if os.path.exists(FALLBACK_CSV_PATH):
            use_fallback = st.sidebar.checkbox("Use fallback example CSV (provided)", value=True)
        else:
            st.sidebar.info("No fallback CSV found. Upload a CSV or use demo generation.")
    use_demo = st.sidebar.checkbox("Use synthetic demo data (only if no upload/fallback)", value=False)

    top_n_ips = st.sidebar.number_input("Top N IPs for IP plots", min_value=5, max_value=500, value=DEFAULT_TOP_N_IPS)
    time_freq = st.sidebar.selectbox("Time aggregation", options=['H','D'], index=0, format_func=lambda x: f"{x} (H=hour, D=day)")
    show_raw = st.sidebar.checkbox("Show raw table", value=True)
    make_excel = st.sidebar.button("Build & Download clear Excel file (.xlsx)")

    # Load dataframe
    if uploaded is not None:
        try:
            df = pd.read_csv(uploaded, parse_dates=['timestamp'], infer_datetime_format=True)
        except Exception as e:
            st.error(f"Failed to read CSV: {e}")
            st.stop()
    elif use_fallback:
        try:
            df = pd.read_csv(FALLBACK_CSV_PATH, parse_dates=['timestamp'], infer_datetime_format=True)
        except Exception as e:
            st.error(f"Failed to read fallback CSV at {FALLBACK_CSV_PATH}: {e}")
            df = generate_demo(1000)
    elif use_demo:
        df = generate_demo(1000)
    else:
        st.warning("No data source selected. Choose upload or fallback/demo options on the left.")
        st.stop()

    df = safe_parse_df(df)

    # Show raw table
    st.title("Honeypot — Raw Data + Auto Graphs + Clear Excel Export")
    st.write("Loaded rows:", len(df))
    if show_raw:
        st.subheader("Raw table (first 500 rows)")
        cols_to_show = st.multiselect("Columns to display (default useful subset)", options=list(df.columns),
                                      default=['session_id','timestamp','src_ip','dst_port','attack_type','success'])
        if cols_to_show:
            st.dataframe(df[cols_to_show].sort_values('timestamp', ascending=False).head(500))
        else:
            st.dataframe(df.sort_values('timestamp', ascending=False).head(500))

    # Quick stats
    col1, col2 = st.columns([1,2])
    with col1:
        st.metric("Total sessions", int(len(df)))
        st.metric("Unique source IPs", int(df['src_ip'].nunique()))
        st.metric("Distinct attack types", int(df['attack_type'].nunique()))
        st.metric("Max threat_score (heuristic)", float(df.get('threat_score', pd.Series([0])).max()))

    with col2:
        st.subheader("Sessions time-series")
        fig_ts = time_series_volume(df.copy(), time_col='timestamp', freq=time_freq)
        st.pyplot(fig_ts)

    # Graph gallery
    st.subheader("Automated Graphs")
    g1, g2 = st.columns(2)
    with g1:
        st.write("Top attacker IPs")
        st.pyplot(top_n_bar(df, 'src_ip', n=10, title="Top 10 Attacker IP addresses"))
        if 'username' in df.columns:
            st.write("Top usernames attempted")
            st.pyplot(top_n_bar(df, 'username', n=10, title="Top 10 Usernames Attempted"))
        st.write("Most probed ports / services")
        st.pyplot(top_n_bar(df, 'dst_port', n=20, title="Most Probed Destination Ports"))
        st.write("Attack Types Frequency")
        st.pyplot(attack_type_freq(df))

    with g2:
        st.write("Attack Type Distribution (pie)")
        st.pyplot(pie_attack_types(df))
        st.write("Success vs Failed (overall)")
        st.pyplot(success_ratio(df, groupby=None))
        if 'protocol' in df.columns:
            st.write("Success vs Failed by protocol")
            st.pyplot(success_ratio(df, groupby='protocol'))
        fig_country = country_distribution(df, top_n=20)
        if fig_country:
            st.pyplot(fig_country)

    st.markdown("---")
    st.subheader("Advanced / forensic visuals")
    adv1, adv2 = st.columns(2)
    with adv1:
        st.write(f"IP vs Port heatmap (top {top_n_ips} IPs)")
        fig_heat = heatmap_ip_port(df.copy(), top_n=top_n_ips)
        if fig_heat:
            st.pyplot(fig_heat)
        else:
            st.info("Not enough data to render heatmap.")
        st.write("Port scanning matrix (binary) — top IPs")
        fig_ps = port_scan_matrix(df.copy(), top_n=top_n_ips)
        if fig_ps:
            st.pyplot(fig_ps)
        else:
            st.info("Not enough data to render port-scan matrix.")

    with adv2:
        st.write("Network graph: source IP → port → payload (limited nodes)")
        fig_net = network_graph(df.copy(), top_src=40)
        if fig_net:
            st.pyplot(fig_net)
        else:
            st.info("No strong relationships found for network graph.")
        st.write("Command sequence token pairs (top pairs)")
        fig_cmd = command_sequence_analysis(df.copy(), top_n=30)
        if fig_cmd:
            st.pyplot(fig_cmd)
        else:
            st.info("No transcripts or insufficient token pairs.")

    # Aggregated CSV displayed (and downloadable)
    st.markdown("---")
    st.subheader("Aggregated summary (by source IP)")
    agg = df.groupby(['src_ip','src_country','src_asn','attack_type'], dropna=False).agg(
            sessions=('session_id','nunique'),
            first_seen=('timestamp','min'),
            last_seen=('timestamp','max'),
            bytes_in_sum=('bytes_in','sum'),
            bytes_out_sum=('bytes_out','sum'),
        ).reset_index()
    st.dataframe(agg.head(200))

    # Build & download Excel
    if make_excel:
        st.info("Building Excel file — this may take a few seconds for big datasets.")
        excel_bytes = build_excel_bytes(df, top_n_ips=top_n_ips)
        b64 = base64.b64encode(excel_bytes).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="honeypot_export_clear.xlsx">Download honeypot_export_clear.xlsx</a>'
        st.markdown(href, unsafe_allow_html=True)
        st.success("Excel ready. It contains sheets: Raw_Clean, Aggregated_By_SrcIP, Top_Alerts, Summary")

    st.markdown("---")
    st.write("Notes & next steps: If you want model-based threat_score injected into the Excel 'threat_score' column, upload your model artifact to the deployment and we will call it during build (I can add that). For very large datasets, pre-aggregate upstream and supply smaller extracts to the app for interactive performance.")


# Run UI unless we're being imported by pytest (tests import app to access helper functions)
if 'pytest' not in sys.modules:
    main()
