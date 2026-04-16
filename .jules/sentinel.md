# Sentinel's Journal - Wasm-Kalpixk Security

## 2026-04-04 - API Security Hardening
**Vulnerability:** Unauthenticated sensitive endpoints and lack of input validation.
**Learning:** The application exposed critical control endpoints (`/train`, `/benchmark`, `/simulate`) and a data injection endpoint (`/detect`) without any authentication or strict input schema. This allowed anyone to trigger expensive GPU tasks or potentially crash the service with malformed data.
**Prevention:** Always use Pydantic models to enforce strict input validation and implement a security dependency (like API Key or OAuth2) for any endpoint that performs resource-intensive operations or modifies the system state.

## 2026-04-05 - Entry Point Inconsistency
**Vulnerability:** The root `main.py` entry point lacked the same security hardening as `src/api/main.py`.
**Learning:** In projects with multiple entry points (e.g., for different deployment modes or legacy support), security fixes are often applied to one but missed in others. The root `main.py` had a public `/metrics` endpoint and used non-constant-time string comparison for API keys.
**Prevention:** Maintain a centralized security dependency module or ensure all entry points are audited simultaneously when applying security patches.

## 2026-04-10 - Main Entry Point DoS and Auth Hardening
**Vulnerability:** Lack of input validation on training parameters and missing rate limiting on resource-intensive endpoints in `main.py`.
**Learning:** While `src/api/main.py` was hardened, the unified entry point `main.py` was still vulnerable to DoS via large training payloads and unauthenticated access if the environment was not properly configured (fail-open).
**Prevention:** Enforce strict Pydantic `Field` constraints on all user-controlled numeric parameters and apply rate limiting to all public or authenticated endpoints that trigger heavy computation (e.g., GPU training).

## 2026-04-12 - Missing Rate Limiting on Data and Honeypot Endpoints
**Vulnerability:** Missing rate limiting decorators on sensitive data endpoints and offensive honeypots in `src/api/main.py`.
**Learning:** Even when a `Limiter` is globally initialized, it must be explicitly applied to each endpoint. Honeypots that generate large or high-entropy responses (like `atlatl` entropy traps) can be weaponized against the host if not rate-limited, turning a defense mechanism into a DoS vector.
**Prevention:** Always apply rate limits to endpoints that return large payloads or perform disk/GPU intensive tasks. For `slowapi`, ensure the `Request` object is included in the endpoint signature.
=======
## 2026-04-05 - API Security Fix for Standalone API
**Vulnerability:** Missing authentication on `src/api/main.py` endpoints.
**Learning:** While the root `main.py` had some API key validation, the specialized standalone API in `src/api/main.py` (likely used for containerized/isolated detection nodes) completely lacked authentication for sensitive endpoints like `/metrics`, `/detect`, and `/simulate`.
**Prevention:** Ensure consistent security posture across all entry points, especially in microservices architectures where different entry points might serve the same underlying logic but have different exposed interfaces.

## 2026-04-16 - Insecure CORS Defaults and Unconstrained Pydantic Models
**Vulnerability:** Permissive CORS configuration ("*") in production and lack of length constraints on P2P sync payloads.
**Learning:** Defaulting to wildcard CORS in production environments increases the risk of unauthorized cross-origin requests. Additionally, unconstrained Pydantic models in public or authenticated endpoints can be exploited for Denial of Service (DoS) by sending extremely large payloads that exhaust server memory.
**Prevention:** Always enforce strict CORS origins in production and use Pydantic's `Field` with `max_length`, `max_items`, and other constraints to bound the size of incoming data.
