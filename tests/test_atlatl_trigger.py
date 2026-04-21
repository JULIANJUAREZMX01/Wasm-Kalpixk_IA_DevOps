
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.retaliation.atlatl import atlatl
from loguru import logger

def test_retaliation_trigger():
    logger.info("Testing ATLATL-ORDNANCE Retaliation Trigger Logic...")

    # Test Block
    logger.info("Test 1: Low score (Block)")
    res = atlatl.trigger_retaliation(0.5, "192.168.1.100")
    assert res["action"] == "BLOCK"

    # Test Red Phase
    logger.info("Test 2: Medium score (Phase Red)")
    res = atlatl.trigger_retaliation(0.75, "192.168.1.101")
    assert res["action"] == "RETALIATE_RED"
    assert "pointer_poisoning" in res["measures"]

    # Test Black Phase
    logger.info("Test 3: High score (Phase Black)")
    res = atlatl.trigger_retaliation(0.95, "192.168.1.102")
    assert res["action"] == "EXTERMINATE"
    assert "recursive_zip_bomb" in res["measures"]

    logger.success("ATLATL-ORDNANCE Retaliation Trigger Logic: SUCCESS")

if __name__ == "__main__":
    try:
        test_retaliation_trigger()
    except Exception as e:
        logger.error(f"Test failed: {e}")
        sys.exit(1)
