# Sentinel Security Learnings

## 2024-05-18 - [v7 Adversarial Evasion]
**Vulnerability:** Adversarial Tensor Noise induced via FGSM/PGD to bypass neural detection.
**Learning:** High-frequency infinitesimal noise can blind autoencoders. Detectable at the bit-level via roughness analysis.
**Prevention:** Implement `v7_audit_tensor` in Zig/WASM to validate tensor roughness and numeric stability before inference.

## 2024-05-22 - [v8 Guerrilla Hardening]
**Vulnerability:** JIT Spraying and Buffer Deduplication Evasion in decentralized nodes.
**Learning:** Standard entropy storms can be mitigated by deduplicating network appliances. JIT probing requires polymorphic instruction noise to disrupt shellcode alignment.
**Prevention:** Implement non-linear chaotic entropy (Logistic Map) and polymorphic instruction padding (JIT Shield) at the metal layer (Zig/Rust).

## 2024-05-25 - [Non-Finite Float Feature DoS & Validation Exception Crash]
**Vulnerability:** Passing non-finite floats (`NaN`, `Infinity`) in feature inputs bypassed standard array type checking, causing Unhandled 500 Internal Server Errors or crashes during JSON error detail serialization.
**Learning:** Standard FastAPI/Pydantic validation includes the raw invalid input in the error detail (`RequestValidationError.errors()`). Serializing `NaN`/`Inf` via `json.dumps()` raises `ValueError: Out of range float values are not JSON compliant`, causing a 500 server crash when attempting to respond with a 422 error.
**Prevention:** Enforce strict `math.isfinite()` checks on all incoming numerical feature vectors and install a custom `RequestValidationError` exception handler in FastAPI that sanitizes non-finite floats to `None` in exception error contexts before JSON serialization.
