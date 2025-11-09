def classify(features):
    if features.get("wget"): return ("exploit", 0.9)
    if features.get("num_commands", 0) > 5: return ("bruteforce", 0.8)
    return ("recon", 0.6)
