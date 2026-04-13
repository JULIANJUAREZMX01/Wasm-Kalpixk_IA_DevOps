## 2024-04-13 - [Dashboard derived state optimization]
**Learning:** In a highly reactive system like a SIEM dashboard with frequent log updates (`wasmLog`), calculating derived states (like mapped chart data or severity averages) directly in the component body triggers expensive O(N) array operations on every minor state change, leading to unnecessary CPU load.
**Action:** Always wrap heavy derived state computations (map, filter, reduce) inside `useMemo` hooks with tight dependency arrays (e.g., `[events]`) to ensure they only recalculate when the specific underlying data changes.
