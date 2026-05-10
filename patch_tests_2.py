import re

with open("python/tests/test_full_pipeline.py", "r") as f:
    content = f.read()

# Update test_all_scores_in_unit_interval
content = content.replace(
    '''payload = {
        "features": features,
        "event_ids": [f"e{i}" for i in range(200)],
        "source_type": "syslog",
        "metadata": [{}] * 200,
    }''',
    '''payload = {
        "features": features[0],
        "source": "syslog",
    }'''
)

with open("python/tests/test_full_pipeline.py", "w") as f:
    f.write(content)
