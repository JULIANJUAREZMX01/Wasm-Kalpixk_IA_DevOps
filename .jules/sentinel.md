# Sentinel Security Learnings

## 2024-05-18 - [v7 Adversarial Evasion]
**Vulnerability:** Adversarial Tensor Noise induced via FGSM/PGD to bypass neural detection.
**Learning:** High-frequency infinitesimal noise can blind autoencoders. Detectable at the bit-level via roughness analysis.
**Prevention:** Implement `v7_audit_tensor` in Zig/WASM to validate tensor roughness and numeric stability before inference.

## 2024-05-22 - [v8 Guerrilla Hardening]
**Vulnerability:** JIT Spraying and Buffer Deduplication Evasion in decentralized nodes.
**Learning:** Standard entropy storms can be mitigated by deduplicating network appliances. JIT probing requires polymorphic instruction noise to disrupt shellcode alignment.
**Prevention:** Implement non-linear chaotic entropy (Logistic Map) and polymorphic instruction padding (JIT Shield) at the metal layer (Zig/Rust).

## 2026-10-04 - [Non-Finite Float Input DoS & Unhandled Serialization Crash]
**Vulnerability:** Non-finite float values (`NaN`, `Infinity`, `-Infinity`) in API feature vectors bypass default schema checks, causing model inference issues or throwing unhandled exceptions during JSON validation error serialization.
**Learning:** FastAPI/Pydantic validation errors include the raw `input` value in error responses. When `input` contains non-finite floats, standard `json.dumps` fails with `ValueError: Out of range float values are not JSON compliant`, causing a 500 server crash instead of a 422 error response.
**Prevention:** Enforce `math.isfinite` validation on all numeric input arrays in Pydantic models, and implement a custom `RequestValidationError` handler that recursively replaces non-finite float inputs in error details with `None` before JSON rendering.
