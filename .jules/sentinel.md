# Sentinel's Journal - Wasm-Kalpixk Security

## 2026-04-04 - API Security Hardening
**Vulnerability:** Unauthenticated sensitive endpoints and lack of input validation.
**Learning:** The application exposed critical control endpoints (`/train`, `/benchmark`, `/simulate`) and a data injection endpoint (`/detect`) without any authentication or strict input schema. This allowed anyone to trigger expensive GPU tasks or potentially crash the service with malformed data.
**Prevention:** Always use Pydantic models to enforce strict input validation and implement a security dependency (like API Key or OAuth2) for any endpoint that performs resource-intensive operations or modifies the system state.

## 2026-04-07 - Fail-Secure API Configuration
**Vulnerability:** Insecure defaults where missing configuration could lead to unauthenticated access in production.
**Learning:** Hardening `verify_api_key` to explicitly check for the production environment ensures that the system refuses to start/serve if the expected security credentials are not found, rather than silently falling back to a "no auth" mode.
**Prevention:** Implement explicit environment-based validation logic that raises a 500 error if security keys are missing in production.
