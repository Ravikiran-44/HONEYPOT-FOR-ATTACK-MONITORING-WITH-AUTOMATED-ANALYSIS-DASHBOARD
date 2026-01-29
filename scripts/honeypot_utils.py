import re
import pandas as pd
import numpy as np
import plotly.express as px
from typing import Optional

# Normalizer for multiple honeypot schemas + Top Ports plot
# Extracted from app_auto.py to be testable independently

def normalize_honeypot_data(df: Optional[pd.DataFrame]) -> Optional[pd.DataFrame]:
    """
    Normalize a variety of honeypot CSV schemas into canonical columns used by the app.
    Returns a cleaned dataframe with canonical columns where possible.
    """
    if df is None:
        return df

    df = df.copy()
    df.columns = [c.strip() for c in df.columns]
    lowermap = {c.lower(): c for c in df.columns}
    rename_map = {}

    # IPs
    for cand in ("src","src_ip","source_ip","source","saddr","ip_src"):
        if cand in lowermap:
            rename_map[lowermap[cand]] = "src_ip"
            break
    for cand in ("dst","dst_ip","destination_ip","dest_ip","daddr","ip_dst"):
        if cand in lowermap:
            rename_map[lowermap[cand]] = "dst_ip"
            break

    # ports
    for cand in ("dst_port","dpt","dest_port","destination_port","dstport","destport","port","destination"):
        if cand in lowermap:
            rename_map[lowermap[cand]] = "dst_port"
            break
    for cand in ("src_port","spt","sport","source_port"):
        if cand in lowermap:
            rename_map[lowermap[cand]] = "src_port"
            break

    # other fields
    for cand in ("proto","protocol"):
        if cand in lowermap:
            rename_map[lowermap[cand]] = "protocol"
            break
    for cand in ("type","attack_type","event_type"):
        if cand in lowermap:
            rename_map[lowermap[cand]] = "attack_type"
            break
    for cand in ("time","timestamp","datetime"):
        if cand in lowermap:
            rename_map[lowermap[cand]] = "timestamp"
            break
    for cand in ("user","username","usr"):
        if cand in lowermap:
            rename_map[lowermap[cand]] = "username"
            break
    for cand in ("pass","password","pwd"):
        if cand in lowermap:
            rename_map[lowermap[cand]] = "password"
            break
    for cand in ("bytes_in","bytesin","rx_bytes","bytes_received"):
        if cand in lowermap:
            rename_map[lowermap[cand]] = "bytes_in"
            break
    for cand in ("bytes_out","bytesout","tx_bytes","bytes_sent"):
        if cand in lowermap:
            rename_map[lowermap[cand]] = "bytes_out"
            break
    for cand in ("payload_hash","hash","file_hash","sha256"):
        if cand in lowermap:
            rename_map[lowermap[cand]] = "payload_hash"
            break

    if rename_map:
        df = df.rename(columns=rename_map)

    # Helper: try extract port from string
    port_re = re.compile(r"(?:(?:[:/]|port=)\s*|^)(\d{1,5})(?:\D|$)")
    def extract_port(val):
        if pd.isna(val):
            return None
        try:
            if isinstance(val, (int, float)) and not np.isnan(val):
                return int(val)
            s = str(val)
            if "," in s and s.split(",")[0].strip().isdigit():
                return int(s.split(",")[0].strip())
            if s.isdigit():
                return int(s)
            m = port_re.search(s)
            if m:
                p = int(m.group(1))
                if 0 < p < 65536:
                    return p
        except Exception:
            return None
        return None

    # stricter extractor to avoid capturing IP octets when filling
    strict_port_re = re.compile(r"(?:(?:[:/]|port=)\s*)(\d{1,5})(?:\D|$)")
    def extract_port_strict(val):
        if pd.isna(val):
            return None
        try:
            s = str(val)
            m = strict_port_re.search(s)
            if m:
                p = int(m.group(1))
                if 0 < p < 65536:
                    return p
        except Exception:
            return None
        return None

    # If there is no dst_port column but there's a generic 'service' or 'uri', attempt to parse
    if "dst_port" not in df.columns:
        for cand in ("service","connection","endpoint","dst"):
            if cand in df.columns:
                df["dst_port"] = df[cand].apply(extract_port)
                break

    if "dst_port" in df.columns:
        df["dst_port"] = df["dst_port"].apply(extract_port)
        if df["dst_port"].isna().any():
            for cand in ("dst_ip","service","connection","endpoint","destination","dst"):
                if cand in df.columns:
                    try:
                        df["dst_port"] = df["dst_port"].fillna(df[cand].apply(extract_port_strict))
                    except Exception:
                        pass
        df["dst_port"] = pd.to_numeric(df["dst_port"], errors="coerce").astype("Int64")

    if "src_port" in df.columns:
        df["src_port"] = df["src_port"].apply(extract_port)
        df["src_port"] = pd.to_numeric(df["src_port"], errors="coerce").astype("Int64")

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    if "attack_type" in df.columns:
        df["attack_type"] = df["attack_type"].astype(str).str.lower().str.replace(r"\s+","_", regex=True)

    if "src_ip" not in df.columns:
        for cand in ("src","source","saddr"):
            if cand in df.columns:
                df = df.rename(columns={cand:"src_ip"})
                break
    if "dst_ip" not in df.columns:
        for cand in ("dst","destination","daddr"):
            if cand in df.columns:
                df = df.rename(columns={cand:"dst_ip"})
                break

    for ipcol in ("src_ip","dst_ip"):
        if ipcol in df.columns:
            df[ipcol] = df[ipcol].astype(str).str.strip().replace({"nan": None, "None": None})

    return df


def plot_top_ports(df: Optional[pd.DataFrame], n: int = 20, height: int = 360):
    """Return a Plotly bar Figure of top destination ports (uses canonical dst_port)."""
    if df is None:
        return None
    if "dst_port" not in df.columns:
        return None
    ports = df["dst_port"].dropna().astype(int)
    if ports.empty:
        return None
    s = ports.value_counts().head(n).reset_index()
    s.columns = ["dst_port","count"]
    fig = px.bar(s.sort_values("count", ascending=False), x="dst_port", y="count", title=f"Top {n} Destination Ports", height=height)
    fig.update_layout(xaxis_title="dst_port", yaxis_title="count", template="plotly_dark")
    return fig
