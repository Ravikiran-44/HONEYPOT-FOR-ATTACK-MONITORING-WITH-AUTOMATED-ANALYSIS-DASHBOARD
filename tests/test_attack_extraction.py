import pandas as pd
import sys
sys.path.insert(0, '.')
from app_auto import normalize_honeypot_data

# Load the CSV
df = pd.read_csv('output/honeypot_sessions.csv')
print(f"Before normalization:")
print(f"  Columns: {df.columns.tolist()}")
print(f"  'attack_type' in columns: {'attack_type' in df.columns}")
print(f"  Sample events[0]: {df['events'].iloc[0][:100]}...")

# Normalize
df = normalize_honeypot_data(df)
print(f"\nAfter normalization:")
print(f"  Columns: {df.columns.tolist()}")
print(f"  'attack_type' in columns: {'attack_type' in df.columns}")
print(f"\nAttack-type value counts:")
print(df['attack_type'].value_counts(dropna=False))
print(f"\nSample rows:")
print(df[['session_id', 'src_ip', 'attack_type']].head(10))
