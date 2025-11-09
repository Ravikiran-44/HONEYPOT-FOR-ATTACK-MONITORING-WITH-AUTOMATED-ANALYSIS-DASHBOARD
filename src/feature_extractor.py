def extract_features(events):
    text = " ".join(e.get("text", "") for e in events).lower()
    return {"wget": 1 if "wget" in text or "curl" in text else 0, "num_commands": len(events)}
