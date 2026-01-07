# generate_excel_helper.py
from io import BytesIO
import pandas as pd
from pathlib import Path
import xlsxwriter
import numpy as np
import json
from advisor import ATTACK_ADVICE

def compute_simple_threat_score_row(row):
    score = 0.0
    hits = []
    pred_prob = float(row.get('pred_prob') or 0)
    score += pred_prob * 70.0
    try:
        dport = int(row.get('dst_port') or 0)
    except Exception:
        dport = 0
    try:
        failed = int(row.get('failed_auth') or 0)
    except Exception:
        failed = 0
    entropy = float(row.get('payload_entropy') or 0)
    bytes_in = float(row.get('bytes_in') or 0)
    unique_uri = int(row.get('unique_uri') or 0)
    if dport == 22 and failed >= 10:
        score += 20.0; hits.append('ssh_bruteforce_rule')
    if entropy > 7.0 and bytes_in > 10000:
        score += 25.0; hits.append('high_entropy_large_bytes')
    if unique_uri > 100:
        score += 10.0; hits.append('massive_unique_uri_scanner')
    score = min(100.0, score)
    return round(score,1), ";".join(hits), round(pred_prob,3)

def generate_clean_excel_bytes(df, top_n_lists=50, alert_threshold=70.0, disk_fallback=True, disk_path='output/clean_honeypot_report.xlsx'):
    """
    Build a multi-sheet Excel workbook and return its bytes.
    If dataset is large (>100k rows) and disk_fallback=True, write to disk and return file bytes.
    """
    d = df.copy()

    # normalize column names
    if 'datetime' in d.columns and 'timestamp' not in d.columns:
        d.rename(columns={'datetime':'timestamp'}, inplace=True)

    # Ensure columns exist
    cols = ['session_id','timestamp','host','src_ip','src_str','src_asn','src_country',
            'dst_ip','dst_port','protocol','attack_type','username','password','success',
            'bytes_in','bytes_out','files_dropped','payload_hash','transcript',
            'latitude','longitude','locale','postalcode','failed_auth','payload_entropy','unique_uri']
    for c in cols:
        if c not in d.columns:
            d[c] = None

    # Best-effort timestamp normalization
    def to_iso(x):
        try:
            ts = pd.to_datetime(x)
            return ts.isoformat()
        except Exception:
            return None
    d['timestamp'] = d['timestamp'].apply(to_iso)

    raw_cols = ['session_id','timestamp','host','src_ip','src_str','src_asn','src_country',
                'dst_ip','dst_port','protocol','attack_type','username','password','success',
                'bytes_in','bytes_out','files_dropped','payload_hash','transcript',
                'latitude','longitude','locale','postalcode']
    raw_events = d[raw_cols].copy()

    # BY_SRCIP aggregation
    agg = d.groupby(['src_ip','src_country','src_asn'], dropna=False).agg(
        sessions=('session_id','nunique'),
        first_seen=('timestamp','min'),
        last_seen=('timestamp','max'),
        unique_attack_types=('attack_type', lambda x: ",".join(sorted(set([str(i) for i in x if pd.notna(i)])))),
        bytes_in_sum=('bytes_in', lambda x: pd.to_numeric(x, errors='coerce').sum(skipna=True)),
        bytes_out_sum=('bytes_out', lambda x: pd.to_numeric(x, errors='coerce').sum(skipna=True)),
        files_dropped_sum=('files_dropped', lambda x: pd.to_numeric(x, errors='coerce').sum(skipna=True))
    ).reset_index()

    # Top lists
    def top_series(series, n=top_n_lists):
        return series.fillna('NULL').astype(str).value_counts().head(n).reset_index().rename(columns={'index':'value', 0:'count'})

    top_src_ips = top_series(d['src_ip'])
    top_usernames = top_series(d.get('username', pd.Series(dtype=str)))
    top_passwords = top_series(d.get('password', pd.Series(dtype=str)))
    top_ports = top_series(d['dst_port'])
    top_asns = top_series(d.get('src_asn', pd.Series(dtype=str)))
    top_countries = top_series(d.get('src_country', pd.Series(dtype=str)))

    # GEO summary
    geo = d.groupby('src_country', dropna=False).agg(
        sessions=('session_id','nunique'),
        unique_src_ips=('src_ip', lambda x: x.nunique()),
        bytes_in_sum=('bytes_in', lambda x: pd.to_numeric(x, errors='coerce').sum(skipna=True)),
        bytes_out_sum=('bytes_out', lambda x: pd.to_numeric(x, errors='coerce').sum(skipna=True)),
        first_seen=('timestamp','min'),
        last_seen=('timestamp','max')
    ).reset_index()

    # ALERTS: compute threat_score if necessary
    if 'threat_score' not in d.columns or d['threat_score'].isnull().all():
        tups = d.apply(lambda r: compute_simple_threat_score_row(r), axis=1)
        d[['threat_score','rule_hits','pred_prob']] = pd.DataFrame(tups.tolist(), index=d.index)
    else:
        if 'rule_hits' not in d.columns:
            d['rule_hits'] = d.get('rule_hits', '')
        if 'pred_prob' not in d.columns:
            d['pred_prob'] = d.get('pred_prob', 0.0)

    alerts = d.loc[pd.to_numeric(d['threat_score'], errors='coerce').fillna(0) >= alert_threshold, [
        'session_id','timestamp','src_ip','src_asn','attack_type','threat_score','rule_hits','pred_prob','bytes_in','files_dropped','transcript'
    ]].sort_values('threat_score', ascending=False)

    # If big and disk fallback enabled -> write to disk
    if disk_fallback and len(d) > 100000:
        Path(disk_path).parent.mkdir(parents=True, exist_ok=True)
        with pd.ExcelWriter(disk_path, engine='xlsxwriter', options={'strings_to_numbers': True}) as writer:
            raw_events.to_excel(writer, sheet_name='RAW_EVENTS', index=False)
            agg.to_excel(writer, sheet_name='BY_SRCIP', index=False)
            workbook = writer.book
            ws = workbook.add_worksheet('TOP_LISTS')
            writer.sheets['TOP_LISTS'] = ws
            startrow = 0
            def write_small(df_small, title, startrow):
                hdr = workbook.add_format({'bold':True,'bg_color':'#D9E1F2'})
                ws.write(startrow, 0, title, hdr)
                for ci, col in enumerate(df_small.columns):
                    ws.write(startrow+1, ci, col, hdr)
                for r, rowvals in enumerate(df_small.values):
                    for c, val in enumerate(rowvals):
                        ws.write(startrow+2+r, c, val)
                return startrow + 2 + len(df_small) + 2
            startrow = write_small(top_src_ips, 'Top source IPs', startrow)
            startrow = write_small(top_usernames, 'Top usernames attempted', startrow)
            startrow = write_small(top_passwords, 'Top passwords attempted', startrow)
            startrow = write_small(top_ports, 'Top destination ports', startrow)
            startrow = write_small(top_asns, 'Top ASNs', startrow)
            startrow = write_small(top_countries, 'Top source countries', startrow)
            geo.to_excel(writer, sheet_name='GEO_SUMMARY', index=False)
            alerts.to_excel(writer, sheet_name='ALERTS', index=False)

            # freeze & autofilter & conditional formatting
            for sheetname, df_sheet in [('RAW_EVENTS', raw_events), ('BY_SRCIP', agg), ('GEO_SUMMARY', geo), ('ALERTS', alerts)]:
                try:
                    ws2 = writer.sheets[sheetname]
                    ws2.freeze_panes(1,0)
                    ws2.autofilter(0, 0, len(df_sheet), max(1, len(df_sheet.columns)-1))
                except Exception:
                    pass
            # conditional formatting on ALERTS threat_score
            try:
                ws_alerts = writer.sheets['ALERTS']
                try:
                    col_idx = list(alerts.columns).index('threat_score')
                except ValueError:
                    col_idx = 5
                col_letter = xlsxwriter.utility.xl_col_to_name(col_idx)
                last_row = 1 + max(1, len(alerts))
                rng = f"{col_letter}2:{col_letter}{last_row+0}"
                ws_alerts.conditional_format(rng, {'type':'3_color_scale',
                                                   'min_color': '#63BE7B',
                                                   'mid_color': '#FFEB84',
                                                   'max_color': '#F8696B'})
            except Exception:
                pass
        return Path(disk_path).read_bytes()

    # small/medium dataset -> in-memory write
    out = BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter', datetime_format='yyyy-mm-ddThh:mm:ss', date_format='yyyy-mm-dd') as writer:
        raw_events.to_excel(writer, sheet_name='RAW_EVENTS', index=False)
        agg.to_excel(writer, sheet_name='BY_SRCIP', index=False)
        workbook = writer.book
        ws = workbook.add_worksheet('TOP_LISTS')
        writer.sheets['TOP_LISTS'] = ws
        startrow = 0
        def write_small(df_small, title, startrow):
            hdr = workbook.add_format({'bold':True,'bg_color':'#D9E1F2'})
            ws.write(startrow, 0, title, hdr)
            for ci, col in enumerate(df_small.columns):
                ws.write(startrow+1, ci, col, hdr)
            for r, rowvals in enumerate(df_small.values):
                for c, val in enumerate(rowvals):
                    ws.write(startrow+2+r, c, val)
            return startrow + 2 + len(df_small) + 2
        startrow = write_small(top_src_ips, 'Top source IPs', startrow)
        startrow = write_small(top_usernames, 'Top usernames attempted', startrow)
        startrow = write_small(top_passwords, 'Top passwords attempted', startrow)
        startrow = write_small(top_ports, 'Top destination ports', startrow)
        startrow = write_small(top_asns, 'Top ASNs', startrow)
        startrow = write_small(top_countries, 'Top source countries', startrow)
        geo.to_excel(writer, sheet_name='GEO_SUMMARY', index=False)
        alerts.to_excel(writer, sheet_name='ALERTS', index=False)

        for sheetname, df_sheet in [('RAW_EVENTS', raw_events), ('BY_SRCIP', agg), ('GEO_SUMMARY', geo), ('ALERTS', alerts)]:
            try:
                ws2 = writer.sheets[sheetname]
                for i, col in enumerate(df_sheet.columns):
                    col_vals = df_sheet[col].astype(str).fillna('')
                    max_len = max(col_vals.map(len).max(), len(col)) + 2
                    ws2.set_column(i, i, min(max_len, 60))
                ws2.freeze_panes(1,0)
                ws2.autofilter(0, 0, len(df_sheet), max(1, len(df_sheet.columns)-1))
            except Exception:
                pass

        # conditional formatting on ALERTS
        try:
            ws_alerts = writer.sheets['ALERTS']
            try:
                col_idx = list(alerts.columns).index('threat_score')
            except ValueError:
                col_idx = 5
            col_letter = xlsxwriter.utility.xl_col_to_name(col_idx)
            last_row = 1 + max(1, len(alerts))
            rng = f"{col_letter}2:{col_letter}{last_row+0}"
            ws_alerts.conditional_format(rng, {'type':'3_color_scale',
                                               'min_color': '#63BE7B',
                                               'mid_color': '#FFEB84',
                                               'max_color': '#F8696B'})
        except Exception:
            pass

    # Add defense recommendations sheet
    recs = []
    for atk, info in ATTACK_ADVICE.items():
        recs.append({
            "attack_type": atk,
            "description": info["description"],
            "how_attacker_got_in": info["how_attacker_got_in"],
            "recommendations": " | ".join(info["recommendations"])
        })
    recs_df = pd.DataFrame(recs)
    recs_df.to_excel(writer, sheet_name='DEFENSE_RECOMMENDATIONS', index=False)
    
    # Set column widths for readability
    worksheet = writer.sheets['DEFENSE_RECOMMENDATIONS']
    worksheet.set_column('A:A', 15)  # attack_type
    worksheet.set_column('B:B', 40)  # description
    worksheet.set_column('C:C', 40)  # how_attacker_got_in
    worksheet.set_column('D:D', 60)  # recommendations

    out.seek(0)
    return out.getvalue()