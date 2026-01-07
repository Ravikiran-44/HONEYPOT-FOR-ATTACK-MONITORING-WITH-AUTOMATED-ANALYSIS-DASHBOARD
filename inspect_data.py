import pandas as pd
import json

df = pd.read_csv('output/honeypot_sessions.csv')
print("=== DataFrame Info ===")
print(f"Shape: {df.shape}")
print(f"Columns: {list(df.columns)}")
print(f"\n=== First Row ===")
row = df.iloc[0]
for col in df.columns:
    val = row[col]
    if isinstance(val, str) and len(val) > 100:
        print(f"{col}: {val[:100]}...")
    else:
        print(f"{col}: {val}")

print(f"\n=== Timestamp column type ===")
print(f"dtype: {df['start_ts'].dtype}")
print(f"Sample values: {df['start_ts'].head(3).tolist()}")

print(f"\n=== Events column sample ===")
if 'events' in df.columns:
    events_sample = df['events'].iloc[0]
    if isinstance(events_sample, str):
        try:
            parsed = json.loads(events_sample)
            print(f"Type: {type(parsed)}, len: {len(parsed) if isinstance(parsed, list) else 'N/A'}")
            if isinstance(parsed, list) and len(parsed) > 0:
                print(f"First event: {parsed[0]}")
        except:
            print(f"Events raw (first 200 chars): {events_sample[:200]}")
