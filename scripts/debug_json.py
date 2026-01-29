from pathlib import Path
import json
import pandas as pd

p = Path('C:\project\data\sessions\S-1762444442\meta.json')
txt = p.read_text(encoding="utf-8").strip()
print("Text length:", len(txt))
print("First 100 chars:", txt[:100])

try:
    obj = json.loads(txt)
    print("JSON loaded successfully")
    print("Type:", type(obj))
    print("\nFull JSON Object:")
    print(json.dumps(obj, indent=2))
    if isinstance(obj, dict):
        df = pd.DataFrame([obj])
        print("\nDataFrame shape:", df.shape)
        print("Columns:", list(df.columns))
        print("\nDataFrame content:")
        print(df)
        print("\nDataFrame info:")
        print(df.info())
except Exception as e:
    print("Error:", e)
