# Sentinel's Journal - Wasm-Kalpixk Security

## 2026-04-05 - API Security Fix for Standalone API
**Vulnerability:** Missing authentication on `src/api/main.py` endpoints.
**Learning:** While the root `main.py` had some API key validation, the specialized standalone API in `src/api/main.py` (likely used for containerized/isolated detection nodes) completely lacked authentication for sensitive endpoints like `/metrics`, `/detect`, and `/simulate`.
**Prevention:** Ensure consistent security posture across all entry points, especially in microservices architectures where different entry points might serve the same underlying logic but have different exposed interfaces.
