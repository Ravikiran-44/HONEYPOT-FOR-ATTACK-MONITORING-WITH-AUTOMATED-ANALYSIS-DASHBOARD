def decide_engagement(label, conf):
    if label == "exploit" and conf > 0.8: return "HIGH"
    if label == "bruteforce": return "MEDIUM"
    return "LOW"
