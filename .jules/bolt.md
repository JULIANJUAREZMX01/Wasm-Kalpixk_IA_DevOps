## 2024-04-13 - [Dashboard derived state optimization]
**Learning:** In a highly reactive system like a SIEM dashboard with frequent log updates (`wasmLog`), calculating derived states (like mapped chart data or severity averages) directly in the component body triggers expensive O(N) array operations on every minor state change, leading to unnecessary CPU load.
**Action:** Always wrap heavy derived state computations (map, filter, reduce) inside `useMemo` hooks with tight dependency arrays (e.g., `[events]`) to ensure they only recalculate when the specific underlying data changes.

## 2024-04-14 - [Frontend list rendering optimization with React.memo]
**Learning:** In a real-time SIEM dashboard, rendering prepended lists with array index as keys causes React to unmount and remount every single row whenever a new log arrives, creating a huge O(N) rendering bottleneck as `events` size grows up to 100 items. This triggers expensive `new Date()` calculations and string slice operations repeatedly.
**Action:** Always use stable unique keys (like timestamp + raw log) for frequently updated lists and extract the list item into a separate component wrapped with `React.memo()` to skip re-rendering rows that haven't changed.

## 2025-04-15 - [Optimize ML prediction loops with NumPy vectorization]
**Learning:** In machine learning prediction loops, native Python list comprehensions for calculating scores and confidences from arrays create a severe performance bottleneck. Native loops iterate item by item in Python's evaluation loop, whereas NumPy vectorized operations push the iteration down into optimized C code.
**Action:** Always prefer native NumPy vectorized operations (like `np.clip`, `np.abs`, and direct arithmetic) over Python loops or list comprehensions when processing arrays or tensors, particularly in hot paths like ML prediction.
