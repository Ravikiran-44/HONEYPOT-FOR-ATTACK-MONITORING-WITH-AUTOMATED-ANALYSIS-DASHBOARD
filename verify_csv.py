#!/usr/bin/env python3
import pandas as pd

df = pd.read_csv('output/honeypot_sessions.csv')
print('CSV Analysis:')
print(f'  Columns: {list(df.columns)}')
print(f'  Total rows: {len(df)}')
print(f'  Has src_country: {"src_country" in df.columns}')
if "src_country" in df.columns:
    print(f'  Non-null countries: {df["src_country"].notna().sum()}')
    print(f'  Unique countries: {df["src_country"].nunique()}')
    print(f'  Country distribution:\n{df["src_country"].value_counts()}')
