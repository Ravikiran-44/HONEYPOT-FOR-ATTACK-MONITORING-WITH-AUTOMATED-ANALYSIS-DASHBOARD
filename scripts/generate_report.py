# generate_reports.py
"""
Generate honeypot graphs + "clear" Excel export from a normalized session CSV.
Usage:
  python generate_reports.py --input "C:\project\data\sessions.csv" --outdir "C:\project\out"
If no --input provided, tries default path "C:\project\data\sessions.csv"
Outputs:
  <outdir>/graphs/*.png
  <outdir>/honeypot_export_clear.xlsx
  <outdir>/aggregated_by_srcip.csv
"""

import argparse
import os
from pathlib import Path
import pandas as pd
import numpy as np
from io import BytesIO
import matplotlib
matplotlib.use('Agg')  # headless backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import networkx as nx
from datetime import datetime
import xlsxwriter

# ----------------------------
# Helpers (same behavior as Streamlit)
# ----------------------------
def safe_parse_df(df):
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    else:
        df['timestamp'] = pd.NaT
    # Ensure list of useful columns
    cols = ['session_id','src_ip','dst_port','attack_type','success','bytes_in','bytes_out','src_country','src_asn','payload_hash','transcript','username','password','dst_ip','files_dropped','failed_auth','payload_entropy','unique_uri']
    for c in cols:
        if c not in df.columns:
            df[c] = np.nan
    # numeric casts
    df['dst_port'] = pd.to_numeric(df['dst_port'], errors='coerce').fillna(-1).astype(int)
    df['success'] = df['success'].fillna(0).astype(int)
    df['bytes_in'] = pd.to_numeric(df['bytes_in'], errors='coerce').fillna(0).astype(int)
    df['bytes_out'] = pd.to_numeric(df['bytes_out'], errors='coerce').fillna(0).astype(int)
    if 'transcript' in df.columns:
        df['transcript_preview'] = df['transcript'].astype(str).str.slice(0,300)
    else:
        df['transcript_preview'] = ""
    return df

# ----------------------------
# Plot functions (headless)
# ----------------------------
def ensure_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)

def save_fig(fig, outpath):
    fig.savefig(outpath, bbox_inches='tight')
    plt.close(fig)

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
        payload = f"HASH:{r.get('payload_hash','')}" if 'payload_hash' in r else None
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

# ----------------------------
# Excel builder
# ----------------------------
def build_excel_bytes(df):
    dfc = safe_parse_df(df.copy())
    # compute simple threat_score (rule-based)
    for c in ['failed_auth','payload_entropy','unique_uri']:
        if c not in dfc.columns:
            dfc[c] = 0
    def compute_rule_boost_row(r):
        boost = 0.0
        try:
            if int(r.get('dst_port', -1)) == 22 and int(r.get('failed_auth', 0)) >= 10:
                boost += 20.0
        except:
            pass
        if float(r.get('bytes_in', 0)) > 10000 and float(r.get('payload_entropy', 0)) > 7:
            boost += 25.0
        if int(r.get('unique_uri', 0)) > 100:
            boost += 10.0
        return min(boost, 30.0)
    dfc['rule_boost'] = dfc.apply(compute_rule_boost_row, axis=1)
    dfc['pred_confidence'] = 0.0
    dfc['threat_score'] = (dfc['pred_confidence'] * 70) + dfc['rule_boost']
    dfc['threat_score'] = dfc['threat_score'].clip(0,100).round(1)

    agg = dfc.groupby(['src_ip','src_country','src_asn','attack_type'], dropna=False).agg(
        sessions=('session_id','nunique'),
        first_seen=('timestamp','min'),
        last_seen=('timestamp','max'),
        bytes_in_sum=('bytes_in','sum'),
        bytes_out_sum=('bytes_out','sum'),
        avg_threat_score=('threat_score','mean')
    ).reset_index()

    top_alerts = dfc.sort_values('threat_score', ascending=False).head(200)

    summary = {
        "total_sessions": len(dfc),
        "unique_src_ips": int(dfc['src_ip'].nunique()),
        "unique_asns": int(dfc.get('src_asn', pd.Series()).nunique()) if 'src_asn' in dfc.columns else 0,
        "distinct_attack_types": int(dfc['attack_type'].nunique()),
        "max_threat_score": float(dfc['threat_score'].max())
    }
    summary_df = pd.DataFrame([summary])

    # Excel bytes
    out = BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
        cols_order = ['session_id','timestamp','src_ip','src_country','src_asn','dst_ip','dst_port','protocol','username','password','attack_type','success','bytes_in','bytes_out','files_dropped','payload_hash','transcript','transcript_preview','failed_auth','unique_uri','payload_entropy','rule_boost','threat_score']
        cols_existing = [c for c in cols_order if c in dfc.columns]
        dfc.to_excel(writer, sheet_name='Raw_Clean', index=False, columns=cols_existing)
        agg.to_excel(writer, sheet_name='Aggregated_By_SrcIP', index=False)
        top_alerts.to_excel(writer, sheet_name='Top_Alerts', index=False)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        writer.save()
    out.seek(0)
    return out.read(), agg, dfc

# ----------------------------
# Main runner
# ----------------------------
def generate_reports(input_csv, outdir, top_n_ips=25, time_freq='H'):
    input_csv = Path(input_csv)
    outdir = Path(outdir)
    ensure_dir(outdir)
    graphs_dir = outdir / 'graphs'
    ensure_dir(graphs_dir)

    if not input_csv.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")

    df = pd.read_csv(input_csv, parse_dates=['timestamp'], infer_datetime_format=True)
    df = safe_parse_df(df)
    # Produce graphs
    figs = []
    figs.append((top_n_bar(df, 'src_ip', n=10, title="Top 10 Attacker IP addresses"), 'plot_top10_src_ip.png'))
    if 'username' in df.columns:
        figs.append((top_n_bar(df, 'username', n=10, title="Top 10 Usernames Attempted"), 'plot_top10_usernames.png'))
    figs.append((top_n_bar(df, 'dst_port', n=20, title="Most Probed Destination Ports"), 'plot_top_ports.png'))
    figs.append((attack_type_freq(df), 'plot_attack_types.png'))
    figs.append((pie_attack_types(df), 'plot_attack_types_pie.png'))
    figs.append((time_series_volume(df.copy(), time_col='timestamp', freq=time_freq), f'plot_timeseries_{time_freq}.png'))
    hm = heatmap_ip_port(df.copy(), top_n=top_n_ips)
    if hm is not None:
        figs.append((hm, 'plot_heatmap_ip_port.png'))
    pm = port_scan_matrix(df.copy(), top_n=top_n_ips)
    if pm is not None:
        figs.append((pm, 'plot_port_scan_matrix.png'))
    netg = network_graph(df.copy(), top_src=40)
    if netg is not None:
        figs.append((netg, 'plot_network_graph.png'))
    cmdg = command_sequence_analysis(df.copy(), top_n=30)
    if cmdg is not None:
        figs.append((cmdg, 'plot_command_sequences.png'))
    countryg = country_distribution(df.copy(), top_n=20)
    if countryg is not None:
        figs.append((countryg, 'plot_country_dist.png'))

    # Save figures
    for fig, name in figs:
        save_fig(fig, graphs_dir / name)

    # Build excel and save other outputs
    excel_bytes, agg, df_clean = build_excel_bytes(df)
    with open(outdir / 'honeypot_export_clear.xlsx', 'wb') as f:
        f.write(excel_bytes)
    agg.to_csv(outdir / 'aggregated_by_srcip.csv', index=False)
    # Also save cleaned raw
    df_clean.to_csv(outdir / 'raw_clean.csv', index=False)

    return {
        'graphs_dir': str(graphs_dir),
        'excel_path': str(outdir / 'honeypot_export_clear.xlsx'),
        'aggregated_csv': str(outdir / 'aggregated_by_srcip.csv'),
        'raw_clean_csv': str(outdir / 'raw_clean.csv')
    }

# ----------------------------
# CLI
# ----------------------------
if __name__ == '__main__':
    p = argparse.ArgumentParser(description="Generate honeypot graphs + Excel from CSV")
    p.add_argument('--input', '-i', type=str, default=r"C:\project\data\sessions.csv", help="Input CSV path")
    p.add_argument('--outdir', '-o', type=str, default=r"C:\project\out", help="Output directory")
    p.add_argument('--top-n-ips', type=int, default=25)
    p.add_argument('--time-freq', type=str, default='H')
    args = p.parse_args()
    print("Reading:", args.input)
    out = generate_reports(args.input, args.outdir, top_n_ips=args.top_n_ips, time_freq=args.time_freq)
    print("Generated:", out)
