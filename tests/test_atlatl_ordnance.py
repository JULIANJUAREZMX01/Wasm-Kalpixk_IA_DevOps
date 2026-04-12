"""
ATLATL-ORDNANCE — Integration and Retaliation Tests
Verifies the aggressive defense and P2P orchestration logic.
"""
import pytest
import numpy as np
from src.retaliation.atlatl import atlatl
from src.nodes.orchestrator import orchestrator
from src.detector.anomaly_detector import AnomalyDetector

def test_atlatl_phase_black_trigger():
    """Verifies that high anomaly scores trigger Phase Black."""
    response = atlatl.trigger_retaliation(0.95, "1.2.3.4")
    assert response["action"] == "EXTERMINATE"
    assert "recursive_zip_bomb" in response["measures"]
    assert "deep_corruption" in response["measures"]

def test_atlatl_phase_red_trigger():
    """Verifies that moderate anomaly scores trigger Phase Red."""
    response = atlatl.trigger_retaliation(0.75, "1.2.3.4")
    assert response["action"] == "RETALIATE_RED"
    assert "pointer_poisoning" in response["measures"]
    assert "hardware_hang" in response["measures"]

def test_orchestrator_blacklist():
    """Verifies that the orchestrator correctly manages the global blacklist."""
    threats = ["10.0.0.1", "192.168.1.100"]
    import asyncio
    asyncio.run(orchestrator.sync_threats(threats))

    blacklist = orchestrator.get_blacklist()
    assert "10.0.0.1" in blacklist
    assert "192.168.1.100" in blacklist

def test_anomaly_detector_integration():
    """Verifies that the anomaly detector can process features for prediction."""
    detector = AnomalyDetector()
    # Mock feature vector (32 dimensions)
    features = np.zeros((1, 32), dtype=np.float32)
    features[0, 0] = 5.0 # Alter something

    result = detector.predict(features)
    assert "reconstruction_errors" in result
    assert "anomalies" in result

@pytest.mark.asyncio
async def test_orchestrator_async_sync():
    """Verifies async sync logic in orchestrator."""
    await orchestrator.sync_threats(["8.8.8.8"])
    assert "8.8.8.8" in orchestrator.get_blacklist()
