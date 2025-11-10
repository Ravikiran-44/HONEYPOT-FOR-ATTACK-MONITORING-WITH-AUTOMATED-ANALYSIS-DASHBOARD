# src/classifier.py
from .model import load_model

clf, inv_label_map = load_model()

def classify(features):
    # features: dict with keys: wget, failed_login, num_commands
    fv = [features.get("wget",0), features.get("failed_login",0), features.get("num_commands",0)]
    if clf:
        pred = clf.predict([fv])[0]
        label = inv_label_map.get(pred, "unknown")
        # crude mock confidence using predict_proba if available
        try:
            conf = float(max(clf.predict_proba([fv])[0]))
        except Exception:
            conf = 0.8
        return label, conf
    # fallback rules (existing)
    if features.get("wget",0)==1 and features.get("num_commands",0)>2:
        return ("exploit", 0.9)
    if features.get("failed_login",0)>3:
        return ("bruteforce", 0.85)
    if features.get("num_commands",0)<=2:
        return ("recon", 0.6)
    return ("unknown", 0.5)
