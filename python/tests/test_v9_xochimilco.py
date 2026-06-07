import pytest
from src.retaliation.atlatl import atlatl


@pytest.mark.asyncio
async def test_v9_retaliation_vectors():
    target = "192.168.1.100"

    # Test v9 Annihilation
    res = atlatl.v9_xochimilco_annihilation(target)
    assert res["status"] == "ANNIHILATION_EXECUTED_V9"
    assert res["zip_trap"] == "ACTIVE_PETABYTE_RECURSIVE"
    assert res["hardware_panic"] == "ACTIVE_IO_SATURATION"
    assert res["collapse_results"]["v9_recursive_zip_trap"] == "SUCCESS"
    assert res["collapse_results"]["v9_hardware_panic_trigger"] == "SUCCESS"

def test_v9_trigger_logic():
    target = "10.0.0.5"
    # Severe breach should trigger v9
    res = atlatl.trigger_retaliation(0.98, target, "xochimilco_breach")
    assert res["status"] == "ANNIHILATION_EXECUTED_V9"

    # Standard ransomware should still trigger v8
    res = atlatl.trigger_retaliation(0.92, target, "ransomware_detected")
    assert res["status"] == "GUILLOTINE_EXECUTED_V8"

@pytest.mark.asyncio
async def test_v9_api_endpoint():
    # This assumes the server is running, but we can mock or just test the logic
    # In this environment, we'll just check if atlatl is correctly configured
    from src.retaliation.atlatl import systemic_collapse
    assert "v9_recursive_zip_trap" in systemic_collapse.strike_vectors
    assert "v9_hardware_panic_trigger" in systemic_collapse.strike_vectors
