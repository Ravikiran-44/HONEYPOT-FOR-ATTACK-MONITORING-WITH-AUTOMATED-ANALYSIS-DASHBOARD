import pandas as pd
import sys
sys.path.insert(0, '/project')

# Test robust timestamp parsing
from pathlib import Path
df = pd.read_csv('output/honeypot_sessions.csv')

print("=== Before Processing ===")
print(f"end_time sample:\n{df['end_time'].head(3)}")
print(f"start_ts sample:\n{df['start_ts'].head(3)}")

# Simulate what app does
def robust_parse_timestamps(series):
    """Return DatetimeIndex-friendly series with best-effort parsing."""
    if series is None:
        return pd.Series(dtype="datetime64[ns]")
    s = series.copy().astype(str).replace({"nan":"", "None":"", "NaN":""})
    dt = pd.to_datetime(s, errors="coerce")
    need = dt.isna()
    if need.any():
        def parse_num(v):
            try:
                v2 = float(v)
            except Exception:
                return pd.NaT
            if v2 > 1e12:
                return pd.to_datetime(int(v2/1000), unit="s", errors="coerce")
            if v2 > 1e9:
                return pd.to_datetime(int(v2), unit="s", errors="coerce")
            return pd.NaT
        parsed = s[need].map(parse_num)
        dt.loc[need] = parsed.values
    return dt

# Test parsing
ts_parsed = robust_parse_timestamps(df['end_time'])

print("\n=== After robust_parse_timestamps ===")
print(f"Parsed timestamps:\n{ts_parsed.head(3)}")
print(f"\nValid (non-NaT) count: {ts_parsed.notna().sum()}")
print(f"NaT count: {ts_parsed.isna().sum()}")

# Test resampling
df_with_ts = df.copy()
df_with_ts['timestamp'] = ts_parsed
df_with_ts = df_with_ts[df_with_ts['timestamp'].notna()]

if len(df_with_ts) > 0:
    ts_hourly = df_with_ts.set_index('timestamp').resample('h').size().reset_index(name='count')
    print(f"\n=== Hourly Resampling ===")
    print(f"Timeline rows: {len(ts_hourly)}")
    print(f"Timeline:\n{ts_hourly}")
else:
    print("\nNo valid timestamps for timeline")
