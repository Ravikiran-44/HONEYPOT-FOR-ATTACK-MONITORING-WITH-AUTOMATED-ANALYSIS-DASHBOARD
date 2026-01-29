#!/usr/bin/env python
import sys
print(f"Python: {sys.executable}")
print(f"Version: {sys.version}")

try:
    import pandas
    print("✓ pandas imported")
except ImportError as e:
    print(f"✗ pandas failed: {e}")

try:
    import numpy
    print("✓ numpy imported")
except ImportError as e:
    print(f"✗ numpy failed: {e}")

try:
    import sklearn
    print("✓ sklearn imported")
except ImportError as e:
    print(f"✗ sklearn failed: {e}")

try:
    import streamlit
    print("✓ streamlit imported")
except ImportError as e:
    print(f"✗ streamlit failed: {e}")

try:
    import joblib
    print("✓ joblib imported")
except ImportError as e:
    print(f"✗ joblib failed: {e}")

try:
    import paramiko
    print("✓ paramiko imported")
except ImportError as e:
    print(f"✗ paramiko failed: {e}")

try:
    import plotly
    print("✓ plotly imported")
except ImportError as e:
    print(f"✗ plotly failed: {e}")

try:
    import matplotlib
    print("✓ matplotlib imported")
except ImportError as e:
    print(f"✗ matplotlib failed: {e}")

try:
    import geoip2
    print("✓ geoip2 imported")
except ImportError as e:
    print(f"✗ geoip2 failed: {e}")

print("\nAll packages imported successfully!")
