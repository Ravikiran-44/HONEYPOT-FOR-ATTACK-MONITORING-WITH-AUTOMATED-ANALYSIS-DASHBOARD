import pandas as pd

df = pd.read_csv('output/honeypot_sessions.csv')
print('✅ Dashboard Data Verification:')
print(f'   Sessions loaded: {len(df)}')
print(f'   Countries: {df["src_country"].nunique()}')
print(f'   Honeypots: {df["instance"].nunique()}')
print(f'   Columns: {df.columns.tolist()}')
print('\n✅ Dataset is ready for visualization!')
