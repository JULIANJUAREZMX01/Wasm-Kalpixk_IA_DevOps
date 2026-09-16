## 2024-05-24 - [Avoid list conversion for ML inference loops]
**Learning:** [Avoid converting NumPy arrays to Python lists (`.tolist()`) inside ML inference loops like `predict()`. Natively handling numpy arrays and using vectorized filters significantly reduces processing overhead for large arrays, preventing CPU bottlenecks.]
**Action:** [Use native numpy masking (e.g., `scores[scores < self._current_threshold]`) and remove `.tolist()` conversions until the very final serialization step when constructing APIs.]
