import numpy as np
from src.runtime.fallback import fallback_extractor

def test_entropy_low():
    # Uniform data
    m = {"entropy": 0.0}
    f = fallback_extractor.extract(m)
    # entropy is f[8]
    assert f[8] < 0.5

def test_entropy_high():
    # Random-like data
    m = {"entropy": 1.0}
    f = fallback_extractor.extract(m)
    assert f[8] > 0.1
