
import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add python dir to path if needed
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.kalpixk_api import app
from db.database import get_alerts, init_db, insert_alert
from datetime import UTC, datetime

@pytest.fixture
def tmp_db(monkeypatch, tmp_path):
    db_file = str(tmp_path / "test_pagination.db")
    monkeypatch.setenv("KALPIXK_DB_PATH", db_file)
    return db_file

@pytest.mark.asyncio
async def test_pagination_hardening(tmp_db):
    await init_db()
    for i in range(5):
        await insert_alert({"ts": datetime.now(UTC).isoformat(), "anomaly_score": 0.1 * i, "severity": "LOW"})

    # Test database hardening (-1 is a bypass in SQLite)
    alerts, _ = await get_alerts(limit=-1)
    assert len(alerts) == 1, "Negative limit should be constrained to 1"

    # Test API hardening
    client = TestClient(app)
    client.headers = {"X-Kalpixk-Key": "development_secret"}
    response = client.get("/api/alerts?limit=-10")
    assert response.status_code == 200
    assert len(response.json()["alerts"]) == 1
