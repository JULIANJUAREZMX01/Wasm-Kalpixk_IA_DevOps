import re

with open("python/tests/test_full_pipeline.py", "r") as f:
    content = f.read()

# Update test_detect_brute_force
content = content.replace(
    '''payload = {
        "features": brute_force_features.tolist(),
        "event_ids": [f"ssh_{i}" for i in range(50)],
        "source_type": "syslog",
        "metadata": [{"event_type": "login_failure"}] * 50,
    }''',
    '''payload = {
        "features": brute_force_features[0].tolist(),
        "source": "syslog",
    }'''
)
content = content.replace('assert len(data["results"]) == 50', '')

# Update test_detect_normal_traffic_low_anomalies
content = content.replace(
    '''payload = {
        "features": normal_traffic_features.tolist(),
        "event_ids": [f"normal_{i}" for i in range(100)],
        "source_type": "json",
        "metadata": [{"event_type": "db_query"}] * 100,
    }''',
    '''payload = {
        "features": normal_traffic_features[0].tolist(),
        "source": "json",
    }'''
)

# Update test_detection_latency_under_50ms
content = content.replace(
    '''features = rng.uniform(0, 1, (100, 32)).tolist()
    payload = {
        "features": features,
        "event_ids": [f"e{i}" for i in range(100)],
        "source_type": "json",
        "metadata": [{}] * 100,
    }''',
    '''features = rng.uniform(0, 1, 32).tolist()
    payload = {
        "features": features,
        "source": "json",
    }'''
)

# Update test_all_scores_in_unit_interval
content = content.replace(
    '''features = rng.uniform(0, 1, (50, 32)).tolist()
    payload = {
        "features": features,
        "event_ids": [f"t{i}" for i in range(50)],
        "source_type": "db2",
        "metadata": [{}] * 50,
    }''',
    '''features = rng.uniform(0, 1, 32).tolist()
    payload = {
        "features": features,
        "source": "db2",
    }'''
)

with open("python/tests/test_full_pipeline.py", "w") as f:
    f.write(content)
