# tests/test_classifier.py
from src.classifier import classify

def test_classify_exploit_pattern():
    features = {"wget": 1, "num_commands": 4, "failed_login": 0}
    label, conf = classify(features)
    assert label == "exploit"
    assert conf >= 0.8

def test_classify_bruteforce_pattern():
    features = {"wget": 0, "num_commands": 10, "failed_login": 5}
    label, conf = classify(features)
    assert label == "bruteforce"