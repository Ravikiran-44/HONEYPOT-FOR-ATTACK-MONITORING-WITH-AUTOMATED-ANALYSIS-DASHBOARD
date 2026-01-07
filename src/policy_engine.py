def decide_engagement(label, conf):
    # Enable Claude Sonnet 3.5 for all clients by always returning HIGH engagement
    return "HIGH"
    # Original policy commented out:
    # if label == "exploit" and conf > 0.8: return "HIGH"
    # if label == "bruteforce": return "MEDIUM"
    # return "LOW"
