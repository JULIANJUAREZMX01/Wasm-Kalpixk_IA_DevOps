import numpy as np
from src.retaliation.atlatl import atlatl, stream_entropy_payload


def test_v8_entropy_generation():
    """Verify that v8 entropy generator produces high-entropy data."""
    size_mb = 10
    payload = stream_entropy_payload(size_mb)
    assert len(payload) == size_mb * 1024 * 1024

    # Simple check for randomness: mean should be around 127.5
    mean_val = np.mean(np.frombuffer(payload, dtype=np.uint8))
    assert 120 <= mean_val <= 135


def test_v8_algorithmic_guillotine_execution():
    """Verify the v8 guillotine strike logic and result structure."""
    target = "192.168.1.100"
    result = atlatl.v8_algorithmic_guillotine(target)

    assert result["status"] == "GUILLOTINE_EXECUTED_V8"
    assert result["impact"] == "SYSTEMIC_DESTRUCTION"
    assert result["target"] == target
    assert result["bandwidth_saturation"] == "25GB/s"
    assert result["neural_poisoning"] == "SUCCESS"
    assert "collapse_results" in result
    assert len(result["collapse_results"]) >= 8


def test_systemic_collapse_vectors():
    """Verify that all v8 strike vectors are correctly initialized."""
    from src.retaliation.atlatl import systemic_collapse

    expected_vectors = [
        "v8_corrupt_remote_pointers",
        "v8_saturate_network_buffers",
        "v8_neutralize_c2_uplinks",
        "v8_trigger_hardware_lockdown",
        "v8_dynamic_entropy_saturation",
        "v8_c2_signature_poisoning",
        "v8_ghost_mesh_isolation",
        "v8_adversarial_tensor_flood",
    ]
    for vector in expected_vectors:
        assert vector in systemic_collapse.strike_vectors


def test_v8_api_endpoint_structure():
    """Verify API structure for v8 strikes (mocking FastAPI app)."""
    from fastapi.testclient import TestClient

    from python.api.kalpixk_api import app

    client = TestClient(app)
    # We expect a 403 or 401 if unauthorized, but we check if the route exists
    response = client.post("/api/v1/guerrilla/v8/strike")
    assert response.status_code in [403, 401]  # Security is working
