import pandas as pd
import pytest
from honeypot_utils import normalize_honeypot_data, plot_top_ports


def test_normalize_extracts_ports_and_columns():
    rows = [
        {"src":"1.2.3.4","dst":"10.0.0.5:2222","service":"tcp/2222","timestamp":"2025-11-10T12:00:00Z"},
        {"saddr":"5.6.7.8","daddr":"10.0.0.6","dpt":"22","timestamp":"2025-11-10T12:01:00Z"},
        {"source_ip":"8.8.8.8","destination":"10.0.0.7:80","port":"80","timestamp":"2025-11-10T12:02:00Z"}
    ]
    df = pd.DataFrame(rows)
    df2 = normalize_honeypot_data(df)

    # canonical columns present
    assert 'src_ip' in df2.columns
    assert 'dst_port' in df2.columns

    # ports extracted correctly
    ports = df2['dst_port'].astype('Int64').tolist()
    # order corresponds to input rows
    assert ports[0] == 2222
    assert ports[1] == 22
    assert ports[2] == 80


def test_plot_top_ports_returns_figure():
    df = pd.DataFrame({'dst_port': [22,22,80,443,443,443,8080]})
    fig = plot_top_ports(df, n=3)
    assert fig is not None
    # Ensure it's a plotly figure by checking for 'data' attribute
    assert hasattr(fig, 'data')
    # We can't rely on 'name' field; instead inspect x/y values
    xs = []
    ys = []
    for trace in fig.data:
        try:
            xs.extend(list(trace.x))
            ys.extend(list(trace.y))
        except Exception:
            pass
    assert 443 in [int(x) for x in xs]
    assert max([int(v) for v in ys]) == 3
