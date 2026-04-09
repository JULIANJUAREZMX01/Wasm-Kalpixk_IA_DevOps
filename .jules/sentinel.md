# Sentinel's Journal - Wasm-Kalpixk Security

## 2026-04-04 - API Security Hardening
**Vulnerability:** Unauthenticated sensitive endpoints and lack of input validation.
**Learning:** The application exposed critical control endpoints (`/train`, `/benchmark`, `/simulate`) and a data injection endpoint (`/detect`) without any authentication or strict input schema. This allowed anyone to trigger expensive GPU tasks or potentially crash the service with malformed data.
**Prevention:** Always use Pydantic models to enforce strict input validation and implement a security dependency (like API Key or OAuth2) for any endpoint that performs resource-intensive operations or modifies the system state.

## 2026-04-05 - Entry Point Inconsistency
**Vulnerability:** The root `main.py` entry point lacked the same security hardening as `src/api/main.py`.
**Learning:** In projects with multiple entry points (e.g., for different deployment modes or legacy support), security fixes are often applied to one but missed in others. The root `main.py` had a public `/metrics` endpoint and used non-constant-time string comparison for API keys.
**Prevention:** Maintain a centralized security dependency module or ensure all entry points are audited simultaneously when applying security patches.
