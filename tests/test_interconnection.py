from fastapi.testclient import TestClient
from main import app
import os

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "ip_assigned" in data

def test_metrics_endpoint():
    # Detectar si hay API key en el environment para pasarla en el test
    api_key = os.getenv("KALPIXK_API_KEY")
    headers = {"X-Kalpixk-Key": api_key} if api_key else {}

    response = client.get("/metrics", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    assert "detection" in data

def test_static_dashboard():
    response = client.get("/")
    assert response.status_code in [200, 404]

def test_local_ip_detection():
    from main import get_local_ip
    ip = get_local_ip()
    assert isinstance(ip, str)
    assert "." in ip or ":" in ip
