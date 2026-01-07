import pandas as pd

df = pd.read_csv("output/honeypot_sessions.csv", dtype=str)
if 'attack_type' not in df.columns:
    print("MISSING_ATTACK_COLUMN")
else:
    s = df['attack_type'].fillna('')\
        .astype(str).str.strip().str.lower()
    print("unique_count=", s.nunique())
    counts = s.value_counts(dropna=False)
    print(counts.to_string())
    print("\nSAMPLE raw values (first 30):")
    print(df['attack_type'].head(30).tolist())
