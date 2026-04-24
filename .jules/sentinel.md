# Sentinel's Journal - Wasm-Kalpixk Security

## 2026-04-04 - API Security Hardening
**Vulnerability:** Unauthenticated sensitive endpoints and lack of input validation.
**Learning:** The application exposed critical control endpoints (`/train`, `/benchmark`, `/simulate`) and a data injection endpoint (`/detect`) without any authentication or strict input schema. This allowed anyone to trigger expensive GPU tasks or potentially crash the service with malformed data.
**Prevention:** Always use Pydantic models to enforce strict input validation and implement a security dependency (like API Key or OAuth2) for any endpoint that performs resource-intensive operations or modifies the system state.

## 2026-04-05 - Entry Point Inconsistency
**Vulnerability:** The root `main.py` entry point lacked the same security hardening as `src/api/main.py`.
**Learning:** In projects with multiple entry points (e.g., for different deployment modes or legacy support), security fixes are often applied to one but missed in others. The root `main.py` had a public `/metrics` endpoint and used non-constant-time string comparison for API keys.
**Prevention:** Maintain a centralized security dependency module or ensure all entry points are audited simultaneously when applying security patches.

## 2026-04-05 - API Security Fix for Standalone API
**Vulnerability:** Missing authentication on `src/api/main.py` endpoints.
**Learning:** While the root `main.py` had some API key validation, the specialized standalone API in `src/api/main.py` (likely used for containerized/isolated detection nodes) completely lacked authentication for sensitive endpoints like `/metrics`, `/detect`, and `/simulate`.
**Prevention:** Ensure consistent security posture across all entry points, especially in microservices architectures where different entry points might serve the same underlying logic but have different exposed interfaces.

## 2026-04-10 - Main Entry Point DoS and Auth Hardening
**Vulnerability:** Lack of input validation on training parameters and missing rate limiting on resource-intensive endpoints in `main.py`.
**Learning:** While `src/api/main.py` was hardened, the unified entry point `main.py` was still vulnerable to DoS via large training payloads and unauthenticated access if the environment was not properly configured (fail-open).
**Prevention:** Enforce strict Pydantic `Field` constraints on all user-controlled numeric parameters and apply rate limiting to all public or authenticated endpoints that trigger heavy computation (e.g., GPU training).

## 2026-04-15 - Defensive Feature DoS and Memory Exhaustion
**Vulnerability:** Honeypots and metadata endpoints lacked resource controls.
**Learning:** Defensive features like honeypots can themselves be leveraged for DoS if they serve large payloads (e.g., entropy traps) without streaming or rate limiting. An attacker could exhaust server memory by requesting multiple large payloads simultaneously.
**Prevention:** Always use streaming responses for large defensive payloads and apply strict rate limits to all honeypot and metadata endpoints to ensure the "counter-attack" doesn't crash the defender.

## 2026-04-16 - Insecure CORS Defaults and Unconstrained Pydantic Models
**Vulnerability:** Permissive CORS configuration ("*") in production and lack of length constraints on P2P sync payloads.
**Learning:** Defaulting to wildcard CORS in production environments increases the risk of unauthorized cross-origin requests. Additionally, unconstrained Pydantic models in public or authenticated endpoints can be exploited for Denial of Service (DoS) by sending extremely large payloads that exhaust server memory.
**Prevention:** Always enforce strict CORS origins in production and use Pydantic's `Field` with `max_length`, `max_items`, and other constraints to bound the size of incoming data.

## 2026-04-20 - Legacy API Security Gap
**Vulnerability:** The legacy backend API (`python/api/kalpixk_api.py`) lacked all security controls: no authentication, wildcard CORS, and no security headers.
**Learning:** Security hardening is often applied to the primary or "new" entry points while leaving legacy or internal-only APIs vulnerable, assuming they are protected by network isolation which may not always be the case.
**Prevention:** Audit all entry points regardless of their perceived usage. Use shared security dependencies across all FastAPI instances to ensure a consistent security posture.

## 2026-04-23 - Internal Component Auth Bypass
**Vulnerability:** Internal orchestrator components bypassed API authentication when calling local and peer endpoints.
**Learning:** Hardening an API is insufficient if the internal clients/orchestrators (e.g., `src/nodes/orchestrator.py`) are not updated to include the mandatory authentication headers (`X-Kalpixk-Key`). This led to functional failures and security gaps in P2P threat synchronization.
**Prevention:** When implementing mandatory authentication at the API layer, audit all internal scripts, sidecars, and orchestrators to ensure they are configured with the necessary credentials to maintain system functionality and security posture.
