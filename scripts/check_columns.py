import pandas as pd

df = pd.read_csv('output/honeypot_sessions.csv')
print('Columns:', list(df.columns))
print('Unique?', len(df.columns) == len(set(df.columns)))
dupes = [c for c in set(df.columns) if df.columns.tolist().count(c) > 1]
print('Duplicates:', dupes)
print('First row:')
print(df.iloc[0])
