from src.retaliation.atlatl import atlatl


def test_v8_algorithmic_guillotine_logic():
    """Verify v8 strike orchestration and entropy saturation."""
    target = "192.168.1.100"
    result = atlatl.v8_algorithmic_guillotine(target)

    assert result["status"] == "GUILLOTINE_EXECUTED_V8"
    assert result["bandwidth_saturation"] == "25GB/s"
    assert result["neural_poisoning"] == "ACTIVE"
    assert result["target"] == target
    assert "v8_ghost_mesh_consensus" in result["collapse_results"]
    assert result["collapse_results"]["v8_ghost_mesh_consensus"] == "SUCCESS"

def test_v8_trigger_retaliation_guerrilla():
    """Verify trigger_retaliation handles guerrilla_threat type."""
    target = "10.0.0.5"
    result = atlatl.trigger_retaliation(0.5, target, anomaly_type="guerrilla_threat")

    assert result["status"] == "GUILLOTINE_EXECUTED_V8"

def test_v8_atlatl_initiate_vector():
    """Verify dynamic initiation of v8 vectors."""
    target = "172.16.0.1"
    res = atlatl.initiate("v8_corrupt_remote_pointers", target)
    assert res == "SUCCESS"

    res_unknown = atlatl.initiate("unknown_vector", target)
    assert res_unknown == "FAILED_UNKNOWN_VECTOR"
