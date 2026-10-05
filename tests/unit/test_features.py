import numpy as np
from src.runtime.fallback import fallback_extractor

def test_fallback_shape():
    metrics = {"instruction_count": 100}
    f = fallback_extractor.extract(metrics)
    assert f.shape == (32,)
    assert f.dtype == np.float32

def test_fallback_range():
    f = fallback_extractor.extract({})
    assert np.all(f >= 0)
    assert np.all(f <= 1)

def test_fallback_determinism():
    m = {"test": 1}
    f1 = fallback_extractor.extract(m)
    f2 = fallback_extractor.extract(m)
    assert np.allclose(f1, f2)
