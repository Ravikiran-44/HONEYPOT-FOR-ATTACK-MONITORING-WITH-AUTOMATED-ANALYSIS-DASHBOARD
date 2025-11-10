# src/model.py
import joblib, os
from pathlib import Path

MODEL_PATH = Path(__file__).resolve().parent / "models" / "rf_honeypot.pkl"
LABEL_PATH = Path(__file__).resolve().parent / "models" / "label_map.pkl"

def load_model():
    if MODEL_PATH.exists() and LABEL_PATH.exists():
        clf = joblib.load(MODEL_PATH)
        lbl = joblib.load(LABEL_PATH)
        return clf, {v:k for k,v in lbl.items()}  # invert
    return None, None
